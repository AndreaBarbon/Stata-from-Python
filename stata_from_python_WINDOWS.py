### Imports
import pandas as pd; import numpy  as np
import os;

### Stata regressions from python
#
################################################
## Dependencies for Stata: ivreg2 and reghdfe.
## Run the following in Stata to install them:
# ssc install reghdfe, replace
# ssc install ivreg2, replace
# ssc install ranktest, replace
################################################


### CONFIGURATION ##############################
#
# Change this (if needed) to point to the Stata app:
# Mac example:
# STATA_APP = "/Applications/Stata/StataMP.app/Contents/MacOS/StataMP"
# WINDOWS   = False
#
# Windows example:
STATA_APP = "C:\Program Files (x86)\Stata14\StataMP-64.exe"
WINDOWS   = True
#
# Set up the folder where outputs will be placed.
# CAUTION: the folder name cannot contain white spaces
TARGET_FOLDER = "Regressions"
# Leave it `None` if you want everyhting to stay in the main working directory
# If you change it, remember to save your .dta files in that folder
#
################################################

if TARGET_FOLDER is None: TARGET_FOLDER = os.getcwd()
slash = "\\" if WINDOWS else "/"
    
target = TARGET_FOLDER if (TARGET_FOLDER.endswith("/") | (TARGET_FOLDER=="")) else TARGET_FOLDER + slash
if not target.startswith(os.getcwd()): target = os.getcwd() + slash + target

import common_functions