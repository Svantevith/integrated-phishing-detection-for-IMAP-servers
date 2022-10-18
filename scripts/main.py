import os
from dotenv import load_dotenv
from email_listener import email_listener

"""
Main script with the IMAP server configuration.
It is highly recommended to use Gmail IMAP server for the email listener.
Otherwise, unexpected errors might occur.

Usage
-----
1. In the .env file define EMAIL_ADDRESS and APP_PASSWORD
2. Define MAIL_BOXES. 
    a. If empty, user is prompted to select mailboxes via console.
3. Define SPAM_BOX. 
    a. If empty, user is prompted to select spam folder via console.
    b. If there exists a default spam folder, the first mailbox containing 'spam' in its name is used.
4. Define PHISHY_THRESHOLD. All emails with phishing probability higher than the threshold are moved to SPAM_BOX.
"""

# Disable info & warning messages for tensorflow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 

# Load environmental variables
load_dotenv()
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
APP_PASSWORD = os.getenv("APP_PASSWORD")

# Define IMAP server
IMAP_SERVER = "imap.gmail.com"

# Define mailboxes to search through
MAIL_BOXES = [] # ["Inbox"]

# Define the folder, where to move spam
SPAM_BOX = "[Gmail]/Spam"

# Define probability threshold for malicious tag
PHISHY_THRESHOLD = 0.7

if __name__ == "__main__":
    # Iterate over unseen messages in the selected mailboxes and output predictions to the console
    email_listener(IMAP_SERVER, EMAIL_ADDRESS, APP_PASSWORD, MAIL_BOXES, SPAM_BOX, PHISHY_THRESHOLD)
