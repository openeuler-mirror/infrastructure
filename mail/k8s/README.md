# Deploy mailman on kubernetes.


## Components
1. **Mailman Core**: Basically we use the image directly from [maxking](https://github.com/maxking/docker-mailman) and changed nothing. There is another copied version in dockerfile/core
2. **Mailman Web**: We built another version of mailman web image based from [maxking](https://github.com/maxking/docker-mailman), and the detail can be found in dockerfile/web/dockerfile.overwrite
3. **Postgres**: It's a standard image from `postgres:9.6-alpine`.
4. **Mailman Exim4**: This is an ubuntu 14.04 image with exim4 installed, see [exim4 guide](https://help.ubuntu.com/lts/serverguide/exim4.html) for more information.


## TODOS
1. mailman web https is not enabled, which is required for a production environment.
2. postgres database service should be upgraded into a Huaweicloud database service.
3. all of the domain name should be replaced with the production domain name, now it's `tommylike.me`.
4. EmptyDir volume is used for mailman-web service, this should be upgraded into a persistent volume. since all log file will be generated there.
5. `mailman-core` and `exim4` should be put into the same StatefulSet or use the identical persistent volume, since exim4 will try to recognize mailman receive lists which configured in mailman data folder.
6. Configmap should be upgraded to dynamic reading content from files.
7. static resource(/opt/mailman-web/static) for mailman web now is being served via uwsgi, we need move it into nginx's static folder for production use.
8. MAILMAN_ADMIN_USER & MAILMAN_ADMIN_EMAIL should be replaced, this is the initial admin user when cluster running up.
9. Admin page (/admin login with default Admin user) can be used to maintain the social accounts and this is used for social app login.
10. Mailman web and exim4 both are exposed via NodePort(check the related services) now, this should be upgraded to ClusterIP on huaweicloud.
11. Docker Images should be replaced.
12. Environment variables `HYPERKITTY_API_KEY` and `SECRET_KEY` should be upgraded.
13. `ALLOWED_HOSTS` should be upgraded to reflect the real hosts.