FROM ubuntu:14.04
MAINTAINER tommylikehu@gmail.com

EXPOSE 873

# install required packages
RUN apt-get update && \
    apt-get -y install rsync && \
    apt-get -y install net-tools && \
    apt-get -y install createrepo && \
    apt-get -y install vim && \
    apt-get -y install openssh-server

EXPOSE 22
RUN mkdir /var/run/sshd
RUN sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

#Update apt sources
RUN source_file=/etc/apt/sources.list \
    && echo "deb http://mirrors.aliyun.com/ubuntu/ trusty main restricted universe multiverse" > ${source_file} \
    && echo "deb http://mirrors.aliyun.com/ubuntu/ trusty-security main restricted universe multiverse" >> ${source_file} \
    && echo "deb http://mirrors.aliyun.com/ubuntu/ trusty-updates main restricted universe multiverse" >> ${source_file} \
    && echo "deb http://mirrors.aliyun.com/ubuntu/ trusty-proposed main restricted universe multiverse" >> ${source_file} \
    && echo "deb http://mirrors.aliyun.com/ubuntu/ trusty-backports main restricted universe multiverse" >> ${source_file} \
    && echo "deb-src http://mirrors.aliyun.com/ubuntu/ trusty main restricted universe multiverse" >> ${source_file} \
    && echo "deb-src http://mirrors.aliyun.com/ubuntu/ trusty-security main restricted universe multiverse" >> ${source_file} \
    && echo "deb-src http://mirrors.aliyun.com/ubuntu/ trusty-updates main restricted universe multiverse" >> ${source_file} \
    && echo "deb-src http://mirrors.aliyun.com/ubuntu/ trusty-proposed main restricted universe multiverse" >> ${source_file} \
    && echo "deb-src http://mirrors.aliyun.com/ubuntu/ trusty-backports main restricted universe multiverse" >> ${source_file}

COPY entrypoint.sh /usr/local/bin/
CMD ["entrypoint.sh"]