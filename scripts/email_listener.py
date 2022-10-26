import os
import mailbox
import imaplib
import joblib
import pandas as pd
import numpy as np
import tensorflow as tf
from typing import List
from dotenv import load_dotenv
from classes.MboxParser import MboxParser
from classes.IMAPAllocationError import IMAPAllocationError
from preprocessing_pipelines import text_pipeline, features_pipeline
from helper_functions import decode_mime_words, parse_uid, parse_mailboxes
from helper_functions import select_mailboxes, select_spam_folder

"""
Python file containing the email listener with an intelligent function to detect & move phishing messages to the Spam folder.
Specifically designed for the Gmail IMAP server, using other service configurations might lead to unexpected issues.
"""

# Disable info & warning messages for tensorflow
tf.get_logger().setLevel('ERROR')

# Define paths to models
load_dotenv()
LSTM_PATH = os.getenv("LSTM_PATH")
KNN_PATH = os.getenv("KNN_PATH")

# Make this wrapped to have 'with'statement

def email_listener(imap_server: str, email_address: str, email_password: str, mail_boxes: List[str] = [], spam_box: str = "", phishy_threshold: float = 0.7) -> None:
    """
    Iterate over unseen messages in the specified mailboxes, output predictions for email fraudulence to the console and move infected messages to the spam folder.
    
    Parameters
    ----------
        imap_server : str
            IMAP server (host)
        email_address : str
            Address for the email account
        email_password : str 
            Password for the email account
        mail_boxes : List[str], optional
            List of mailboxes
        spam_box : str, optional
            Mailbox holding spam messages. When empty (default), it is set to the very first folder containing 'spam' inside its name.
        phishy_threshold : float, optional
            If prediction probability for the phishy email is below that threshold, it is treated as safe. Default is 0.7
    """

    # Connect with server using SSL
    with imaplib.IMAP4_SSL(imap_server) as imap:
        # Login using credentials
        imap.login(email_address, email_password)
        print(f"[🔑] Connection with the IMAP server established.")
        
        # List available mailboxes
        mail_tree = parse_mailboxes(imap.list()[1])

        # ===== USER CONSOLE INPUT [MAILBOXES] ====
        if not mail_boxes:
            mail_boxes = select_mailboxes(mail_tree)
        
        # ===== USER CONSOLE INPUT [SPAM BOX] ====
        if not spam_box:
            spam_box = select_spam_folder(mail_tree)
        
        # ==== EMAIL SCANNING ====
        scanned_emails = []

        # Iterate over each mail box specified
        for i, mail_box in enumerate(mail_boxes, start=1):

            # Select mail-box
            imap.select(mail_box)

            # Get unseen emails
            _, byte_array = imap.search(None, "(UNSEEN)")
            msg_indices = byte_array[0].split()
            if not msg_indices:
                print(f"[{i}] Unseen messages not found in {mail_box}")
                continue

            print(f"[{i}] Found {len(msg_indices)} unseen messages in {mail_box}")
            for msg_idx in msg_indices:
                # Fetch UID
                _, uid_bytes = imap.fetch(msg_idx, "(UID)")
                msg_uid = parse_uid(uid_bytes)
                
                # Fetch message content
                _, content_bytes = imap.fetch(msg_idx, "(RFC822)")

                # Create mboxMessage object
                mbox_msg = mailbox.mboxMessage(content_bytes[0][1])

                # Parse data from the mboxMessage object
                mbox_parser = MboxParser(mbox_msg)

                # Add parsed email data to the list of scanned emails
                scanned_emails.append({
                    'UID': msg_uid,
                    **mbox_parser.parsed_email_data,
                    'Mailbox': mail_box
                })

        if not scanned_emails:
            print('\n[⚠️ ] No unseen emails to scan')
            return 

        # Convert list of scanned email data to a DataFrame
        scanned_emails_df = pd.DataFrame.from_dict(scanned_emails)

        # Load models
        print("\n[⌛] Loading models...")
        lstm = tf.keras.models.load_model(LSTM_PATH)
        knn = joblib.load(KNN_PATH)
        print("[⚙️ ] Models ready!\n")
        
        # Preprocess corpus
        text_pipe = text_pipeline(min_length=2, is_num_like=False)
        text_in = text_pipe.fit_transform(scanned_emails_df[['Subject', 'Raw Message']])

        # Preprocess features
        features_pipe = features_pipeline(exclude=['X-Virus-Scanned', 'Is JavaScript', 'Attachments'])
        features_in = features_pipe.fit_transform(scanned_emails_df)

        # Make predictions using LSTM
        y_pred_lstm = lstm.predict(text_in, verbose=0)

        # Make predictions using KNN
        y_pred_knn = knn.predict_proba(features_in)

        # Use bagging to combine predictions
        y_pred_proba = np.mean([y_pred_lstm, y_pred_knn], axis=0)
        
        # Set appropriate label based on the defined probability threshold
        y_pred = [int(p[1] >= phishy_threshold) for p in y_pred_proba]

        # Output predictions to the console
        console_out = " [{}] Message '{}' from {} in {} is {}. {}"
        for idx, (msg_uid, msg_subject, msg_from, mail_box) in scanned_emails_df[['UID', 'Subject', 'From', 'Mailbox']].iterrows():
            is_phishy = y_pred[idx]
            tag, icon, action = 'safe', '✔️ ', ''
            # Move phishy message from the current mailbox to the '[Gmail]/Spam' mailbox
            if is_phishy:
                imap.select(mail_box)
                tag, icon, action = 'malicious', '❌ ', f'For security reasons, email was moved to {spam_box} folder.'
                try:
                    # Copy email to Spam
                    copy_status, _ = imap.uid('COPY', msg_uid, spam_box)
                    if copy_status != 'OK':
                        raise IMAPAllocationError

                    # Remove email from the current folder
                    del_status, _ = imap.uid('STORE', msg_uid , '+FLAGS', '(\Deleted)')
                    if del_status != 'OK':
                        raise IMAPAllocationError
                    
                    # Perform deletion
                    imap.expunge()

                # Handle error in case of insuccessful message allocation
                except IMAPAllocationError(message=f"Moving email to {spam_box} failed.") as err:
                    action = err
            
            # Print information to the user
            print(console_out.format(icon, decode_mime_words(msg_subject), msg_from, mail_box, tag, action))