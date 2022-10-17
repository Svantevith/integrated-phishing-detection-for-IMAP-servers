import os
import re
import mailbox
import email.header
from typing import Generator, List
from classes.MboxParser import MboxParser

"""
Python file containing helper functions.
"""

def get_newest_directory(root_dir: str) -> str:
    """
    Find the most recently created folder in the specified root directory.
    
    Parameters
    ----------
    root_dir : str
        Directory, which to search for folders in.
    
    Returns
    -------
    dir : str
        String path to the newest directory.
    """
    return max([os.path.join(root_dir, dir) for dir in os.listdir(root_dir)], key=os.path.getmtime)

def parse_data_from_mbox(
    mbox_path: str, is_phishy: bool
) -> Generator[dict, None, None]:
    """
    Generator yielding dictionaries containing data parsed from the mbox file.
    
    Parameters
    ----------
    mbox_path : str
        Path to the mbox file
    is_phishy : str
        Label assigned to the emails from the mbox

    Yields
    ------
    data : Dict[str, Sequence]
        Dictionary storing data parsed from the mbox file.
    
    Usage
    -----
    Efficiently create a DataFrame from the output Generator of dictionaries.    
    """
    mbox = mailbox.mbox(mbox_path)
    for email_obj in mbox:
        message_obj = MboxParser(email_obj)
        yield {**message_obj.parsed_email_data, "Is Phishy": is_phishy}


def decode_mime_words(text: str) -> str:
    """
    Decode MIME-Encoded words.
    
    Parameters
    ----------
    text : str
        Text to decode.
    
    Returns
    -------
    text_out : str
        Decoded text.
    """
    return u''.join(
        word.decode(encoding or 'UTF-8') if isinstance(word, bytes) else word
        for word, encoding in email.header.decode_header(text))

def parse_uid(response: List[bytes]) -> str:
    """
    Parse UID from the IMAP server response.
    
    Parameters
    ----------
    response : bytearray
        Response bytearray from the IMAP server.
    
    Returns
    -------
    uid : str
        UID as a string.
    """ 
    uid = response[0].decode("utf-8") 
    match = re.compile(r'\d+ \(UID (?P<uid>\d+)\)').match(uid)
    return match.group('uid') if match else ''