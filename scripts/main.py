import os
from dotenv import load_dotenv
from email_listener import email_listener

# Disable info & warning messages for tensorflow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 

# Load environmental variables
load_dotenv()
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
APP_PASSWORD = os.getenv("APP_PASSWORD")

# Define IMAP server
IMAP_SERVER = "imap.gmail.com"

# Define mailboxes to search through
MAIL_BOXES = ["Inbox", "[Gmail]/Spam"]

# Define probability threshold for malicious tag
PHISHY_THRESHOLD = 0.7

if __name__ == "__main__":
    # Iterate over unseen messages in the selected mailboxes and output predictions to the console
    email_listener(IMAP_SERVER, EMAIL_ADDRESS, APP_PASSWORD, MAIL_BOXES, PHISHY_THRESHOLD)
