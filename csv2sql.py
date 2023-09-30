#!/usr/bin/env python3

# import libraries
import mariadb
import csv
import datetime
import os
import logging
import pytz
import yaml

# Get the current date in the format YYYYMMDD
current_date = datetime.datetime.now().strftime("%Y%m%d")

logging.basicConfig(filename=f"csv2sql-{current_date}.log", level=logging.DEBUG) # use this line to create log file in working directory
# logging.basicConfig(filename='/home/supervisor/CSVtoSQL/csv2sql.log', level=logging.DEBUG) # Use this line for absolute path

# Get the directory of the current script file
script_dir = os.path.dirname(os.path.abspath(__file__))

# Build the full path to the configuration file
config_file_path = os.path.join(script_dir, 'configuration.yaml')

# Load the YAML file
with open(config_file_path, 'r') as file:
    config = yaml.safe_load(file)

# Access the variables
DB_HOST = config['db_host'] # IP address of the MySQL database server
DB_USER = config['db_user'] # User name of the database server
DB_PASSWORD = config['db_password'] # Password for the database user
DB_NAME = config['db_name'] # Database to be accessed
DB_PORT = config['db_port'] # Port used by db
TABLE_NAME = config['table_name'] # Table to write data to

# Extract the 'datatypes' list from the configuration file
datatypes_yaml = config['datatypes']
# Convert YAML list to Python list
DATATYPES = list(datatypes_yaml)

# Establish path to directory containing files or all other data directories
PARENT_DIR_PATH = config['parent_dir_path']

# Get a list of all directories contained in parent directory except for directories titled "logs"
Directories = [
              directory
              for directory in os.listdir(PARENT_DIR_PATH)
              if directory != "logs" and os.path.isdir(os.path.join(PARENT_DIR_PATH, directory))]


def get_last_csv_line(file_path):
    # Empty string to later convert list into a string in order to use find
    tempstring = ''
    with open(file_path, 'r') as file:
        # Replace any null values with a ? so that they can be identified later
        reader = csv.reader(x.replace('\0','?') for x in file)
        lines = [] # Empty list
        for line in reader:
           # Search for ? i.e. null characters in data
           foundnull = tempstring.join(line).find('?')
           # Find returns a value if character is found, -1 if not found
           if (foundnull != -1):
              continue # Skip the line if it has null value(s)
           else:
              lines.append(line)
        if lines:
            return lines[-1]  # Return the last line
        else:
            logging.debug(f"{file_path} is empty or all data is corrupt")
            return None


def get_csv_header(file_path):
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        header = next(reader)  # Read the header line
    return header


def create_database(cursor, db_name):
    # Create database if it does not exist
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


def create_table(cursor, table_name, file_path):
    # Check if the table already exists
    cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
    result = cursor.fetchone()
    if result:
        pass
#        logging.info(f"Table {table_name} already exists.")
    else:
        try:
           header = get_csv_header(file_path)
           compare_csv_and_config(header) # Check for equal # of datatypes and csv file columns
           # Create table if it does not exist
           create_table_query = f"""CREATE TABLE IF NOT EXISTS {table_name} (
                  id INT NOT NULL AUTO_INCREMENT,
                  Station CHAR(30) NOT NULL,"""
           # Append columns and datatypes to query
           for column, datatype in zip(header, DATATYPES):
              #print(f"column {column} is type {datatype}")                    # FOR DEBUGGING
              create_table_query += f"\n{column} {datatype},"
              # Select keys to ensure uniqueness in table
              if(datatype.startswith('DATETIME')):
                 keyvar1 = column # Define first key as timestamp
              elif(datatype.startswith('CHAR')):
                 keyvar2 = column # Define second key as string, hopefully a unique identifying name
              else:
                if(keyvar2):
                   pass
                else:
                   keyvar2 = column # Second key defaults to last column in table
           create_table_query += f"""PRIMARY KEY ({keyvar1}, {keyvar2}),
                  KEY id_key (id)
                  );"""
           # Create the table
           cursor.execute(create_table_query)
           logging.info(f"Table {table_name} created successfully.")
        except Exception as e:
           logging.error(f"An error occurred while creating the table {table_name}: {str(e)}")


