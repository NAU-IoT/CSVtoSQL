#!/usr/bin/env python3

# import libraries
import mariadb
import csv
import datetime
import os
import configuration as config
import logging
import pytz

# logging.basicConfig(filename='csv2sql.log', level=logging.DEBUG) # use this line to create log file in working directory
logging.basicConfig(filename='/home/supervisor/CSVtoSQL/csv2sql.log', level=logging.DEBUG) # Use this line for absolute path

DB_HOST = config.db_host # IP address of the MySQL database server
DB_USER = config.db_user # User name of the database server
DB_PASSWORD = config.db_password # Password for the database user
DB_NAME = config.db_name # Database to be accessed
TABLE_NAME = config.table_name # Table to write data to
DB_PORT = config.db_port # Port used by db

# Establish path to directory containing files or all other data directories
Parent_Dir_Path = config.parent_dir_path

# Get a list of all directories contained in parent directory except for directories titled "logs"
Directories = [
              directory
              for directory in os.listdir(Parent_Dir_Path)
              if directory != "logs" and os.path.isdir(os.path.join(Parent_Dir_Path, directory))]

# Define function
def get_last_csv_line(file_path):
    # empty string to later convert list into a string in order to use find
    tempstring = ''
    with open(file_path, 'r') as file:
        #replace any null values with a ? so that they can be identified later
        reader = csv.reader(x.replace('\0','?') for x in file)
        lines = [] #empty list
        for line in reader:
           #search for ? i.e. null characters in data
           foundnull = tempstring.join(line).find('?')
           # find returns a value if character is found, -1 if not found
           if (foundnull != -1):
              continue # Skip the line if it has null value(s)
           else:
              lines.append(line)
        if lines:
            return lines[-1]  # Return the last line
        else:
            logging.debug(f"{file_path} is empty or all data is corrupt")
            return None

def create_database(cursor, db_name):
    #create database if it does not exist
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    # Check if an error occurred during database creation
    if cursor.rowcount == -1:
       logging.info(f"An error occurred while creating the database {db_name}.")
    else:
       # Check if the database already existed
       if cursor.rowcount == 0:
          logging.info(f"Database {db_name} already exists.")
       else:
          logging.info(f"Database {db_name} created successfully.")


def create_table(cursor, table_name):
    #create table if it does not exist
    create_table_query = f"""CREATE TABLE IF NOT EXISTS {table_name} (
           id INT NOT NULL AUTO_INCREMENT,
           DateAndTime DATETIME(6) NOT NULL,
           LoadName CHAR(30) NOT NULL,
           ShuntVoltage FLOAT,
           LoadVoltage FLOAT,
           Current FLOAT,
           Power FLOAT,
           PRIMARY KEY (DateAndTime, LoadName),
           KEY id_key (id)
           );"""
    # To execute the SQL query
    cursor.execute(create_table_query)
    # Check if an error occurred during table creation
    if cursor.rowcount == -1:
       logging.info(f"An error occurred while creating the table {table_name}.")
    else:
       # Check if the table already existed
       if cursor.rowcount == 0:
          logging.info(f"Table {table_name} already exists.")
       else:
          logging.info(f"Table {table_name} created successfully.")


def check_file_in_db(cursor, table_name, file_path):
     #get the last line of the current file
     last_line = get_last_csv_line(file_path)
     #Parse Last_Line tuple into individual variables and convert variables into correct data types
     DateAndTime, LoadName, ShuntVoltage, LoadVoltage, Current, Power = last_line
     DateAndTime = format_timestamp(DateAndTime) # Format the timestamp
     DateAndTime = datetime.datetime.strptime(DateAndTime, "%Y-%m-%d %H:%M:%S.%f") # Convert string into datetime type
     ShuntVoltage = float(ShuntVoltage)
     LoadVoltage = float(LoadVoltage)
     Current = float(Current)
     Power = float(Power)

     #The following is for debugging to ensure values and datatypes are correct before querying
     #DnT = type(DateAndTime)
     #LN = type(LoadName)
     #SV = type(ShuntVoltage)
     #LV = type(LoadVoltage)
     #C = type(Current)
     #P = type(Power)
     #print(f"DateAndTime is {DateAndTime} of type {DnT}")
     #print(f"LoadName is {LoadName} of type {LN}")
     #print(f"ShuntVoltage is {ShuntVoltage} of type {SV}")
     #print(f"LoadVoltage is {LoadVoltage} of type {LV}")
     #print(f"Current is {Current} of type {C}")
     #print(f"Power is {Power} of type {P}")

     # Execute query to check if line already exists in database
     query = "SELECT * FROM {0} WHERE DateAndTime = '{1}' AND ShuntVoltage LIKE {2} AND LoadVoltage LIKE {3} AND Current LIKE {4} AND Power LIKE {5};"
     query = query.format(table_name, DateAndTime, ShuntVoltage, LoadVoltage, Current, Power)
     cursor.execute(query)
     # Fetch the result of the query
     row = cursor.fetchone()
     return row


