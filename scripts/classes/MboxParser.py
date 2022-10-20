import mailbox
import re
import bs4
from email.message import Message
import warnings
from typing import Union, Dict, List, Tuple, Any, Generator
from .PhishyMatcher import PhishyMatcher
from .HTMLFinder import HTMLFinder

warnings.filterwarnings("ignore", category=UserWarning, module="bs4")

class MboxParser(PhishyMatcher, HTMLFinder):
    """
    Class to parse email data from the mboxMessage objects (specifically used by the Gmail services0.

    Attributes
    ----------
    keys : List[str]
        List of keys to use for parsing essential email attributes.
    email_data : mailbox.mboxMessage
        mboxMessage object storing email data.
    parsed_email_data : Dict[str, Sequence]
        Dictionary storing parsed email data.

    Methods
    -------
    read_email_payload()
        Read email payload and parse content data. 
    _get_email_messages(email_payload)
        Generator yielding each message separate from the payload.
    _extract_email_data(msg)
        Extract email data from the email message. 
    _get_html_text(html)
        Get text from the HTML code.

    Usage
    -----
    While iterating over multiple mboxMessage objects, yield parsed_email_data property and covert concatenated dictionaries into a pandas DataFrame.
    """

    # Type hinting for email message
    EmailMessage = Union[Message, str]
    # Type hinting for email payload
    EmailPayload = List[Message] 
    # Type hinting for email data (Content-Type, Content-Encoding, Content-Disposition, Filename, Text)
    EmailData = Tuple[str, str, str, str, str]

    def __init__(self, email_data: mailbox.mboxMessage):
        """
        Constructs all the necessary attributes for the MboxParser object.

        Parameters
        ----------
        email_data : mailbox.mboxMessage
            mboxMessage object storing email data.
        
        Raises
        ------
        TypeError is raised if email_data parameter is not an mailbox.mboxMessage instance.
        """ 
        if not isinstance(email_data, mailbox.mboxMessage):
            raise TypeError('Variable must be type mailbox.mboxMessage')
        super(PhishyMatcher, self).__init__()
        super(HTMLFinder, self).__init__()
        self.keys = ['Message-ID', 'Date', 'From', 'To', 'Subject', 'Content-Length', 'X-Virus-Scanned', 'X-Priority']
        self.email_data = email_data

    @property
    def parsed_email_data(self) -> Dict[str, Any]:
        """
        Dictionary storing parsed email data.

        Returns
        -------
        parsed_email_data : Dict[str, Any]
            Dictionary, providing keyed-access to email message attributes.
        """
        parsed_data = {
            **{k: self.email_data.get(k, '') for k in self.keys},
            'Attached Files': [],
            'Attachments': 0,
            'URL Links': [],
            'URLs': 0,
            'IP Addresses': [],
            'IPs': 0,
            'Images Embedded': [],
            'Images': 0,
            'Encoding': 'NA',
            'Is HTML': False,
            'Is JavaScript': False,
            'Is CSS': False,
            'Raw Message': '',
            'Extracted Text': '',
        }

        parsed_data['Message-ID'] = str(parsed_data['Message-ID']).strip('<>')

        def extract_attributes(is_html: bool = False) -> None:
            """
            Extract relevant attributes from the raw message content and update parsed_data in-place.

            Parameters
            ----------
            is_html : bool
                Flag indicating presence of HTML content in the message.
            """
            urls = self.extract_URLs_from_HTML(raw_msg) if is_html else self.extract_URLs_from_text(raw_msg)
            parsed_data['URL Links'] = urls
            parsed_data['URLs'] = len(urls)

            ips = self.find_IPs(raw_msg)
            parsed_data['IP Addresses'] = ips
            parsed_data['IPs'] = len(ips)

            parsed_data['Encoding'] = encoding
            parsed_data['Raw Message'] = raw_msg


        # Parse data from email payload
        payload = self.read_email_payload()
        # parsed_data['Payload'] = payload

        # Flag if there is plain text in the payload
        is_plain = any(
            data[0] == 'text/plain' and data[-1]
            for data in payload
        )

        # Flag if there is formatted text in the payload
        is_formatted = any(
            data[0] in ['text/html', 'NA'] and data[-1]
            for data in payload
        )

        # Flag if formatted text was parsed already
        is_parsed = False
        
        for email_part in payload:
            content_type, encoding, disposition, filename, raw_msg = email_part
            # Differentiate between attached files and embedded images
            # Embedded images are digested within the HTML code
            if disposition == 'attachment':
                parsed_data['Attachments'] += 1
                parsed_data['Attached Files'].append(filename)
            
            if raw_msg:
                if content_type == 'text/javascript':
                    parsed_data['Is JavaScript'] = True
                
                elif content_type == 'text/css':
                    parsed_data['Is CSS'] = True 

                elif content_type == 'text/plain':
                    parsed_data['Extracted Text'] = raw_msg
                    if not is_formatted:     
                        extract_attributes(is_html=False)
                    
                
                elif content_type in ['text/html', 'NA'] and not is_parsed:        
                    self.feed(raw_msg)
                    parsed_data['Is HTML'] = self.contains_html
                    parsed_data['Is JavaScript'] = self.contains_js
                    parsed_data['Is CSS'] = self.contains_css  
                    parsed_data['Images Embedded'] = self.images
                    parsed_data['Images'] = len(self.images) 

                    extract_attributes(is_html=True)

                    if not is_plain:
                        msg_text = self._get_html_text(raw_msg)
                        parsed_data['Extracted Text'] = msg_text if msg_text else raw_msg
                    
                    is_parsed = True 

        return parsed_data

    def read_email_payload(self) -> List[EmailData]:
        """
        Read email payload and parse content data. 

        Returns
        -------
        email_payload : List[EmailData]
            List of parsed content data extracted from the email payload. 
        """
        email_payload = self.email_data.get_payload()
        if self.email_data.is_multipart():
            email_messages = list(self._get_email_messages(email_payload))
        else:
            email_messages = [email_payload]
        return [self._extract_email_data(msg) for msg in email_messages]

    def _get_email_messages(self, email_payload: EmailPayload) -> Generator[EmailMessage, None, None]:
        """
        Generator yielding each message separate from the payload.

        Parameters
        ----------
        email_payload : EmailPayload
            Payload retrieved from the mboxMessage object.
        
        Yields
        ------
        message : EmailMessage
            Singular message.
        """
        for msg in email_payload:
            if isinstance(msg, (list, tuple)):
                for sub_msg in self._get_email_messages(msg):
                    yield sub_msg
            elif msg.is_multipart():
                for sub_msg in self._get_email_messages(msg.get_payload()):
                    yield sub_msg
            else:
                yield msg

    def _extract_email_data(self, msg: EmailMessage) -> EmailData:
        """
        Extract all email data fields from the email message. 

        Parameters
        ----------
        msg : EmailMessage
            Singular message.
        
        Returns
        -------
        email_fields : EmailData
            Content-type, content-encoding, content-disposition, filename, and text.
        """
        def extract_content_data() -> Tuple[str, str]:
            """
            Extract content data from the email message.

            Returns
            -------
            content_fields : Tuple[str, str]
                Content-disposition and filename.
            """
            content_disposition = 'NA' if isinstance(msg, str) else msg.get('Content-Disposition', 'NA')
            if content_disposition != 'NA':
                filename_regex = r'[^</*?"\\>:|]+'
                any_char = r'[\S\s]*'
                match = re.match(fr'^(\w+)(?:;{any_char}filename{any_char}={any_char}"({filename_regex})")?', content_disposition)
                disposition, filename = match.groups()
                if not filename:
                    filename = 'NA'
                return disposition, filename
            return 'NA', 'NA'

        content_type = 'NA' if isinstance(msg, str) else msg.get_content_type()
        encoding = 'NA' if isinstance(msg, str) else msg.get('Content-Transfer-Encoding', 'NA')
        disposition, filename = extract_content_data()
        if content_type.startswith('text') and 'base64' not in encoding:
            msg_text = msg.get_payload().strip()
        elif content_type == 'NA':
            msg_text = msg.strip()
        else:
            msg_text = ''
        return (content_type, encoding, disposition, filename, msg_text)

    @staticmethod
    def _get_html_text(html: str) -> str:
        """
        Get text from the HTML code.

        Parameters
        ----------
        html : str
            String containing HTML snippet.
        
        Returns
        -------
        text : str
            Text parsed from the HTML body.
        """
        try:
            return bs4.BeautifulSoup(html, 'lxml').body.get_text(' ', strip=True)
        except AttributeError:  # message content is empty
            return ''