def check_file_in_db(file_path, max_station_ts_in_db):
     # Get the last line of the current file
     last_line = get_last_csv_line(file_path)
     # Assign the values in the last line to variables dynamically using a dictionary
     variables = {f"{i}": value for i, value in enumerate(last_line)}
     # Find timestamp column
     for i in range(len(variables)):
        current_value = variables[f"{i}"]  # Assign the value to a variable
        if DATATYPES[i].startswith('DATETIME'):
           max_ts_in_file = format_timestamp(current_value)  # Format the timestamp
#           print(f"csv file max ts: {max_ts_in_file}")                     # FOR DEBUGGING
     if max_ts_in_file >= max_station_ts_in_db:
        return None # File not in db
     else:
        return True # File is in db



def format_timestamp(timestamp):
     try:
        if timestamp.endswith('Z'): # Convert UTC Z into UTC 00:00
           timestamp = timestamp.replace('Z', '+00:00')
        ts = datetime.datetime.fromisoformat(timestamp)
        if ts.tzinfo is not None and ts.tzinfo != pytz.UTC:
           ts = ts.astimezone(pytz.UTC) # Convert timestamp to UTC if it is not already
        timestamp = ts.strftime('%Y-%m-%d %H:%M:%S.%f') # Format the string to remove timezone offset
        return timestamp
     except Exception as e:
        logging.error(f"An error occurred while formatting the timestamp: {str(e)}")


def process_csv_file(connection_object, table_name, station_name, file_path):
     # Empty string to later convert list into a string in order to use find
     tempstring = ''
     with open (file_path, 'r') as f:
          # Replace any null characters
          reader = csv.reader(x.replace('\0','?') for x in f)
          columns = next(reader)
          columns.insert(0, "Station") # Insert a column named Station
          insertquery = 'insert into {0} ({1}) values ({2})'
          # Fill query placeholders with column names and # of question marks equal to the number of columns
          insertquery = insertquery.format(table_name, ','.join(columns), ','.join('?' * len(columns)))
          cursor = connection_object.cursor()
          for row in reader:
              # Search for ? i.e. null characters in data
              foundnull = tempstring.join(row).find('?')
              # Find returns a value if character is found, -1 if not found
              if (foundnull != -1):
                 logging.info(f"skipping over corrupt data in {file_path} at line {row}")
                 continue # Skip the line if it has null value(s)
              else:
                 # Insert line into table
                 row[0] = format_timestamp(row[0]) # Format timestamp
                 row.insert(0, station_name) # Insert Station name into line
                 try:
                    cursor.execute(insertquery, row)
                 except Exception as e:
                    error_message = str(e)
                    if "Duplicate entry" not in error_message:  # Ignore duplicate entry errors
                       logging.debug(f"Query execution failed: {error_message}")
#          connection_object.commit()
          logging.info(f"{file_path} staged for addition to database")


