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
from helper_functions import decode_mime_words, parse_uid

"""
Python file containing the email listener.
"""

# Disable info & warning messages for tensorflow
tf.get_logger().setLevel('ERROR')

# Define paths to models
load_dotenv()
LSTM_PATH = os.getenv("LSTM_PATH")
KNN_PATH = os.getenv("KNN_PATH")

# Make this wrapped to have 'with'statement

def email_listener(imap_server: str, email_address: str, email_password: str, mail_boxes: List[str] = [], phishy_threshold: float = 0.7) -> None:
    """
    Description
        Iterate over unseen images in the specified mailboxes and output predictions for email fraudulence to the console.
    
    Arguments
        imap_server : str
            IMAP server (host)
        email_address : str
            Address for the email account
        email_password : str 
            Password for the email account
        mail_boxes : List[str]
            List of mailboxes
        phishy_threshold : float
            If prediction probability for the phishy email is below that threshold, it is treated as safe
    
    Returns
        Nothing
    """

    # Connect with server using SSL
    with imaplib.IMAP4_SSL(imap_server) as imap:
        # Login using credentials
        imap.login(email_address, email_password)
        print(f"[🔑] Connection with the IMAP server established.")

        # ===== USER CONSOLE INPUT ====
        if not mail_boxes:
            print("\nSelect folders to scan:")
            mail_tree = [
                mail_box.decode().split(' "/" ')[1].strip('"') for mail_box in imap.list()[1]
            ]
            for i, mail_box in enumerate(mail_tree, start=1):
                print(f" {i}. {mail_box.split('/')[-1]}")

            try:
                indices = sorted(
                    set(input("\nSeparate indices with a single space: ").split()),
                    key=str.lower,
                )
                if not indices:
                    print("Empty input sequence")
                    return
                mail_boxes = [mail_tree[int(i) - 1] for i in indices]
                print("\n")
            except IndexError:
                print("Index pointing to non-existing folder")
                return
            except ValueError:
                print("Invalid input index format")
                return

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
        text_pipe = text_pipeline(mode='ascii', min_length=2)
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
                tag, icon, action = 'malicious', '❌ ', 'For security reasons, email was moved to the Spam folder.'
                try:
                    # Copy email to Spam
                    copy_status, _ = imap.uid('COPY', msg_uid, '[Gmail]/Spam')
                    if copy_status != 'OK':
                        raise IMAPAllocationError

                    # Remove email from the current folder
                    del_status, _ = imap.uid('STORE', msg_uid , '+FLAGS', '(\Deleted)')
                    if del_status != 'OK':
                        raise IMAPAllocationError
                    
                    # Perform deletion
                    imap.expunge()

                # Handle error in case of insuccessful message allocation
                except IMAPAllocationError(message="Moving email to the Spam failed failed.") as err:
                    action = err
            
            # Print information to the user
            print(console_out.format(icon, decode_mime_words(msg_subject), msg_from, mail_box, tag, action))