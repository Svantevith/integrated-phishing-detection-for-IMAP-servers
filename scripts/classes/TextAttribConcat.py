import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from typing import List


class TextAttribConcat(BaseEstimator, TransformerMixin): 
    """
    Concatenate multiple columns into a new one by joining the rows with a defined separator.

    Attributes
    ----------
    attribs_in : List[str]
        List of input features to concatenate.
    attrib_out : str
        Feature to add.
    sep : str
        Separator that joins string content in selected columns.

    Methods
    -------
    fit(X, y=None)
        Fit the transformer using X (placeholder).

    transform(self, X)
        Transform X by concatenating input columns into a single one by joining the rows with a defined separator.
    
    Usage
    -----
    Transformation step in the pipeline.
    Let's assume the input feature matrix consists of two columns: ['Title', 'Description']
    We want to concatenate the text content of these columns into one: 'All Details'
    The pipeline should be initialized as:
        
        sklearn.pipe.Pipeline(steps=[
            ...,
            ('all_details', TextAttribConcat(attribs_in=['Title', 'Description'], attrib_out='All Details', sep='-')),
            ...
        ])
    """

    def __init__(self, attribs_in: List[str], attrib_out: str, sep: str = '\n'):
        """
        Constructs all the necessary attributes for the custom transformer object.

        Parameters
        ----------
        attribs_in : List[str]
            List of input features to concatenate.
        attrib_out : str
            Feature to add.
        sep : str
            Separator that joins string content in selected columns.
        """
        super(TextAttribConcat, self).__init__()
        self.attribs_in = attribs_in
        self.attrib_out = attrib_out
        self.sep = sep
    
    def fit(self, X , y=None):
        """
        Fit the transformer using X (placeholder).

        Parameters
        ----------
        X : pd.DataFrame of shape (n_samples, n_features)
            Input data, of which specified subsets are used to fit the transformers.
        y : None, optional
            Ignored.
        
        Returns
        -------
        self : TextAttribConcat
            This transformer.
        """
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transform X by concatenating input columns into a single one by joining the rows with a defined separator.

        Parameters
        ----------
        X : pd.DataFrame of shape (n_samples, n_features)
            Input data, of which specified subsets are used to fit the transformers.
        
        Returns
        -------
        X_t : pd.DataFrame
            Horizontally stacked results of the transformation.

        Raises
        ------
        KeyError
            If any of the input labels (attribs_in) is not found in the columns.
        """
        # Fill NaNs with empty string, explicitly convert columns to string dtype and join values
        X_ = X[self.attribs_in].fillna('').astype(str).agg(self.sep.join, axis=1)
        return pd.DataFrame(
            data=np.c_[X, X_],
            columns=[*X.columns, self.attrib_out]
        )