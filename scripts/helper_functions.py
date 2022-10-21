import os
import re
import mailbox
import email.header
import sys
from typing import Generator, List, Dict, Any, Callable, Union
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
) -> Generator[Dict[str, Any], None, None]:
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
    data : Dict[str, Any]
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

def parse_mailboxes(response: List[bytes]) -> List[str]:
    """
    Parse mailbox names from the IMAP server response.
    
    Parameters
    ----------
    response : bytearray
        Response bytearray from the IMAP server.
    
    Returns
    -------
    mailboxes : List[str]
        List of parsed mailbox names.
    """ 
    return [mail_box.decode().split(' "/" ')[1].strip('"') for mail_box in response]

def preview_mailtree(mail_tree: List[str]) -> None:
    """
    Preview mail tree in the console.

    Parameters
    ----------
    mail_tree : List[str]
        List of mailboxes on the IMAP server.
    """
    for i, mail_box in enumerate(mail_tree, start=1):
        print(f" {i}. {mail_box.split('/')[-1]}")


def console_prompt_exception_handling(select_prompt: str, input_prompt: str, mail_tree: List[str]) -> Callable:
    """
    Exception handling component for taking user input in the console.

    Parameters
    ----------
    select_prompt : str
        Instruction displayed when user is prompted to select from available mailboxes.
    input_prompt : str
        Instruction to the user how to select chosen option(s).
    mail_tree : List[str]
        List of mailbox names.
    
    Returns
    -------
    decorator : Callable
        Function used to embed the inner wrapper and pass parameters
    """
    def decorator(func: Callable) -> Callable:
        """
        Inner wrapper passing the calling function to the parametrized wrapper.

        Parameters
        ----------
        func : Callable
            Function decorated with @console_prompt_exception_handling.
        
        Returns
        -------
        wrapper : Callable
            Parametrized wrapper for the calling function.
        """
        def wrapper(*args, **kwargs) -> Any:
            """
            Parametrized wrapper for the calling function.

            Parameters
            ----------
            args : Any
                Arguments propagated from the console_prompt_exception_handling body.
            kwargs : Any
                Keyword arguments propagated from the console_prompt_exception_handling body.
            
            Returns
            -------
            result : Any
                Return result of the calling function or None if an exception is caught (execution of the program is stopped then).
            """
            try:
                print(f"\n{select_prompt}", end='\n')
                preview_mailtree(mail_tree)
                print(f"\n{input_prompt}", end=' ')
                result = func(*args, **kwargs)
            except IndexError:
                print("[⛔] Index pointing to non-existing folder")
                sys.exit(0)
            except ValueError:
                print("[⛔] Invalid input index format")
                sys.exit(0)
            else:
                print("=" * len(input_prompt))
                return result
        return wrapper
    return decorator

def select_mailboxes(mail_tree: List[str]) -> Union[List[str], None]:
    """
    User prompt to select which mailboxes to scan for unseen emails.

    Parameters
    ----------
    mail_tree : List[str]
        List of mailboxes.
    
    Returns
    -------
    mailboxes : List[str] or None
        List of selected mailboxes or None if empty (execution of the program is stopped then). 
    """
    select_prompt = "Select folders to scan:"
    input_prompt = "Separate indices with a single space:"
    @console_prompt_exception_handling(select_prompt, input_prompt, mail_tree)
    def handle_input():
        """
        Inner function to handle user mailboxes selection.

        Returns
        -------
        mailboxes : List[str] or None
            List of selected mailboxes or None if empty (execution of the program is stopped then). 
        """
        indices = sorted(
            set(input().split()),
            key=str.lower,
        )
        if not indices:
            print("[⛔] Empty input sequence")
            sys.exit(0)
        return [mail_tree[int(i) - 1] for i in indices]
    return handle_input()

def select_spam_folder(mail_tree: List[str]) -> Union[str, None]:
    """
    User prompt to select which mailbox to move phishing emails to.

    Parameters
    ----------
    mail_tree : List[str]
        List of mailboxes.
    
    Returns
    -------
    spam_folder : str
        Name of the spam mailbox or None if empty (execution of the program is stopped then). 
    """
    select_prompt = "Select folder where to move spam:" 
    spam_default = next((mail_box for mail_box in mail_tree if 'spam' in mail_box.lower()), "")
    if spam_default:
        select_prompt = '. '.join([select_prompt[:-1], f"Leave blank to use {spam_default.split('/')[-1]} as default."])
    input_prompt = "Enter index of the mailbox:"
    @console_prompt_exception_handling(select_prompt, input_prompt, mail_tree)
    def handle_input():
        """
        Inner function to handle user spam box selection.

        Returns
        -------
        spam_folder : str
            Name of the spam mailbox or None if empty (execution of the program is stopped then).
        """
        idx = input()                
        if idx:
            spam_box = mail_tree[int(idx) - 1] 
        elif spam_default:
            spam_box = spam_default
        else:
            print("[⛔] Empty input")
            sys.exit(0)
        return spam_box
    return handle_input()