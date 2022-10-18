from __future__ import annotations
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from typing import List, Callable

from .AttributeAdderError import AttributeAdderError

class AttributeAdder(BaseEstimator, TransformerMixin): 
    """
    Custom Transformer class that applies a function on the input columns passed to the transformer and adds transformed data as new features to the output matrix.

    Attributes
    ----------
    attribs_in : List[str]
        List of processed input features.
    attribs_out : List[str]
        List of features added to the output matrix.
    func : Callable
        Function applied to transform input features.

    Methods
    -------
    fit(X, y=None)
        Fit the transformer using X (placeholder).

    transform(self, X)
        Transform X by applying a function to the specified columns and concatenate resulting axes as new columns.
    
    Usage
    -----
    Transformation step in the pipeline.
    
    Example
    -------
    Let's assume the input feature matrix consists of two columns: ['Net Salary', 'Gross Salary']
    We want to calculate mean salaries and add these values as new attributes: ['Avg Net Salary', 'Avg Gross Salary']
    The pipeline should be initialized as:
        
    sklearn.pipe.Pipeline(steps=[
        ...,
        ('avg_salaries', AttributeAdder(attribs_in=['Avg Net Salary', 'Avg Gross Salary'], attribs_out=['Net Salary', 'Gross Salary'], func=np.mean)),
        ...
    ])
    """

    def __init__(self, attribs_in: List[str], attribs_out: List[str], func: Callable) -> None:
        """
        Constructs all the necessary attributes for the custom transformer object.

        Parameters
        ----------
        attribs_in : List[str]
            List of processed input features.
        attribs_out : List[str]
            List of features added to the output matrix.
        func : Callable
            Function applied to transform input features.
        
        Raises
        ------
        AttributeAdderError
            An exception is raised when the number of columns in the transformed input (attribs_in) is not equal to the number of attributes added (attribs_out). 
        """
        if len(attribs_in) != len(attribs_out):
            raise AttributeAdderError

        super(AttributeAdder, self).__init__()
        self.attribs_in = attribs_in
        self.attribs_out = attribs_out
        self.func = func
    
    def fit(self, X: pd.DataFrame , y=None) -> AttributeAdder:
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
        self : AttributeAdder
            This transformer.
        """
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transform X by applying a function to the specified columns and concatenate resulting axes as new columns.

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
        X_ = X[self.attribs_in].applymap(self.func)
        return pd.DataFrame(
            data=np.c_[X, X_],
            columns=[*X.columns, *self.attribs_out]
        )