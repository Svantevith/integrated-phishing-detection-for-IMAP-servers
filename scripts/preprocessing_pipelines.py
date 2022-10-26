import re
import pandas as pd
from sklearn.pipeline import make_pipeline, Pipeline
from sklearn.compose import make_column_transformer
from sklearn.preprocessing import FunctionTransformer, MinMaxScaler
from typing import Callable, List, Union
from functools import wraps
from classes.SpacyPreprocessor import SpacyPreprocessor
from classes.TextAttribConcat import TextAttribConcat
from classes.AttributeAdder import AttributeAdder
from classes.AttributeDropout import AttributeDropout
from classes.NamedTransformer import NamedTransformer

"""
Python file containing pipelines for text & features preprocessing.
"""

def text_pipeline(min_length: int = 0, keep_stop: bool = False, keep_num_like: bool = True, alpha_only: bool = False, alnum_only: bool = False, ascii_only: bool = False) -> Pipeline:
    """
    Pipeline for text preprocessing (LSTM inputs).
    
    Parameters
    ----------
    min_length : int, optional
        Tokens with length shorter than this value are excluded. Default is 0.
    keep_stop : bool, optional
        If true, stopwords are kept. By default (False) stopwords are removed.
    keep_num_like: bool
        Yield numeric-like tokens. Default is True.
    alpha_only : bool
        Yield alphabetical tokens only. Default is False.
    alnum_only: bool
        Yield alphanumerical tokens only. Default is False.
    ascii_only : bool
        Yield ascii-compliant tokens only. Default is False.
    
    Returns
    -------
    pipe : sklearn.pipeline.Pipeline
        Pipeline of transforms with a final estimator.
    """
    text_preprocessor = make_pipeline(
        SpacyPreprocessor(min_length, keep_stop,  keep_num_like, alpha_only, alnum_only, ascii_only), 
        FunctionTransformer(pd.DataFrame.dropna)
    )
    pipe = Pipeline(steps=[
        ('text_concat', TextAttribConcat(attribs_in=['Subject', 'Raw Message'], attrib_out='Email Content', sep='\n')),
        ('text_preprocess', make_column_transformer((text_preprocessor, ['Email Content'])))
    ])
    return pipe

def features_pipeline(exclude: List[str] = [], features_out: bool = False) -> Union[Pipeline, List[str]]:
    """
    Pipeline for features preprocessing (KNN inputs).
    
    Parameters
    ----------
    exclude : List[str], optional
        List of features to exclude. Default is an empty list.
    features_out : bool, optional
        If true, output columns are returned. Default is False.

    Returns
    -------
    pipe : sklearn.pipeline.Pipeline
        Pipeline of transforms with a final estimator.
    features : List[str], optional
        List of output features. Only returned if features_out is True.
    """
    # Add 'Message Length' attribute based on the 'Raw Message' column
    attrib_adder = AttributeAdder(attribs_in=['Raw Message'], attribs_out=['Message Length'], func=get_message_length)
    
    # Transform selected columns
    preprocessor = NamedTransformer(transformers=[
        ('virus_scanned', enumerate_virus_scanned, ['X-Virus-Scanned']),
        ('priority', enumerate_priority, ['X-Priority']),
        ('encoding', enumerate_encoding, ['Encoding']),
        ('flags', enumerate_bool, ['Is HTML', 'Is JavaScript', 'Is CSS']),
        ('select', 'passthrough', ['Attachments', 'URLs', 'IPs', 'Images', 'Message Length'])
    ])

    # Drop selected columns
    attrib_dropout = AttributeDropout(exclude)

    # Define pipeline
    pipe = Pipeline(steps=[
        ('attrib_adder', attrib_adder),
        ('preprocessor', preprocessor),
        ('attrib_dropout', attrib_dropout),
        ('scaler', MinMaxScaler())
    ])

    # Get features out
    if features_out:
        features = [col for col in preprocessor.features_in if col not in exclude]
        
        # Return pipeline and features
        return pipe, features
    
    # Return pipeline
    return pipe

def get_message_length(text: str) -> int:
    """
    Function calculating length of a text message.

    Parameters
    ----------
    text : str
        Input text.
    
    Returns
    -------
    length : int
        Text length.
    """
    return len(str(text))

def transformer_wrapper(func: Callable) -> FunctionTransformer:
    """
    Wrapper for multiple FunctionTransformer object instantiation.

    Parameters
    ----------
    func : Callable
        Callable function used for the transformation. 
    
    Returns
    -------
    transformer : sklearn.preprocessing.FunctionTransformer
        Function transformer object.
    
    Usage
    -----
    Wrapper takes the advantage of functions being applied on scalar values. A wrapped function is then applied to the pandas DataFrame.
    Add the @transformer_wrapper decorator above the function definition to use as a step in sklearn.pipe.Pipeline or transformer in sklearn.compose.ColumnTransformer. 

    Let's say that we want to round up the 'Population' column to the nearest integer. 
    We define a @transformer_wrapper decorated function rounding up a floating number, returning result explicitly casted to integer type. 
    Then this function can be used as a function transformer directly.

        @transformer_wrapper
        def round_up(val: float) -> int:
            return int(np.ceil(val)) 
        
        ctf = sklearn.compose.ColumnTransformer(transformers=[
            ...
            ('round', round_up, ['Population']),
            ...
        ])
    """
    @wraps(func)
    def wrapper(df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:
        """
        Inner wrapper function using the @functools.wraps decorator to preserve the signature/information of the function passed.
        Extends an existing function, without any modification to the original function source code.
        
        Parameters
        ----------
        df : pd.DataFrame
            Input pandas DataFrame.
        
        args : Any
            Additional arguments.
        
        kwargs : Any
            Additional keyword arguments.
        
        Returns
        -------
        df_t : pd.DataFrame
            Result of applying a function to the input DataFrame.
        """
        return df.applymap(func, *args, **kwargs)
    return FunctionTransformer(wrapper)

@transformer_wrapper
def enumerate_virus_scanned(virus_scanned: str) -> int:
    """
    Function to enumerate the X-Virus-Scanned rows.

    Parameters
    ----------
    virus_scanned : str
        X-Virus-Scanned value.
    
    Returns
    -------
    enum : int
        0 if X-Virus-Scanned is null, else 1.    
    """
    try:
        return int(len(virus_scanned) > 0)
    except TypeError:
        return 0

@transformer_wrapper
def enumerate_priority(priority: str) -> int:
    """
    Function to enumerate X-Priority rows.

    Parameters
    ----------
    priority : str
        X-Priority value.
    
    Returns
    -------
    enum : int
        Enumerated X-Priority value.
    """
    try:
        return int(re.search(r'\d+', priority).group(0))
    except (AttributeError, TypeError):
        return 0

@transformer_wrapper
def enumerate_encoding(encoding: str) -> int:
    """
    Function to enumerate Encoding rows.

    Parameters
    ----------
    encoding : str
        Encoding value.
    
    Returns
    -------
    enum : int
        Enumerated Encoding value.
    """
    content_transfer_encoding = {
        "na":  0,
        "base64": 1,
        "quoted-printable": 2,
        "8bit": 3,
        "7bit": 4,
        "binary": 5
    }
    try:
        return content_transfer_encoding[encoding.lower()]
    except (AttributeError, KeyError):
        return 0

@transformer_wrapper
def enumerate_bool(boolean: bool) -> int:
    """
    Function to enumerate any boolean rows.

    Parameters
    ----------
    boolean : bool
        Boolean value.
    
    Returns
    -------
    enum : int
        Enumerated boolean value.
    """
    return int(boolean)