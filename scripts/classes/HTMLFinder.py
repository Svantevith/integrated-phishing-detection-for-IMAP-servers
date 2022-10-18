from html.parser import HTMLParser
from itertools import chain
from typing import List


class HTMLFinder(HTMLParser):
    """
    Class to parse the HTML and extract attributes specific to the email content.

    Attributes
    ----------
    start_tags : List[str]
        List containing opening HTML tags.
    end_tags : List[str]
        List containing closing HTML tags.
    attributes : List[str]
        List containing HTML attributes.
    contains_html : bool
        Flag indicating valid HTML content.
    contains_html : bool
        Flag indicating valid JavaScript content.
    contains_css : bool
        Flag indicating valid CSS content.
    images: List[str]
        List of images in the HTML.

    Methods
    -------
    handle_starttag(tag, attrs)
        Append new opening tags and attributes.

    handle_endtag(self, tag)
        Append new closing tags.
    
    contains_content_type(content_type)
        Return boolean flag indicating MIME content-type presence. 
    """ 
    def __init__(self) -> None:
        """
        Constructs all the necessary attributes for the custom HTMLParser object.
        """
        super(HTMLParser, self).__init__()
        self.start_tags = []
        self.end_tags = []
        self.attributes = []

    @property
    def contains_html(self) -> bool:
        """
        Flag indicating valid HTML content.

        Returns
        -------
        contains_html : bool
            True if the HTML code is valid else False.
        """
        # https://helpdesk.bitrix24.com/open/14099114/
        # https://zapier.com/help/doc/what-html-tags-are-supported-in-gmail
        allowed_tags = [
            "a",
            "b",
            "br",
            "big",
            "blockquote",
            "caption",
            "code",
            "del",
            "div",
            "dt",
            "dd",
            "font",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "hr",
            "i",
            "img",
            "ins",
            "li",
            "map",
            "ol",
            "p",
            "pre",
            "s",
            "small",
            "strong",
            "span",
            "sub",
            "sup",
            "table",
            "tbody",
            "td",
            "tfoot",
            "th",
            "thead",
            "tr",
            "u",
            "ul",
            "php",
            "html",
            "head",
            "body",
            "meta",
            "title",
            "style",
            "link",
            "abbr",
            "acronym",
            "address",
            "area",
            "bdo",
            "button",
            "center",
            "cite",
            "col",
            "colgroup",
            "dfn",
            "dir",
            "dl",
            "em",
            "fieldset",
            "form",
            "input",
            "kbd",
            "label",
            "legend",
            "menu",
            "optgroup",
            "option",
            "q",
            "samp",
            "select",
            "strike",
            "textarea",
            "tt",
            "var",
        ]
        return any(tag in self.start_tags for tag in allowed_tags)

    @property
    def contains_js(self) -> bool:
        """
        Flag indicating presence of JavaScript code inside the HTML.

        Returns
        -------
        contains_js : bool
            True if the JavaScript code is present else False.
        """
        return self.contains_content_type("text/javascript")

    @property
    def contains_css(self) -> bool:
        """
        Flag indicating presence of CSS code inside the HTML.

        Returns
        -------
        contains_css : bool
            True if the CSS code is present else False.
        """
        return self.contains_content_type("text/css")
    
    @property
    def images(self) -> List[str]:
        """
        List of images in the HTML.

        Returns
        -------
        images : List[str]
            List of image filenames embedded in the HTML code.
        """
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Image_types
        img_extensions = [
            ".apng",
            ".avif",
            ".gif",
            ".jpg",
            ".jpeg",
            ".jfif",
            ".pjpeg",
            ".pjp",
            ".png",
            ".svg",
            ".webp",
            ".bmp",
            ".ico",
            ".cur",
            ".tif",
            ".tiff",
        ]
        images = []
        for i, tag in enumerate(self.start_tags):
            if tag in ["img", "source"]:
                for attrib, val in self.attributes[i]:
                    if attrib in ["src", "srcset"]:
                        if any(val.lower().endswith(ext) for ext in img_extensions):
                            images.append(val)
        return images

    def handle_starttag(self, tag: str, attrs: List[str]) -> None:
        """
        Append new opening tag and attributes.

        Parameters
        ----------
        tag : str
            Opening HTML tag.
        attrs : List[str]
            HTML attributes related to the tag.
        """
        self.start_tags.append(tag)
        self.attributes.append(attrs)

    def handle_endtag(self, tag: str) -> None:
        """
        Append new closing tag.

        Parameters
        ----------
        tag : str
            Closing HTML tag.
        """
        self.end_tags.append(tag)
    
    def contains_content_type(self, content_type: str) -> bool:
        """
        Return boolean flag indicating MIME content-type presence. 

        Parameters
        ----------
        content_type : str
            MIME content-type.

        Returns
        -------
        contains_content_type : bool
            True if there is any occurence of the specified content type among parsed attributes, else False.
        """
        for attrib, val in chain(*self.attributes):
            if attrib == "type" and val == content_type:
                return True
        return False