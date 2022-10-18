from __future__ import annotations
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from typing import List

class AttributeDropout(BaseEstimator, TransformerMixin): 
    """
    Custom Transformer that removes selected attributes from the feature matrix.

    Attributes
    ----------
    exclude : List[str]
        List of features to remove.

    Methods
    -------
    fit(X, y=None)
        Fit the transformer using X (placeholder).

    transform(self, X)
        Remove selected attributes from the feature matrix.
    
    Usage
    -----
    Transformation step in the pipeline.
    
    Example
    -------
    Let's assume we want to exclude columns ['X-Priority', 'Attachments'] from the output.
    The pipeline should be initialized as:
        
    sklearn.pipe.Pipeline(steps=[
        ...,
        ('drop_out', AttributeDropout(exclude=['X-Priority', 'Attachments'])),
        ...
    ])
    """ 

    def __init__(self, exclude: List[str]) -> None:
        """
        Constructs all the necessary attributes for the custom transformer object.

        Parameters
        ----------
        exclude : List[str]
            List of features to remove.
        """
        super(AttributeDropout, self).__init__()
        self.exclude = exclude
    
    def fit(self, X: pd.DataFrame , y=None) -> AttributeDropout:
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
        self : AttributeDropout
            This transformer.
        """
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Remove selected attributes from the feature matrix.

        Parameters
        ----------
        X : pd.DataFrame of shape (n_samples, n_features)
            Input data to be transformed.
        
        Returns
        -------
        X_t : pd.DataFrame
            DataFrame without the removed attributes.
        
        Raises
        ------
        KeyError
            If any of the labels is not found in the columns.
        """
        return X.drop(columns=self.exclude)