def format_timestamp(timestamp):
     ts = datetime.datetime.fromisoformat(timestamp)
     if ts.tzinfo != pytz.UTC:
        ts = ts.astimezone(pytz.UTC) # Convert timestamp to UTC if it is not already
     timestamp = ts.strftime('%Y-%m-%d %H:%M:%S.%f') # Format the string to remove timezone offset
     return timestamp


def process_csv_file(connection_object, table_name, file_path):
     # empty string to later convert list into a string in order to use find
     tempstring = ''
     with open (file_path, 'r') as f:
          #replace any null characters
          reader = csv.reader(x.replace('\0','?') for x in f)
          columns = next(reader)
          insertquery = 'insert into {0} ({1}) values ({2})'
          # Fill query placeholders with column names and # of question marks equal to the number of columns
          insertquery = insertquery.format(table_name, ','.join(columns), ','.join('?' * len(columns)))
          cursor = connection_object.cursor()
          for row in reader:
              #search for ? i.e. null characters in data
              foundnull = tempstring.join(row).find('?')
              # find returns a value if character is found, -1 if not found
              if (foundnull != -1):
                 logging.info(f"skipping over corrupt data in {file_path} at line {row}")
                 continue # Skip the line if it has null value(s)
              else:
                 # Insert line into table
                 row[0] = format_timestamp(row[0]) # Format timestamp
                 try:
                    cursor.execute(insertquery, row)
                 except Exception as e:
                    logging.debug(f"Query execution failed: {str(e)}")
          conn.commit()
          logging.info(f"{file_path} added to table")


def process_files_in_directory(directory_path, cursor, table_name, connection_object):
    # Get the current time
    Current_Time = datetime.datetime.now()
    # Define a time delta to be 24 hours
    Delta = datetime.timedelta(hours=24)
    # Get list of files in given directory
    File_List = os.listdir(directory_path)
    # Sort files in ascending order by date
    File_List.sort()
    # Loop through all files in the sorted list
    for filename in File_List:
        File_Path = os.path.join(directory_path, filename) # Get the full path for a file
        # test if File_Path is a file or directory
        if os.path.isfile(File_Path):
           row = check_file_in_db(cursor, table_name, File_Path) # Check if file exists in db
           # Check if the row exists
           if row:
             # Row exists
             logging.info(f"{File_Path} already in table")
           else:
             # Row does not exist
             Last_Modified_Time = datetime.datetime.fromtimestamp(os.path.getmtime(File_Path)) # Create variable for when the file was last modified
             # Check if file isn't a directory and check if modified within last 24 hours
             if Current_Time - Last_Modified_Time > Delta:
                # File was edited over 24 hours ago
                process_csv_file(connection_object, table_name, File_Path) # Insert file into table, Parameters are (connection_object, table_name, file_path)
             else:
                # File was edited within 24 hours ago
                logging.info(f"{File_Path} was last modified within 24 hours")
                process_csv_file(connection_object, table_name, File_Path) # Insert file into table, Parameters are (connection_object, table_name, file_path)
    logging.info(f"Table: {table_name} was updated successfully")


# Create a connection object
conn = mariadb.connect(user=DB_USER,
                       password=DB_PASSWORD,
                       host=DB_HOST,
                       port=DB_PORT)
cursor = conn.cursor() # Create a cusor object
create_database(cursor, DB_NAME) # Parameters are (cursor, database name)
cursor.close() # Close the cursor
conn.close() # Close initial connection

# Create a new connection object, this time including the database
conn = mariadb.connect(user=DB_USER,
                       password=DB_PASSWORD,
                       host=DB_HOST,
                       port=DB_PORT,
                       database=DB_NAME)
cursor = conn.cursor() # Create a new cursor object

if(Directories):
  # Multiple directories, create a table for each directory and process the files in each one
  for Directory in Directories:
      Dir_Path = os.path.join(Parent_Dir_Path, Directory)
      # extract the last component of the path, i.e. the directory name and store it as the table name
      TABLE_NAME = os.path.basename(Dir_Path)
      create_table(cursor, TABLE_NAME) # Parameters are (cursor, table name)
      process_files_in_directory(Dir_Path, cursor, TABLE_NAME, conn) # Parameters are (directory path, cursor, table name, connection object)
  #close cursor and connection
  cursor.close()
  conn.close()
  logging.info(f"Database: {DB_NAME} was updated successfully")
  logging.info ("-"*100)

else:
   # Only one directory, create one table and process files in directory
   create_table(cursor, TABLE_NAME) # Parameters are (cursor, table name)
   process_files_in_directory(Parent_Dir_Path, cursor, TABLE_NAME, conn) # Parameters are (directory path, cursor, table name, connection object)
   #close cursor and connection
   cursor.close()
   conn.close()
   logging.info(f"Database: {DB_NAME} was updated successfully")
   logging.info ("-"*100)
