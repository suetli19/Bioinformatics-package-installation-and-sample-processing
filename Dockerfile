FROM ubuntu:22.04

# also install python version 2 used by bowtie2
RUN apt-get update && \
    DEBIAN_FRONTEND="noninteractive" apt-get install -y python2-dev python2 python-dev-is-python3 python3 python3-dev python3-pip apt-transport-https openjdk-8-jre wget zip git-all zlib1g-dev libbz2-dev liblzma-dev libjpeg-dev
RUN pip3 install boto3 cloudpickle awscli

RUN pip3 install anadama2

RUN apt-get install -y bowtie2
RUN pip3 install numpy
RUN pip3 install cython
RUN pip3 install biom-format

# install cmseq
RUN git clone https://github.com/SegataLab/cmseq.git && \
    cd cmseq && \
    python3 setup.py install && \
    cd ../ && \
    rm -r cmseq

RUN pip3 install metaphlan==4.0.6
RUN metaphlan --install --nproc 24

WORKDIR /tmp

