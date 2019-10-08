FROM jenkins/jenkins:lts

MAINTAINER freesky-edward <freesky.edward@gmail.com>

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN /usr/local/bin/install-plugins.sh < /usr/share/jenkins/ref/plugins.txt

EXPOSE 8080 50000
