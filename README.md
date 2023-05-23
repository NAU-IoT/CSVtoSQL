# CSVtoSQL
This repository contains a method to autonomously convert CSV file data into a SQL database if the csv file has not been modified within 24 hours

## Running with Docker

  - Install docker:
    - `sudo apt install docker.io`
    - Check if docker is functioning `sudo docker run hello-world`
  - Clone repository to get Dockerfile and configuration files `git clone https://github.com/NAU-IoT/CSVtoSQL.git`
  - Change into cloned directory `cd CSVtoSQL`
  - Modify configuration.py to match your current implementation `nano configuration.py`
    - Refer to comments for necessary changes
  - OPTIONAL: To change the docker containers time zone, edit line XX in the Dockerfile. A list of acceptable time zones can be found at https://en.wikipedia.org/wiki/List_of_tz_database_time_zones 
  - Build docker image in /CSVtoSQL directory `docker build -t csv2sql .` this may take a while
  - Create a directory in a convenient location to store the docker volume. For example: `mkdir /logs`
  - Create a volume to store data inside the directory created in the previous step `docker volume create --driver local 
    --opt type=none 
    --opt device=/SOME/LOCAL/DIRECTORY 
    --opt o=bind 
    YOUR_VOLUME_NAME`
  - Execute docker container in /CSVtoSQL directory `docker run --privileged -v YOUR_VOLUME_NAME:/logs -p YOUR_PORT_NUMBER:CONTAINER_PORT_NUMBER -t -i -d csv2sql`
    - Note for IoT Team: Your_port_number could be 1886, container_port_number should be 3306
  - Verify container is running `docker ps`
  - Done!


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
 
-  Install the mariadb development package `sudo apt-get install libmariadb-dev`
-  Install python/mariadb connector `sudo pip install mariadb`

## Using the Script

- Clone repository to get necessary files `git clone https://github.com/NAU-IoT/CSVtoSQL.git`
- Change into directory `cd CSVtoSQL`
- Modify configuration file to suit your implementation `nano configuration.py`
- Execute script `python3 csv2sql.py`
- Done!

## Using Grafana to display MySQL data

NOTES: 
 - These instructions use ubuntu installation, for other OS, refer to https://grafana.com/docs/grafana/latest/setup-grafana/installation/ 
 - These instructions assume you are installing grafana on the same device on which the SQL database is located

STEPS:
- Install required packages `sudo apt-get install -y apt-transport-https software-properties-common wget`
- Download the Grafana repository signing key `sudo wget -q -O /usr/share/keyrings/grafana.key https://apt.grafana.com/gpg.key`
- Add a repository for stable releases `echo "deb [signed-by=/usr/share/keyrings/grafana.key] https://apt.grafana.com stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list`
- Update the list of available packages `sudo apt-get update`
- Install the latest OSS release `sudo apt-get install grafana`
- Start the Grafana service `sudo systemctl start grafana-server.service `
- Check the status of the Grafana service to ensure it is running `sudo systemctl status grafana-server.service`


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
