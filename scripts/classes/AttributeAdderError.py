class AttributeAdderError(Exception):
    """
    Exception raised when the number of input columns passed to the AttributeAdder constructor differs from the specified number of attributes to add.  

    Attributes
    ----------
    message : str
        Message describing raised Exception.
    
    Usage
    -----
    ColumnTransformer([(name, AttributeAdder(attributes), columns)]) 
        - columns have shape (a,)
        - attributes have shape (b,)
    Exception is raised when a != b
    """

    def __init__(self, message: str = "Dimensions of the input columns and attributes to add cannot differ one from another."):
        """
        Constructs all the necessary attributes for the custom Exception object.

        Parameters
        ----------
        message : str, optional
            Message describing raised Exception.
            Default is "Dimensions of the input columns and attributes to add cannot differ one from another".
        """
        self.message = message
        super().__init__(message)