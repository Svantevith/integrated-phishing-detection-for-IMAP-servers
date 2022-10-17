class IMAPAllocationError(Exception):
    """
    Exception raised when moving (coping & deletion) of an email message on an IMAP server fails.     

    Attributes
    ----------
    message : str
        Message describing raised Exception.
    
    Usage
    -----
    Try to catch exception when connection with an IMAP server is established and allocation of an email message takes place.
    """

    def __init__(self, message: str = "Allocation of an email failed."):
        """
        Constructs all the necessary attributes for the custom Exception object.

        Parameters
        ----------
        message : str, optional
            Message describing raised Exception.
            Default is "Allocation of an email failed".
        """
        self.message = message
        super().__init__(self.message)