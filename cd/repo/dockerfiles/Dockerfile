FROM centos:centos7
MAINTAINER tommylike <tommylikehu@gmail.com>

USER root

# Install createrepo
RUN yum -y install createrepo && \
    yum -y install wget

COPY entrypoint.sh /root/entrypoint.sh
RUN chmod +x /root/entrypoint.sh


ENTRYPOINT ["/root/entrypoint.sh"]