def process_files_in_directory(directory_path, cursor, table_name, station_name, connection_object):
    # Get the current time
    current_time = datetime.datetime.now()
    # Define a time delta to be 24 hours
    delta = datetime.timedelta(hours=24)
    # Get list of files in given directory
    file_list = os.listdir(directory_path)
    # Sort files in ascending order by date
    file_list.sort()
    # Initialize to none
    last_station_ts = None
    # Loop through all files in the sorted list
    for filename in file_list:
        file_path = os.path.join(directory_path, filename) # Get the full path for a file
        # Test if file_path is a file or directory
        if os.path.isfile(file_path):
           # Create table
           create_table(cursor, table_name, file_path) # Parameters are (cursor, table name, csv file)
           if(last_station_ts):
              pass
           else:
              # Get most recent timestamp from the current directory being processed
              last_station_ts = get_latest_station_ts(cursor, table_name, station_name, file_path)
           file_in_db = check_file_in_db(file_path, last_station_ts) # Check if file exists in db
           # Check if the row exists
           if file_in_db:
             # File is in db
             logging.info(f"{file_path} already in table")
           else:
             # File not in db
             last_modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path)) # Create variable for when the file was last modified
             # Check if file isn't a directory and check if modified within last 24 hours
             if current_time - last_modified_time > delta:
                # File was edited over 24 hours ago
                process_csv_file(connection_object, table_name, station_name, file_path) # Insert file into table, Parameters are (connection_object, table_name, station_name, file_path)
             else:
                # File was edited within 24 hours ago
                logging.info(f"{file_path} was last modified within 24 hours")
                process_csv_file(connection_object, table_name, station_name, file_path) # Insert file into table, Parameters are (connection_object, table_name, station_name, file_path)


def get_latest_station_ts(cursor, table_name, station_name, file_path):
     #get the last line of the current file
     last_line = get_last_csv_line(file_path)
     # Assign the values in the last line to variables dynamically using a dictionary
     variables = {f"{i}": value for i, value in enumerate(last_line)}
     # Get the header of the csv file
     header = get_csv_header(file_path)
     compare_csv_and_config(header) # Check for equal # of datatypes and csv file columns
     column = None # Initialize column to None
     # Find timestamp column
     for i in range(len(variables)):
        if DATATYPES[i].startswith('DATETIME'):
           column = header[i]  # Get the column name that contained the DATETIME value
     if(column is None):
        logging.error("Error: No timestamp column detected in csv file")
        exit()
     # Execute query to get most recent timestamp in table
     query = "SELECT MAX({})FROM {} WHERE Station LIKE '{}';"
     query = query.format(column, table_name, station_name)
     cursor.execute(query)
     # Fetch the result of the query
     result = cursor.fetchone()
     if result[0] is None:
        # No Station data in DB, assign default value 0
        return '0'
     else:
        # Format most recent timestamp from current directory
        max_ts_in_db = result[0].strftime('%Y-%m-%d')
#       print(f"station max ts: {max_ts_in_db} from {station_name}")                     # FOR DEBUGGING
        return max_ts_in_db


# Function to make sure there are equal # of datatypes and csv file columns
def compare_csv_and_config(header):
    header_elements = len(header)
    datatype_elements = len(DATATYPES)
    if(header_elements != datatype_elements):
       logging.error(f"""Error: Mismatch in csv columns and datatypes. There are {header_elements} columns in the CSV file
             and {datatype_elements} listed datatypes in the configuration file.""")
       exit()


def main():
  try:
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
        # Multiple directories, process the files in each one
        for Directory in Directories:
           dir_path = os.path.join(PARENT_DIR_PATH, Directory)
           # extract the last component of the path, i.e. the directory name and store it as the station name
           STATION_NAME = os.path.basename(dir_path)
           process_files_in_directory(dir_path, cursor, TABLE_NAME, STATION_NAME, conn) # Parameters are (directory path, cursor, table name, station name, connection object)

     else:
        STATION_NAME = os.path.basename(PARENT_DIR_PATH)
        process_files_in_directory(PARENT_DIR_PATH, cursor, TABLE_NAME, STATION_NAME, conn) # Parameters are (directory path, cursor, table name, station name, connection object)

  except Exception as e:
     logging.error(f"Database: {DB_NAME} was not updated due to error: {str(e)}")  
     exit()

  # Commit all changes to database
  conn.commit()
  # Close cursor and connection
  cursor.close()
  conn.close()
  logging.info(f"Database: {DB_NAME} was updated successfully with all staged changes")
  logging.info ("-"*100)

if __name__ == "__main__":
    main()
