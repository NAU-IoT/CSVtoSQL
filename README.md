# CSVtoSQL
This repository contains scripts used to convert CSV file data into a SQL database. The function can be preformed on a directory containing csv files or on a parent directory containing subdirectories that have csv files in them.  

This repository includes information on:
  - Installing dependencies
  - How to use the scripts
  - How to adapt the script to process various csv file data
  - How to implement this function as a cron job
  - Input and expected output format
  - How to display SQL data on Grafana

## Dependencies

- Install mariadb (NOTE: Install on device hosting the database)
  - Update package lists:
  ```
  sudo apt update
  ```
  - Install mariadb: 
  ```
  sudo apt install mariadb-server
  ```
  - Configure mariadb for security:
    -  When running this command, prompts will appear, follow the instructions for each prompt below:
        -  *Enter current password for root (enter for none):* PRESS ENTER
        -  *Switch to unix_socket authentication [Y/n]:* TYPE N AND ENTER
        -  *Set root password? [Y/n]:* TYPE N AND ENTER
        -  TYPE Y AND ENTER FOR ALL SUBSEQUENT PROMPTS
  ```
  sudo mysql_secure_installation
  ```
  - (Optional) create new user with root permissions:
  ```
  sudo mariadb
  ```
  ```
  GRANT ALL ON *.* TO 'YOUR_USERNAME'@'localhost' IDENTIFIED BY 'YOUR_PASSWORD' WITH GRANT OPTION;
  ```
  ```
  FLUSH PRIVILEGES;
  ```
  ```
  exit
  ```
  -  Check the status of mariadb:
  ```
  sudo systemctl status mariadb
  ```
 
-  Install the mariadb development package: 
```
sudo apt-get install libmariadb-dev
```
-  Install python/mariadb connector:
```
sudo pip install mariadb
```
- Install YAML parsing library:
```
sudo pip install pyyaml
```

## Using the Script

- Clone repository to get necessary files: 
```
git clone https://github.com/NAU-IoT/CSVtoSQL.git
```
- Change into repository directory: 
```
cd CSVtoSQL
```
- Modify configuration file to suit your implementation:
```
nano configuration.py
```
- Execute script: 
```
python3 csv2sql.py
```
- Done!

## Adapting the Script

- Lines 79-89: Modify the create_table fucntion by changing column names and data types to apply to your data (add/remove columns as necessary)
- Lines 108-114: Change variable names and data types to reflect your tables columns and data types (refer to comments in code)
- Line 131: Modify query to reflect your column names
- Line 132: Change variable names to fit placeholders in query. These variables should be the same ones assigned at lines 108-114

## Using Cron

- Open cron table file:
```
crontab -e
```
- Modify the following lines to adjust how often the cron job executes, then paste the lines into the cron table: 
```
# execute csv2sql.py every 5 minutes
*/5 * * * * /usr/bin/python3 /SOME/PATH/TO/csv2sql.py >>/SOME/PATH/TO/csv2sql.out 2>>/SOME/PATH/TO/csv2sql.err
```
- Save the cron table and verify it was loaded by inspecting running cron jobs: 
```
crontab -l
```

## Example input and expected output

The following image displays an example of a properly formatted csv file with 3 lines of data:
<img width="529" alt="Screen Shot 2023-06-20 at 3 05 13 PM" src="https://github.com/NAU-IoT/CSVtoSQL/assets/72172361/9a66b970-849a-41dc-a87f-1347a9a8a8ae">

The image below shows the corresponding expected output when viewing the same data in MySQL. First we must select the "testdb" database created by the script, then select all the data from the "Example" table:
<img width="777" alt="Screen Shot 2023-06-20 at 3 03 56 PM" src="https://github.com/NAU-IoT/CSVtoSQL/assets/72172361/3201c1f1-a7b2-4919-b8fd-d738aec05b9b">


## Using Grafana to display MySQL data

NOTES: 
 - These instructions use ubuntu installation, for other OS, refer to https://grafana.com/docs/grafana/latest/setup-grafana/installation/ 
 - These instructions assume you are installing grafana on the same device on which the SQL database is located

STEPS:
- Install required packages 
```
sudo apt-get install -y apt-transport-https software-properties-common wget
```
- Download the Grafana repository signing key 
```
sudo wget -q -O /usr/share/keyrings/grafana.key https://apt.grafana.com/gpg.key
```
- Add a repository for stable releases: 
```
echo "deb [signed-by=/usr/share/keyrings/grafana.key] https://apt.grafana.com stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
```
- Update the list of available packages: 
```
sudo apt-get update
```
- Install the latest OSS release: 
```
sudo apt-get install grafana
```
- Start the Grafana service: 
```
sudo systemctl start grafana-server.service
```
- Check the status of the Grafana service to ensure it is running: 
```
sudo systemctl status grafana-server.service
```


Once this has ben completed, you can begin setting up a dashboard to display the data from the SQL database. For official instructions, refer to the documenation here: https://grafana.com/docs/grafana/latest/

1. Open a browser and access port 3000 of the device that the database and Grafana instance are running on
   <img width="413" alt="Screen Shot 2023-05-22 at 1 47 13 PM" src="https://github.com/NAU-IoT/CSVtoSQL/assets/72172361/6a7c722f-6b13-4bf4-a1e6-6994bcdc0bbb">
   
2. Navigate to the "Add Data Source" page and add MySQL
   <img width="1339" alt="Screen Shot 2023-05-22 at 1 58 35 PM" src="https://github.com/NAU-IoT/CSVtoSQL/assets/72172361/e5182cae-f6a2-4412-8b1b-97e168c16a82">

3. Fill out necessary fields, scroll to the bottom and click "Save and Test"
   <img width="623" alt="Screen Shot 2023-05-22 at 2 02 09 PM" src="https://github.com/NAU-IoT/CSVtoSQL/assets/72172361/26781d5d-15b3-4d43-86b2-9824eaaf19d2">

4. Back on the home page, click the plus and select "New dashboard" from the dropdown menu and select "New visualization"
   <img width="1390" alt="Screen Shot 2023-05-22 at 2 04 33 PM" src="https://github.com/NAU-IoT/CSVtoSQL/assets/72172361/a5e07160-cab1-4928-9dbc-838829a5bfa6">

5. Select type of visualization. This example is comparing Power Consumption of a load against time. Switch from builder to code under the query section. Next, write your query. Next, hit run query. Finally, if you are satisfied with the look of your graph, click Apply.
   <img width="1361" alt="Screen Shot 2023-05-22 at 2 07 56 PM" src="https://github.com/NAU-IoT/CSVtoSQL/assets/72172361/ac0704a6-fa4c-4b92-be9d-83d15012e10a">




   
