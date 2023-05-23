# syntax=docker/dockerfile:1

FROM ubuntu:22.04

RUN apt-get update

RUN apt-get install -y python3 python3-pip

RUN apt-get install -y python3-smbus python3-dev i2c-tools

RUN apt-get install -y libmariadb-dev

RUN pip install mariadb

RUN apt-get -y install cron

RUN DEBIAN_FRONTEND=noninteractive apt-get -y install tzdata

ENV TZ=America/Phoenix

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ADD configuration.py /configuration.py

ADD csv2sql.py /csv2sql.py

ADD CronCSVtoSQL.txt /etc/cron.d/cronjob

RUN touch /var/log/cron.log

RUN mkdir /logs

RUN chmod 0644 /etc/cron.d/cronjob

RUN chmod +x /csv2sql.py

CMD cron \
    && bash
