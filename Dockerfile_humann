FROM ubuntu:22.04

# also install python version 2 used by bowtie2
RUN apt-get update && \
    DEBIAN_FRONTEND="noninteractive" apt-get install -y python2-dev python2 python-dev-is-python3 python3 python3-dev python3-pip apt-transport-https openjdk-8-jre wget zip git-all zlib1g-dev libbz2-dev liblzma-dev libjpeg-dev
RUN pip3 install boto3 cloudpickle awscli


RUN pip3 install anadama2

# install kneaddata and dependencies
RUN pip3 install humann==3.8 --no-binary :all:
RUN pip3 install numpy cython
RUN pip3 install biom-format

WORKDIR /tmp
