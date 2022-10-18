import pandas as pd
import numpy as np
from itertools import chain
from sklearn.compose import ColumnTransformer
from typing import List

class NamedTransformer(ColumnTransformer):  
    """
    ColumnTransformer subclass, additionally supporting a keyed-access to heterogenous, multi-dimensional transformed data.
    
    Attributes
    ----------
    features_in : List[str]
        List of input features.

    Methods
    -------
    to_frame(data)
        Convert array-like input into a pandas DataFrame.

    fit(X, y=None)
        Fit the transformer using X (placeholder).

    transform(self, X)
        Transform X by converting array-like input into a pandas DataFrame.
    
    fit_transform(self, X, y)
        Fit and transform the data.
    
    Usage
    -----
    Use as a step in a sklearn.pipe.Pipeline to propagate forward a preprocessed tabular pd.DataFrame structure instead of a sparse-matrix.
    Output having labeled axes is beneficial if access to specific columns is necessary in subsequent transformers as data is propagated forward through a pipeline. 
    Manipulating with sparse matrices negatively impacts the computational time and memory usage as opposed to array-like objects. 
    """
    @property
    def features_in(self) -> List[str]:
        """
        List of columns from added transformers.

        Returns
        -------
        features_in : List[str]
            Concatenated list of input features used in each transformer.
        """
        return list(chain(*[cols for _,_,cols in self.transformers]))
    
    def to_frame(self, data: np.ndarray) -> pd.DataFrame:
        """
        Convert array-like input into a pandas DataFrame.

        Parameters
        ----------
        data : np.ndarray
            Array-like input.

        Returns
        -------
        df : pd.DataFrame
            Coverted pandas DataFrame.
        """
        return pd.DataFrame(data, columns=self.features_in)
    
    def fit(self, X, y = None):
        """
        Fit the transformer using X.
        ColumnTransformer-derived objects ignore the y parameter.

        Parameters
        ----------
        X : {array-like, pd.DataFrame} of shape (n_samples, n_features)
            Input data, of which specified subsets are used to fit the transformers.
        y : None, optional
            Ignored.
        
        Returns
        -------
        self : NamedTransformer
            This column transformer.
        """
        return super().fit(X, y)

    def transform(self, X) -> pd.DataFrame:
        """
        Transform X by converting array-like input into a pandas DataFrame.

        Parameters
        ----------
        X : {array-like, pd.DataFrame} of shape (n_samples, n_features)
            Input data, of which specified subsets are used to fit the transformers.
        
        Returns
        -------
        X_t : pd.DataFrame
            Converted pandas DataFrame.
        """
        return self.to_frame(super().transform(X))

    def fit_transform(self, X, y = None) -> pd.DataFrame:
        """
        Fit and transform the transformer using X.

        Parameters
        ----------
        X : {array-like, pd.DataFrame} (n_samples, n_features)
            Input data, of which specified subsets are used to fit the transformers.
        y : None, optional
            Ignored.
        
        Returns
        -------
        self : NamedTransformer
            This estimator.
        """
        return self.to_frame(super().fit_transform(X))