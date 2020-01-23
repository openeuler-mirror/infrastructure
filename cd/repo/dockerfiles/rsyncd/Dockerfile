FROM ubuntu:14.04
MAINTAINER tommylikehu@gmail.com

EXPOSE 873

RUN apt-get update && \
    apt-get -y install rsync && \
    apt-get -y install net-tools && \
    apt-get -y install openssh-server

EXPOSE 22
RUN mkdir /var/run/sshd
RUN sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

COPY entrypoint.sh /usr/local/bin/
CMD ["entrypoint.sh"]