# Exim4 Dockerfile
This dockerfile used to create the exim4 image used for mail list system, as a reminder all of
the related exim4 config files(25_mm3_macros/55_mm3_transport/455_mm3_router/etc) are been added via
a configmap when initialize the deployments, therefore it's not presence in dockerfile.