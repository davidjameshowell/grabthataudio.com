FROM ubuntu:14.04
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8 
ENV LANGUAGE en_US:en 
ENV LC_ALL en_US.UTF-8
RUN apt-get update -y
RUN apt-get install software-properties-common -y && apt-get install unzip -y
RUN add-apt-repository ppa:mc3man/trusty-media
RUN apt-get update -y
RUN apt-get install ffmpeg -y
RUN apt-get install python3 -y && apt-get install python3-pip -y
RUN apt-get install curl -y && apt-get install wget -y
RUN wget https://github.com/bloomreach/s4cmd/archive/2.0.1.zip
RUN unzip 2.0.1.zip
WORKDIR /s4cmd-2.0.1
RUN python3 setup.py install
WORKDIR /
RUN pip3 install python-dateutil youtube-dl boto3 pytz raven
WORKDIR /tmp
ADD s3cfg.txt /tmp/.s3cfg
ADD process_file.py /tmp/process_file.py
ADD s4cmd.txt /usr/local/bin/s4cmd
RUN chmod +x /usr/local/bin/s4cmd