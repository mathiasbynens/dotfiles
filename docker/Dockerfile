#
#  The purpose of this Dockerfile is to test out my dotuser repository
#
#	rebuild image: docker build -t dotuser-tester:latest --build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S) .
#	run container: docker run -it dotuser-tester /bin/bash

FROM ubuntu:latest

MAINTAINER Doug Morand <dmorand@gmail.com>

RUN apt-get update -y && apt-get install -y \
	curl \
	git \
	vim \
	sudo

# add dotuser user
RUN adduser dotuser --disabled-password --gecos ""                      && \
    echo "ALL            ALL = (ALL) NOPASSWD: ALL" >> /etc/sudoers && \
    chown -R dotuser:dotuser /home/dotuser

# dotuser user config
USER dotuser
ENV HOME /home/dotuser

WORKDIR $HOME

# Hack used to ensure that the git clone isn't cached
ARG CACHE_DATE=2016-01-01

# get dotuser
RUN cd $HOME && \
    git clone https://github.com/dmorand17/dotfiles.git
