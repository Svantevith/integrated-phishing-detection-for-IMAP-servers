import os
import numpy as np
import pandas as pd
import joblib
import tensorflow as tf
from typing import List
from dotenv import load_dotenv
from preprocessing_pipelines import text_pipeline, features_pipeline

# Disable info & warning messages for tensorflow
tf.get_logger().setLevel('ERROR')

# Define paths to models
load_dotenv()
LSTM_PATH = os.getenv("LSTM_PATH")
ENSEMBLE_PATH = os.getenv("ENSEMBLE_PATH")


def make_predictions(dataset: pd.DataFrame) -> List[int]:
    """
    Return prediction probabilities whether input email messages are phishing or not.

    Parameters
    ----------
    dataset: pd.DataFrame
        Input pandas DataFrame containing data parsed from the email messages.
    
    Returns
    -------
    arr : np.ndarray
        Numpy array of shape (n_dims_input, 2) - value between .0 and 1. for each label.
    """
    # Preprocess corpus
    text_pipe = text_pipeline(min_length=3, keep_num_like=False)
    text_in = text_pipe.fit_transform(dataset[['Subject', 'Extracted Text']])

    # Preprocess features
    features_pipe = features_pipeline(exclude=['X-Virus-Scanned', 'Spam Score', 'Is JavaScript', 'Attachments', 'Message Length', 'URL Unicode Ratio'])
    features_in = features_pipe.fit_transform(dataset)

    # Load models
    print("\n[⌛] Loading models...")

    # Make predictions using LSTM
    empty_idx = dataset[(dataset[['Subject', 'Extracted Text']].applymap(len) == 0).all(axis=1)].index
    ## Do not return predictions for empty input strings
    if len(empty_idx) == len(dataset):
        y_pred_lstm = np.full(shape=(len(dataset),), fill_value=np.nan)
    elif len(empty_idx) < len(dataset):
        lstm = tf.keras.models.load_model(LSTM_PATH)
        y_pred_lstm = lstm.predict(text_in, verbose=0)
        if len(empty_idx) > 0:
            y_pred_lstm[empty_idx] = np.full(shape=(2,), fill_value=np.nan)

    # Make predictions using ensemble model
    ensemble = joblib.load(ENSEMBLE_PATH)
    y_pred_ensemble = ensemble.predict_proba(features_in)

    # Average prediction probabilities from heterogenous estimators
    print("[⚙️ ] Models ready!\n")
    y_pred_proba = np.nanmean([y_pred_lstm, y_pred_ensemble], axis=0)
    
    # Return prediction probabilities
    return y_pred_proba