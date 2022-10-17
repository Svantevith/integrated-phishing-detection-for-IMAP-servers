import pandas as pd
import numpy as np

def enumerate_virus_scanned(virus_scanned: str) -> int:
    # IT DOES NOT WORK!!!!
    """
    Function to enumerate the X-Virus-Scanned rows.

    Parameters
    ----------
    virus_scanned : str
        X-Virus-Scanned value.
    
    Returns
    -------
    i : int
        1 if virus scanned is NaN, else 0.    
    """
    try:
        return int(len(virus_scanned) > 0)
    except TypeError:
        return 0
for val in [pd.NA, pd.NaT, np.nan, '', None, 'DUPA']:
    print(enumerate_virus_scanned(val))