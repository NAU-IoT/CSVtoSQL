# CSVtoSQL
This repository contains a method to autonomously convert CSV file data into a SQL database if the csv file has not been modified within 24 hours

## Dependencies

- Install mariadb 
  - update package lists `sudo apt update`
  - install mariadb `sudo apt install mariadb-server`
  - configure mariadb for security `sudo mysql_secure_installation`
    -  When running this command, prompts will appear, follow the instructions for each prompt below:
        -  *Enter current password for root (enter for none):* PRESS ENTER
        -  *Switch to unix_socket authentication [Y/n]:* TYPE N AND ENTER
        -  *Set root password? [Y/n]:* TYPE N AND ENTER
        -  TYPE Y AND ENTER FOR ALL SUBSEQUENT PROMPTS
  - (Optional) create new user with root permissions
    -  `sudo mariadb`
    -  `GRANT ALL ON *.* TO 'YOUR_USERNAME'@'localhost' IDENTIFIED BY 'YOUR_PASSWORD' WITH GRANT OPTION;`
    -  `FLUSH PRIVILEGES;`
    -  `exit`
  -  Check the status of mariadb `sudo systemctl status mariadb`


- OR install with `sudo apt install libmariadb3 libmariadb-dev`
-  install python/mariadb connector `pip install mariadb`

## Using the Script

- Clone repository to get necessary files `git clone https://github.com/NAU-IoT/CSVtoSQL.git`
- Change into directory `cd CSVtoSQL`
- Modify configuration file to suit your implementation `nano configuration.py`
- Execute script `python3 csv2sql.py`
- Done!
