# import the mysql client for python
import mariadb
import csv
import datetime
import os

# IP address of the MySQL database server
DB_HOST = "localhost"
# User name of the database server
DB_USER = "mwc72"
# Password for the database user
DB_PASSWORD = "testpi"
#database to be accessed
DB_NAME = "PMonData"
#port used by db
DB_PORT = 1886

# Establish path to directory
Dir_Path = '/some/path/to/directory'

# Create a connection object
conn = mariadb.connect(user=DB_USER,
                       password=DB_PASSWORD,
                       host=DB_HOST,
                       port=DB_PORT,
                       database=DB_NAME)

cursor = conn.cursor()


#create table if it does not exist
create_table_query = """CREATE TABLE IF NOT EXISTS IOBoard1 (
         id INT NOT NULL AUTO_INCREMENT,
         DateAndTime DATETIME(6) NOT NULL,
         LoadName CHAR(30) NOT NULL,
         ShuntVoltage FLOAT,
         LoadVoltage FLOAT,
         Current FLOAT,
         Power FLOAT,
         PRIMARY KEY (id));"""

# To execute the SQL query
cursor.execute(create_table_query)

# Get the current time
Current_Time = datetime.datetime.now()

# Define a time delta to be 24 hours
Delta = datetime.timedelta(hours=24)

# Loop through all files in the given directory
for filename in os.listdir(Dir_Path):
   # Get the full path for a file
   File_Path = os.path.join(Dir_Path, filename)
   Last_Modified_Time = datetime.datetime.fromtimestamp(os.path.getmtime(File_Path))
   # Check if file isn't a directory and check if modified within last 24 hours
   if os.path.isfile(File_Path) and Current_Time - Last_Modified_Time > Delta:
      # File was edited over 24 hours ago, insert file into table
      with open ('PowerMonitor-20230401.csv', 'r') as f:
        reader = csv.reader(f)
        columns = next(reader)
        query = 'insert into IOBoard1({0}) values ({1})'
        # Fill query placeholders with column names and # of question marks equal to the number of columns
        query = query.format(','.join(columns), ','.join('?' * len(columns)))
        cursor = conn.cursor()
        for row in reader:
          # Parse the datetime string and remove the timezone offset
          dt = datetime.datetime.fromisoformat(row[0])
          dt = dt.replace(tzinfo=None)
          row[0] = dt.strftime('%Y-%m-%d %H:%M:%S.%f')
          cursor.execute(query, row)

        conn.commit()

conn.close()





