# %% [markdown]
# # Python for Nonprofits Part 1: Sharing Database Data Via Google Sheets
# 
# By Kenneth Burchfiel
# 
# Released under the MIT license
# 
# (Note: This project was based on my [Google Sheets Database Connections](https://github.com/kburchfiel/google_sheets_database_connections) Python project.)

# %% [markdown]
# # Introduction
# 
# This project demonstrates how to use Python to read data from a database, then export that data to a Google Sheets document. This approach can be a great way to make the contents of a database accessible to individuals who don't have a background in SQL.
# 
# If you need to update this Google Sheets document with the latest copy of your data on a regular basis, you can export this script to a Python file, then have your operating system run that task each day, hour, etc. using a tool like cron or Task Scheduler.
# 
# This project will import an entire table from a local SQLite database, then export an unmodified copy of that table to Google Sheets. However, in future Python for Nonprofits sections, I plan to demonstrate how Python's pandas library can be used to reformat and analyze data.

# %% [markdown]
# # Prerequisites:
# 
# Before you can apply this code to your own projects (or get it to run locally on your own computer), you'll need to perform some setup tasks.
# 
# ## Step 1:
# Open a Google Cloud Platform project. I used the Google Cloud Console to accomplish this step. For instructions, go to https://cloud.google.com/resource-manager/docs/creating-managing-projects#console. 
# 
# NOTE: You may incur expenses when using the Google Cloud platform.
# 
# ## Step 2:
# Enable the Google Sheets API for your project. To do so, enter 'Sheets API' within the search box near the top of the Google Cloud Platform window. Click on the 'Google Sheets API' result and then select the blue 'Enable' button. 
# 
# ## Step 3:
# Create a Google service account. You can do so by following the steps shown in Google's [Create service accounts](https://cloud.google.com/iam/docs/service-accounts-create#iam-service-accounts-create-console) documentation page. (Although this page instructs you to "enable the IAM API," I didn't need to do so in order for the following steps to work, but it's possible that this API had been enabled beforehand for my Cloud Console project.)
# 
# ## Step 4:
# Create a key in JSON format for your new service account, then download it to your computer (as a .json file) and store it in a safe location. See https://cloud.google.com/iam/docs/creating-managing-service-account-keys 
# 
# ## Step 5:
# Grant this service account Editor access to the Google Sheet to which you will need to connect. You can grant it access by clicking the 'Share' button within the presentation and then entering the service account's email within the box that appears. The address of this service account can be found within the 'Service account details' page of your service account within the Google Cloud platform.
# 
# ## Step 6: 
# To get this notebook to run on your own computer, update the 'service_key_path' variable with the path to your own service account key, then update wb_id and ws_name with your own Google Sheets workbook.

# %% [markdown]
# # Code:

# %%
print("Starting program.")
import time
start_time = time.time() # Allows the program's runtime to be measured
import pandas as pd
import sqlalchemy
import gspread
from gspread_dataframe import set_with_dataframe

# %% [markdown]
# ## Connecting to our database:
# 
# This local SQLite database was created using the database_generator.ipnyb code found in supplemental/db_generator. The steps for connecting to an online database are quite similar; for guidance on this process, visit the [app_functions_and_variables.py](https://github.com/kburchfiel/dash_school_dashboard/blob/main/dsd/app_functions_and_variables.py) file within my [Dash School Dashboard](https://github.com/kburchfiel/dash_school_dashboard) project.

# %%
pfn_db_engine = sqlalchemy.create_engine(
'sqlite:///'+'../data/network_database.db') 
# Based on:
#  https://docs.sqlalchemy.org/en/13/dialects/sqlite.html#connect-strings

pfn_db_engine

# %% [markdown]
# Here are the tables present in this database:

# %%
pd.read_sql("Select * from sqlite_schema", con = pfn_db_engine)

# %%
df_curr_enrollment = pd.read_sql("Select * from curr_enrollment", 
con = pfn_db_engine)
df_curr_enrollment

# %% [markdown]
# ## Importing our Google Cloud Project service key:
# 
# **Note: This project stores the service key in the same folder as this notebook so that you can see what it looks like; however, for real-world applications, I highly recommend storing the key in an alternate location in order to keep it more secure.**

# %%
service_key_path = 'db-to-gsheets-demo-0a2a95a56f00.json' # Make
# sure to replace this path with your own service key's path; otherwise,
# this code won't work.
gc = gspread.service_account(service_key_path) 
    # Based on https://docs.gspread.org/en/latest/oauth2.html . The 
    # 'For Bots: Using Service Account' section of this page offers a helpful
    # guide for creating and utilizing Google Cloud Console service accounts.
# This is the path to my downloaded Google Service Account key, which is 
# necessary for connecting to Google Sheets documents from your computer.

# %%
wb_id = '1LcB3bqPJ-CPUNPeR-Ohdd5bI6jjV6enh5Gd338Dqqcs' # As with your service
# key path, make sure to replace this workbook ID with your own workbook's ID.

# This ID was taken from the Google Sheets workbok's full URL:
# https://docs.google.com/spreadsheets/d/1R1AYhSBRK2QQX_obzk9iHHZQI8XmfqbZGPQouQH8fSA/edit#gid=0

ws_name = 'Current Enrollment' # The name of the worksheet itself. One workbook
# can have multiple worksheets. You'll want to either rename this workbook
# to your own worksheet's name or create a worksheet named 'Current Enrollment'
# within your workbook.

wb = gc.open_by_key(wb_id)
ws = wb.worksheet(ws_name)
ws.clear()
set_with_dataframe(ws, df_curr_enrollment) # This code uploads df_curr_enrollment
# to the worksheet specified by ws. If this code doesn't work for you, make
# sure that you have completed all of the prerequisites listed earlier 
# in this notebook.

# %%
end_time = time.time()
run_time = end_time - start_time
print(f"Finished running script in {round(run_time, 3)} seconds.")


