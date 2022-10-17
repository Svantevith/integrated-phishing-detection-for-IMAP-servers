import re
import spacy
import pandas as pd
from spacy.tokens.doc import Doc
from typing import Generator, List
from string import whitespace, punctuation
from sklearn.base import BaseEstimator, TransformerMixin


class SpacyPreprocessor(BaseEstimator, TransformerMixin):
    """
    Class for custom text preprocessing transformer.
    
    Attributes
    ----------
    nlp : spacy.lang.en.English
        SpaCy trained pipeline supporting English language.
    mode : str
        Determine how to exclude tokens based on allowed characters
            'all' yields all tokens
            'alpha' yields only alphabetical tokens
            'alnum' yields alphanumerical tokens 
            'ascii' yields any ascii-compliant tokens
            'non_num' yields everything except for number-like tokens
    min_length : int
        Tokens with length shorter than this value are excluded.
    keep_stop : bool
        If true, stopwords are kept.

    Methods
    -------
    fit(X, y=None)
        Fit the transformer using X (placeholder).
    transform(self, X)
        Transform X by applying preprocess_corpus function.
    preprocess_corpus(corpus)
        Preprocess text corpus.
    preprocess_document(doc)
        Generator yielding preprocessed tokens for the specified text document.
    clean_document(doc)
        Clean each word within the document and replace multiple whitespaces with a single space.
    clean_word(word)
        Remove any unicode characters, strip whitespaces and punctuation marks, while remaining non-alphanumeric characters within words.

    Usage
    -----
    Add either as a step in sklearn.pipe.Pipeline, or as a transformer in sklearn.compose.ColumnTransformer.
    """
    def __init__(self, mode: str = 'all', min_length: int = 0, keep_stop: bool = False):
        """
        Constructs all the necessary attributes for the custom transformer object.

        Parameters
        ----------
        mode : str, optional
            Determine how to exclude tokens based on allowed characters
                'all' yields all tokens (Default)
                'alpha' yields only alphabetical tokens
                'alnum' yields alphanumerical tokens 
                'ascii' yields any ascii-compliant tokens
                'non_num' yields everything except for number-like tokens
        min_length : int, optional
            Tokens with length shorter than this value are excluded. Default is 0.
        keep_stop : bool, optional
            If true, stopwords are kept. By default (False) stopwords are removed.
        """
        super(SpacyPreprocessor, self).__init__()
        self.nlp = spacy.load(
            name='en_core_web_sm', 
            disable=["parser", "ner"]
        )
        self.mode = mode
        self.min_length = min_length
        self.keep_stop = keep_stop


    def fit(self, X: pd.DataFrame, y=None):
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
        
    def transform(self, X: pd.DataFrame, y=None):
        """
        Transform X by applying preprocess_corpus function.

        Parameters
        ----------
        X : pd.DataFrame of shape (n_samples, n_features)
            Input data, of which specified subsets are used to fit the transformers.
        
        Returns
        -------
        X_t : pd.DataFrame
            Transformed corpus.
        """
        return X.apply(self.preprocess_corpus)
    
    def preprocess_corpus(self, corpus: List[str]) -> List[str]:
        """
        Preprocess text corpus.

        Parameters
        ----------
        corpus : List[str]
            List of text documents.
        
        Returns
        -------
        clean_corpus : List[str]
            Preprocessed text corpus.
        """
        return [
            # Join preprocessed docs
            ' '.join(self.preprocess_document(doc))
            # Apply initial sentence-level cleaning
            for doc in self.nlp.pipe(self.clean_document(doc=str(x)) for x in corpus)
        ]

    def preprocess_document(self, doc: Doc) -> Generator[str, None, None]:
        """
        Generator yielding preprocessed tokens for the specified text document.

        Parameters
        ----------
        doc : spacy.tokens.doc.Doc
            Document object.
        
        Yields
        -------
        lemma : str
            Lemmatized token.
        """
        # Tokenize document
        for token in doc:
            # Exclude tokens shorter than 2 characters
            # Keep in mind that high frequency of extremely short tokens might indicate fraudulent email
            if not len(token.text) >= self.min_length:
                continue

            # Exclude any non-alphanumeric tokens
            # Keep in mind that high frequency of tokens consisting of special characters might indicate fraudulent email
            if self.mode == 'alnum' and not token.text.isalnum():
                continue

            # Exclude non-ASCII tokens
            # Keep in mind that high frequency of non-ascii characters might indicate fraudulent email
            if self.mode == 'ascii' and not token.is_ascii:
                continue 

            # Exclude non-alphabetic tokens
            # Keep in mind that it limits the vocabulary to alphabetic tokens only, significantly affecting the spectrum of characters
            if self.mode == 'alpha' and not token.is_alpha:
              continue
            
            # Exclude numeric-like tokens
            # Keep in mind that high frequency of numeric-like tokens might indicate fraudulent email
            if self.mode == 'non_num' and token.like_num:
                continue
            
            # Exclude stopwords
            if not self.keep_stop and token.is_stop:
                continue
              
            # Lemmatization
            lemma = token.lemma_

            # Yield lemma
            yield lemma

    @staticmethod
    def clean_document(doc: str) -> str:
        """
        Clean each word within the document and replace multiple whitespaces with a single space. 
        
        Parameters
        ----------
        doc : str
            Input document.
        
        Returns : 
        clean_doc : str
            Clean document.
        """
        words = map(
            lambda s: SpacyPreprocessor.clean_word(s), 
            doc.casefold().split()
        )
        return ' '.join(filter(lambda s: bool(s), words))

    @staticmethod
    def clean_word(word: str) -> str:
        """
        Remove any unicode characters, strip whitespaces and punctuation marks, while remaining non-alphanumeric characters within words. 
        
        Parameters
        ----------
        word : str
            Input word.
        
        Returns : 
        clean_word : str
            Clean word.
        """
        return re.sub(
            r"_x([0-9a-fA-F]{4})_", '', word
        ).strip(whitespace + punctuation)