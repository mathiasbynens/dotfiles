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
    jq \
	sudo

# add dotuser user
RUN adduser dotuser --disabled-password --gecos ""                      && \
    echo "ALL            ALL = (ALL) NOPASSWD: ALL" >> /etc/sudoers && \
    chown -R dotuser:dotuser /home/dotuser

# dotuser user config
USER dotuser
ENV HOME /home/dotuser

WORKDIR $HOME

# If BRANCH not passed, default to 'master'
ARG BRANCH=master

# Using SHA gets past the issue of the git clone being cached and not pulling in most recent commits
ARG SHA=LATEST
RUN SHA=${SHA} \
    git clone -b ${BRANCH} https://github.com/dmorand17/dotfiles.git
