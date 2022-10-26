# Integrated phishing(fraud?) detection for IMAP servers
> Email listener, specifically designed for the Gmail IMAP server, automatically identifies incoming phishing emails and moves them to the spam folder. 

## Table of Contents
* [General Info](#general-information)
* [Technologies Used](#technologies-used)
* [Features](#features)
* [Screenshots](#screenshots)
* [Setup](#setup)
* [Usage](#usage)
* [Project Status](#project-status)
* [Room for Improvement](#room-for-improvement)
* [Acknowledgements](#acknowledgements)
* [Contact](#contact)
<!-- * [License](#license) -->


## General Information
- Provide general information about your project here.
- Phishing is the most prevalent method of cybercrime that convinces people to provide sensitive information; for instance, account IDs, passwords, and bank details. Emails, instant messages, and phone calls are widely used to launch such cyber-attacks. Despite constant updating of the methods of avoiding such cyber-attacks, the ultimate outcome is currently inadequate. On the other hand, phishing emails have increased exponentially in recent years, which suggests a need for more effective and advanced methods to counter them. Numerous methods have been established to filter phishing emails, but the problem still needs a complete solution. 
- What is the purpose of your project?
- The purpose of this project is to use the most recent NLP techniques to identify the patterns indicating malicious character of an email message and take the advantage of machine learning to extract the intrinsic email attributes highly related to the fraud probability. 
- Why did you undertake it?
<!-- You don't have to answer all the questions - just the ones relevant to your project. -->


## Technologies Used
- Python - version 3.9.2


## Features
List the ready features here:
- Email listener connecting to any IMAP server (specifically designed for Gmail, might cause issues on different services).
- 
- Ensemble model using bootstrap sampling


## Screenshots
![Example screenshot](./img/screenshot.png)
<!-- If you have screenshots you'd like to share, include them here. -->


## Setup
What are the project requirements/dependencies? Where are they listed? A requirements.txt or a Pipfile.lock file perhaps? Where is it located?

Proceed to describe how to install / setup one's local environment / get started with the project.


## Usage
How does one go about using it?
Provide various use cases and code examples here.

`write-your-code-here`


## Project Status
Project is: _in progress_ / _complete_ / _no longer being worked on_. If you are no longer working on it, provide reasons why.


## Room for Improvement
Include areas you believe need improvement / could be improved. Also add TODOs for future development.

Room for improvement:
- Improvement to be done 1
- Improvement to be done 2

To do:
- Feature to be added 1
- Feature to be added 2


## Acknowledgements
Give credit here.
- This project was inspired by...
- This project was based on [this tutorial](https://www.example.com).
- Many thanks to...


## Contact
Created by [@flynerdpl](https://www.flynerd.pl/) - feel free to contact me!


<!-- Optional -->
<!-- ## License -->
<!-- This project is open source and available under the [... License](). -->

<!-- You don't have to include all sections - just the one's relevant to your project -->

Usage manual
============
1. ./scripts/main.py is running the email listener, which scans for unseen emails in the specified folders. 
2. If there are any messages that were not opened yet, LSTM and KNN models are loaded.
3. Prediction probability for the phishing class received from the weak learners ensembled in bagging is compared agains the predefined threshold. 
4. Output is printed to the console.
