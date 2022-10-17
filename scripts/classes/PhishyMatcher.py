import bs4
import re
import ipaddress
from typing import List
from urlextract import URLExtract


class PhishyMatcher:
    """
    Class providing various methods to help extract attributes that indicate the phishing nature of the textual data, such as the body of an email message.

    Attributes
    ----------
    URL_regex : re.Pattern
        Regex used for URL address extraction.
    IP_regex : re.Pattern
        Regex pattern used for IP address extraction.
    
    Methods
    -------
    find_IPs(text) 
        Find IP addresses within the provided text.
    extract_URLs_from_text(text)
        Find URL links within the provided text.
    extract_URLs_from_HTML(html)
        Extract URLs from the HTML code.
    clean_html(html)
        Remove any '3D' attribute prefix from the HTML code.
    clean_text(text)
        Remove multiple overlapping whitespace characters from text.
    clean_message_tags(text)
        Remove any whitespaces within the message attributes (denoted as <>).
    is_valid_IP(ip)
        Check if given IP is a valid IPv4 or IPv6 address.
    
    Usage
    -----
    Inherit from the PhishyMatcher class.
    """
    @property
    def URL_regex(self) -> re.Pattern:
        # https://daringfireball.net/2010/07/improved_regex_for_matching_urls
        # -> https://gerrit.wikimedia.org/r/c/mediawiki/extensions/Collection/OfflineContentGenerator/latex_renderer/+/170329/1/lib/index.js
        url_regex = r"""\b((?:[a-z][\w\-]+:(?:\/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}\/)(?:[^\s()<>]|\((?:[^\s()<>]|(?:\([^\s()<>]+\)))*\))+(?:\((?:[^\s()<>]|(?:\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))"""
        return re.compile(url_regex, re.IGNORECASE)

    @property
    def IP_regex(self) -> re.Pattern:
        IPv4 = r"(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
        IPv6 = r"(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9]))"
        ip_regex = fr"{IPv4}|{IPv6}"
        return re.compile(ip_regex, re.IGNORECASE)
    
    def find_IPs(self, text: str) -> List[str]:
        """
        Find IP addresses within the provided text.

        Parameters
        ----------
        text : str
            Input text.
        
        Returns
        -------
        IPs : List[str]
            List of IP addresses.
        """
        return [ip for ip in re.findall(self.IP_regex, self.clean_text(text)) if self.is_valid_IP(ip)]
    
    def extract_URLs_from_text(self, text: str) -> list:
        """
        Find URL addresses within the provided text.

        Parameters
        ----------
        text : str
            Input text.
        
        Returns
        -------
        URLs : List[str]
            List of URL addresses.
        """
        text = self.clean_text(text)
        text = self.clean_message_tags(text)
        try:
            return URLExtract().find_urls(text)
        except UnicodeDecodeError:
            return [url for url in re.findall(self.URL_regex, text) if url]

    def extract_URLs_from_HTML(self, html: str) -> List[str]:
        """
        Extract URLs from the HTML code.

        Parameters
        ----------
        html : str
            Input HTML code.
        
        Returns
        -------
        URLs : List[str]
            List of URL addresses.
        """
        # https://stackoverflow.com/questions/6976053/xss-which-html-tags-and-attributes-can-trigger-javascript-events
        url_attribs = [
            "action",
            "archive",
            "background",
            "cite",
            "classid",
            "codebase",
            "data",
            "dsync",
            "dynsrc",
            "formaction",
            "href",
            "icon",
            "longdesc",
            "lowsrc",
            "manifest",
            "poster",
            "profile",
            "src",
            "usemap",
        ]

        urls = []
        bs = bs4.BeautifulSoup(self.clean_text(html), "html.parser")
        for x in [
            [
                (attr, tag[attr])
                for tag in bs.select(f"[{attr}]")
                if not tag[attr].startswith("#")
            ]
            for attr in url_attribs
        ]:
            if x:
                for (attr, url) in x:
                    url = self.clean_html(url)
                    if attr == 'href' or re.match(self.URL_regex, url):
                        urls.append(url)

        return urls

    @staticmethod
    def clean_html(html: str) -> str:
        """
        Remove any '3D' attribute prefix from the HTML code.

        Parameters
        ----------
        html : str
            Input HTML code.
        
        Returns
        -------
        clean_html : str
            Clean HTML code.
        """
        return re.match(r"^(?:3D)?(.*)$", html).group(1).strip('"')

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Remove multiple overlapping whitespace characters from text.

        Parameters
        ----------
        text : str
            Input text.
        
        Returns
        -------
        clean_text : str
            Clean text.
        """
        return " ".join(text.split())
    
    @staticmethod
    def clean_message_tags(text: str) -> str:
        """
        Remove any whitespaces within the message attributes (denoted as <>).

        Parameters
        ----------
        text : str
            Input text.
        
        Returns
        -------
        clean_text : str
            Clean text.
        """
        return re.sub(
            pattern=r"<.*?>", 
            repl=lambda m: re.sub(r"\s+", "", m.group()), 
            string=text
        )
    
    @staticmethod
    def is_valid_IP(ip: str) -> bool:
        """
        Check if given IP is a valid IPv4 or IPv6 address.  

        Parameters
        ----------
        ip : str
            IP address.
        
        Returns
        -------
        flag : bool
            True if ip is a valid IPv4 or IPv6 address. Otherwise, False.
        """
        try:
            addr = ipaddress.ip_address(ip)
            if isinstance(addr, ipaddress.IPv4Address):
                # IPv4 packet size: 576 bytes required
                return int(addr) >= 576
            elif isinstance(addr, ipaddress.IPv6Address):
                # IPv6 packet size: 1280 bytes required
                return int(addr) >= 1280
        except ValueError:
            return False