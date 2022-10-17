Introduction
============

Project goal
============

Approach
========

Methods
=======

Results
=======

Summary and conclusion
======================

Usage manual
============
1. ./scripts/main.py is running the email listener, which scans for unseen emails in the specified folders. 
2. If there are any messages that were not opened yet, LSTM and KNN models are loaded.
3. Prediction probability for the phishing class received from the weak learners ensembled in bagging is compared agains the predefined threshold. 
4. Output is printed to the console.
