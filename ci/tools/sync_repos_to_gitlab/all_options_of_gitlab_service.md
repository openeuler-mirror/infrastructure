# Below is the complete list of available options that can be used to customize your gitlab installation.

DEBUG<br>
Set this to true to enable entrypoint debugging.

TZ<br>
Set the container timezone. Defaults to UTC. Values are expected to be in Canonical format. Example: Europe/Amsterdam See the list of acceptable values. For configuring the timezone of gitlab see variable GITLAB_TIMEZONE.

GITLAB_HOST<br>
The hostname of the GitLab server. Defaults to localhost

GITLAB_CI_HOST<br>
If you are migrating from GitLab CI use this parameter to configure the redirection to the GitLab service so that your existing runners continue to work without any changes. No defaults.

GITLAB_PORT<br>
The port of the GitLab server. This value indicates the public port on which the GitLab application will be accessible on the network and appropriately configures GitLab to generate the correct urls. It does not affect the port on which the internal nginx server will be listening on. Defaults to 443 if GITLAB_HTTPS=true, else defaults to 80.

GITLAB_SECRETS_DB_KEY_BASE<br>
Encryption key for GitLab CI secret variables, as well as import credentials, in the database. Ensure that your key is at least 32 characters long and that you don't lose it. You can generate one using pwgen -Bsv1 64. If you are migrating from GitLab CI, you need to set this value to the value of GITLAB_CI_SECRETS_DB_KEY_BASE. No defaults.

GITLAB_SECRETS_SECRET_KEY_BASE<br>
Encryption key for session secrets. Ensure that your key is at least 64 characters long and that you don't lose it. This secret can be rotated with minimal impact - the main effect is that previously-sent password reset emails will no longer work. You can generate one using pwgen -Bsv1 64. No defaults.

GITLAB_SECRETS_OTP_KEY_BASE<br>
Encryption key for OTP related stuff with GitLab. Ensure that your key is at least 64 characters long and that you don't lose it. If you lose or change this secret, 2FA will stop working for all users. You can generate one using pwgen -Bsv1 64. No defaults.

GITLAB_TIMEZONE<br>
Configure the timezone for the gitlab application. This configuration does not effect cron jobs. Defaults to UTC. See the list of acceptable values. For settings the container timezone which will effect cron, see variable TZ

GITLAB_ROOT_PASSWORD<br>
The password for the root user on firstrun. Defaults to 5iveL!fe. GitLab requires this to be at least 8 characters long.

GITLAB_ROOT_EMAIL<br>
The email for the root user on firstrun. Defaults to admin@example.com

GITLAB_EMAIL<br>
The email address for the GitLab server. Defaults to value of SMTP_USER, else defaults to example@example.com.

GITLAB_EMAIL_DISPLAY_NAME<br>
The name displayed in emails sent out by the GitLab mailer. Defaults to GitLab.

GITLAB_EMAIL_REPLY_TO<br>
The reply-to address of emails sent out by GitLab. Defaults to value of GITLAB_EMAIL, else defaults to noreply@example.com.

GITLAB_EMAIL_SUBJECT_SUFFIX<br>
The e-mail subject suffix used in e-mails sent by GitLab. No defaults.

GITLAB_EMAIL_ENABLED<br>
Enable or disable gitlab mailer. Defaults to the SMTP_ENABLED configuration.

GITLAB_EMAIL_SMIME_ENABLE<br>
Enable or disable email S/MIME signing. Defaults is false.

GITLAB_EMAIL_SMIME_KEY_FILE<br>
Specifies the path to a S/MIME private key file in PEM format, unencrypted. Defaults to ``.

GITLAB_EMAIL_SMIME_CERT_FILE<br>
Specifies the path to a S/MIME public certificate key in PEM format. Defaults to ``.

GITLAB_DEFAULT_THEME<br>
Default theme ID, by default 2. (1 - Indigo, 2 - Dark, 3 - Light, 4 - Blue, 5 - Green, 6 - Light Indigo, 7 - Light Blue, 8 - Light Green, 9 - Red, 10 - Light Red)

GITLAB_ISSUE_CLOSING_PATTERN<br>
Issue closing pattern regex. See GitLab's documentation for more detail. Defaults to \b((?:[Cc]los(?:e[sd]?|ing)|\b[Ff]ix(?:e[sd]|ing)?|\b[Rr]esolv(?:e[sd]?|ing)|\b[Ii]mplement(?:s|ed|ing)?)(:?) +(?:(?:issues? +)?%{issue_ref}(?:(?:, *| +and +)?)|([A-Z][A-Z0-9_]+-\d+))+) .

GITLAB_INCOMING_EMAIL_ADDRESS<br>
The incoming email address for reply by email. Defaults to the value of IMAP_USER, else defaults to reply@example.com. Please read the reply by email documentation to currently set this parameter.

GITLAB_INCOMING_EMAIL_ENABLED<br>
Enable or disable gitlab reply by email feature. Defaults to the value of IMAP_ENABLED.

GITLAB_SIGNUP_ENABLED<br>
Enable or disable user signups (first run only). Default is true.

GITLAB_IMPERSONATION_ENABLED<br>
Enable or disable impersonation. Defaults to true.

GITLAB_PROJECTS_LIMIT<br>
Set default projects limit. Defaults to 100.

GITLAB_USERNAME_CHANGE<br>
Enable or disable ability for users to change their username. Defaults to true.

GITLAB_CREATE_GROUP<br>
Enable or disable ability for users to create groups. Defaults to true.

GITLAB_PROJECTS_ISSUES<br>
Set if issues feature should be enabled by default for new projects. Defaults to true.

GITLAB_PROJECTS_MERGE_REQUESTS<br>
Set if merge requests feature should be enabled by default for new projects. Defaults to true.

GITLAB_PROJECTS_WIKI<br>
Set if wiki feature should be enabled by default for new projects. Defaults to true.

GITLAB_PROJECTS_SNIPPETS<br>
Set if snippets feature should be enabled by default for new projects. Defaults to false.

GITLAB_PROJECTS_BUILDS<br>
Set if builds feature should be enabled by default for new projects. Defaults to true.

GITLAB_PROJECTS_CONTAINER_REGISTRY<br>
Set if container_registry feature should be enabled by default for new projects. Defaults to true.

GITLAB_SHELL_CUSTOM_HOOKS_DIR<br>
Global custom hooks directory. Defaults to /home/git/gitlab-shell/hooks.

GITLAB_WEBHOOK_TIMEOUT<br>
Sets the timeout for webhooks. Defaults to 10 seconds.

GITLAB_NOTIFY_ON_BROKEN_BUILDS<br>
Enable or disable broken build notification emails. Defaults to true

GITLAB_NOTIFY_PUSHER<br>
Add pusher to recipients list of broken build notification emails. Defaults to false

GITLAB_REPOS_DIR<br>
The git repositories folder in the container. Defaults to /home/git/data/repositories

GITLAB_BACKUP_DIR<br>
The backup folder in the container. Defaults to /home/git/data/backups

GITLAB_BACKUP_DIR_CHOWN<br>
Optionally change ownership of backup files on start-up. Defaults to true

GITLAB_BACKUP_DIR_GROUP<br>
Optionally group backups into a subfolder. Can also be used to place backups in to a subfolder on remote storage. Not used by default.

GITLAB_BUILDS_DIR<br>
The build traces directory. Defaults to /home/git/data/builds

GITLAB_DOWNLOADS_DIR<br>
The repository downloads directory. A temporary zip is created in this directory when users click Download Zip on a project. Defaults to /home/git/data/tmp/downloads.

GITLAB_SHARED_DIR<br>
The directory to store the build artifacts. Defaults to /home/git/data/shared

GITLAB_ARTIFACTS_ENABLED<br>
Enable/Disable GitLab artifacts support. Defaults to true.

GITLAB_ARTIFACTS_DIR<br>
Directory to store the artifacts. Defaults to $GITLAB_SHARED_DIR/artifacts

AWS_ACCESS_KEY_ID<br>
Default AWS access key to be used for object store. Defaults to AWS_ACCESS_KEY_ID

AWS_SECRET_ACCESS_KEY<br>
Default AWS access key to be used for object store. Defaults to AWS_SECRET_ACCESS_KEY

AWS_REGION<br>
AWS Region. Defaults to us-east-1

AWS_HOST<br>
Configure this for an compatible AWS host like minio. Defaults to $AWS_HOST. Defaults to s3.amazon.com

AWS_ENDPOINT<br>
AWS Endpoint like http://127.0.0.1:9000. Defaults to nil

AWS_PATH_STYLE<br>
Changes AWS Path Style to 'host/bucket_name/object' instead of 'bucket_name.host/object'. Defaults to true

AWS_SIGNATURE_VERSION<br>
AWS signature version to use. 2 or 4 are valid options. Digital Ocean Spaces and other providers may need 2. Defaults to 4

GITLAB_OBJECT_STORE_CONNECTION_GOOGLE_PROJECT<br>
Default Google project to use for Object Store.

GITLAB_OBJECT_STORE_CONNECTION_GOOGLE_CLIENT_EMAIL<br>
Default Google service account email to use for Object Store.

GITLAB_OBJECT_STORE_CONNECTION_GOOGLE_JSON_KEY_LOCATION<br>
Default Google key file Defaults to /gcs/key.json

GITLAB_OBJECT_STORE_CONNECTION_PROVIDER<br>
Default object store connection provider. Defaults to AWS

GITLAB_ARTIFACTS_OBJECT_STORE_ENABLED<br>
Enables Object Store for Artifacts that will be remote stored. Defaults to false

GITLAB_ARTIFACTS_OBJECT_STORE_REMOTE_DIRECTORY<br>
Bucket name to store the artifacts. Defaults to artifacts

GITLAB_ARTIFACTS_OBJECT_STORE_DIRECT_UPLOAD<br>
Set to true to enable direct upload of Artifacts without the need of local shared storage. Defaults to false

GITLAB_ARTIFACTS_OBJECT_STORE_BACKGROUND_UPLOAD<br>
Temporary option to limit automatic upload. Defaults to false

GITLAB_ARTIFACTS_OBJECT_STORE_PROXY_DOWNLOAD<br>
Passthrough all downloads via GitLab instead of using Redirects to Object Storage. Defaults to false

GITLAB_ARTIFACTS_OBJECT_STORE_CONNECTION_PROVIDER<br>
Connection Provider for the Object Store. (AWS or Google) Defaults to $GITLAB_OBJECT_STORE_CONNECTION_PROVIDER (AWS)

GITLAB_ARTIFACTS_OBJECT_STORE_CONNECTION_AWS_ACCESS_KEY_ID<br>
AWS Access Key ID for the Bucket. Defaults to $AWS_ACCESS_KEY_ID

GITLAB_ARTIFACTS_OBJECT_STORE_CONNECTION_AWS_SECRET_ACCESS_KEY<br>
AWS Secret Access Key. Defaults to $AWS_SECRET_ACCESS_KEY

GITLAB_ARTIFACTS_OBJECT_STORE_CONNECTION_AWS_REGION<br>
AWS Region. Defaults to $AWS_REGION

GITLAB_ARTIFACTS_OBJECT_STORE_CONNECTION_AWS_HOST<br>
Configure this for an compatible AWS host like minio. Defaults to $AWS_HOST

GITLAB_ARTIFACTS_OBJECT_STORE_CONNECTION_AWS_ENDPOINT<br>
AWS Endpoint like http://127.0.0.1:9000. Defaults to $AWS_ENDPOINT

GITLAB_ARTIFACTS_OBJECT_STORE_CONNECTION_AWS_PATH_STYLE<br>
Changes AWS Path Style to 'host/bucket_name/object' instead of 'bucket_name.host/object'. Defaults to $AWS_PATH_STYLE

GITLAB_ARTIFACTS_OBJECT_STORE_CONNECTION_AWS_SIGNATURE_VERSION<br>
AWS signature version to use. 2 or 4 are valid options. Digital Ocean Spaces and other providers may need 2. Defaults to $AWS_SIGNATURE_VERSION

GITLAB_ARTIFACTS_OBJECT_STORE_CONNECTION_GOOGLE_PROJECT<br>
Google project. Defaults to $GITLAB_OBJECT_STORE_CONNECTION_GOOGLE_PROJECT

GITLAB_ARTIFACTS_OBJECT_STORE_CONNECTION_GOOGLE_CLIENT_EMAIL<br>
Google service account. Defaults to $GITLAB_OBJECT_STORE_CONNECTION_GOOGLE_CLIENT_EMAIL

GITLAB_ARTIFACTS_OBJECT_STORE_CONNECTION_GOOGLE_JSON_KEY_LOCATION<br>
Default Google key file. Defaults to $GITLAB_OBJECT_STORE_CONNECTION_GOOGLE_JSON_KEY_LOCATION (/gcs/key.json)

GITLAB_PIPELINE_SCHEDULE_WORKER_CRON<br>
Cron notation for the GitLab pipeline schedule worker. Defaults to '19 * * * *'

GITLAB_LFS_ENABLED<br>
Enable/Disable Git LFS support. Defaults to true.

GITLAB_LFS_OBJECTS_DIR<br>
Directory to store the lfs-objects. Defaults to $GITLAB_SHARED_DIR/lfs-objects

GITLAB_LFS_OBJECT_STORE_ENABLED<br>
Enables Object Store for LFS that will be remote stored. Defaults to false

GITLAB_LFS_OBJECT_STORE_REMOTE_DIRECTORY<br>
Bucket name to store the LFS. Defaults to lfs-object

GITLAB_LFS_OBJECT_STORE_BACKGROUND_UPLOAD<br>
Temporary option to limit automatic upload. Defaults to false

GITLAB_LFS_OBJECT_STORE_PROXY_DOWNLOAD<br>
Passthrough all downloads via GitLab instead of using Redirects to Object Storage. Defaults to false

GITLAB_LFS_OBJECT_STORE_CONNECTION_PROVIDER<br>
Connection Provider for the Object Store. (AWS or Google) Defaults to $GITLAB_OBJECT_STORE_CONNECTION_PROVIDER (AWS)

GITLAB_LFS_OBJECT_STORE_CONNECTION_AWS_ACCESS_KEY_ID<br>
AWS Access Key ID for the Bucket. Defaults to AWS_ACCESS_KEY_ID

GITLAB_LFS_OBJECT_STORE_CONNECTION_AWS_SECRET_ACCESS_KEY<br>
AWS Secret Access Key. Defaults to AWS_SECRET_ACCESS_KEY

GITLAB_LFS_OBJECT_STORE_CONNECTION_AWS_REGION<br>
AWS Region. Defaults to $AWS_REGION

GITLAB_LFS_OBJECT_STORE_CONNECTION_AWS_HOST<br>
Configure this for an compatible AWS host like minio. Defaults to $AWS_HOST

GITLAB_LFS_OBJECT_STORE_CONNECTION_AWS_ENDPOINT<br>
AWS Endpoint like http://127.0.0.1:9000. Defaults to $AWS_ENDPOINT

GITLAB_LFS_OBJECT_STORE_CONNECTION_AWS_PATH_STYLE<br>
Changes AWS Path Style to 'host/bucket_name/object' instead of 'bucket_name.host/object'. Defaults to $AWS_PATH_STYLE

GITLAB_LFS_OBJECT_STORE_CONNECTION_AWS_SIGNATURE_VERSION<br>
AWS signature version to use. 2 or 4 are valid options. Digital Ocean Spaces and other providers may need 2. Defaults to $AWS_SIGNATURE_VERSION

GITLAB_LFS_OBJECT_STORE_CONNECTION_GOOGLE_PROJECT<br>
Google project. Defaults to $GITLAB_OBJECT_STORE_CONNECTION_GOOGLE_PROJECT

GITLAB_LFS_OBJECT_STORE_CONNECTION_GOOGLE_CLIENT_EMAIL<br>
Google service account. Defaults to $GITLAB_OBJECT_STORE_CONNECTION_GOOGLE_CLIENT_EMAIL

GITLAB_LFS_OBJECT_STORE_CONNECTION_GOOGLE_JSON_KEY_LOCATION<br>
Default Google key file. Defaults to $GITLAB_OBJECT_STORE_CONNECTION_GOOGLE_JSON_KEY_LOCATION (/gcs/key.json)

GITLAB_PACKAGES_ENABLED<br>
Enable/Disable Pakages support. Defaults to true.

GITLAB_PACKAGES_DIR<br>
Directory to store the packages data. Defaults to $GITLAB_SHARED_DIR/packages

GITLAB_PACKAGES_OBJECT_STORE_ENABLED<br>
Enables Object Store for Packages that will be remote stored. Defaults to false

GITLAB_PACKAGES_OBJECT_STORE_REMOTE_DIRECTORY<br>
Bucket name to store the packages. Defaults to packages

GITLAB_PACKAGES_OBJECT_STORE_DIRECT_UPLOAD<br>
Set to true to enable direct upload of Packages without the need of local shared storage. Defaults to false

GITLAB_PACKAGES_OBJECT_STORE_BACKGROUND_UPLOAD<br>
Temporary option to limit automatic upload. Defaults to false

GITLAB_PACKAGES_OBJECT_STORE_PROXY_DOWNLOAD<br>
Passthrough all downloads via GitLab instead of using Redirects to Object Storage. Defaults to false

GITLAB_PACKAGES_OBJECT_STORE_CONNECTION_PROVIDER<br>
Connection Provider for the Object Store. (AWS or Google) Defaults to $GITLAB_OBJECT_STORE_CONNECTION_PROVIDER (AWS)

GITLAB_PACKAGES_OBJECT_STORE_CONNECTION_AWS_ACCESS_KEY_ID<br>
AWS Access Key ID for the Bucket. Defaults to $AWS_ACCESS_KEY_ID

GITLAB_PACKAGES_OBJECT_STORE_CONNECTION_AWS_SECRET_ACCESS_KEY<br>
AWS Secret Access Key. Defaults to $AWS_SECRET_ACCESS_KEY

GITLAB_PACKAGES_OBJECT_STORE_CONNECTION_AWS_REGION<br>
AWS Region. Defaults to $AWS_REGION

GITLAB_PACKAGES_OBJECT_STORE_CONNECTION_AWS_HOST<br>
Configure this for an compatible AWS host like minio. Defaults to $AWS_HOST

GITLAB_PACKAGES_OBJECT_STORE_CONNECTION_AWS_ENDPOINT<br>
AWS Endpoint like http://127.0.0.1:9000. Defaults to $AWS_ENDPOINT

GITLAB_PACKAGES_OBJECT_STORE_CONNECTION_AWS_PATH_STYLE<br>
Changes AWS Path Style to 'host/bucket_name/object' instead of 'bucket_name.host/object'. Defaults to AWS_PATH_STYLE

GITLAB_PACKAGES_OBJECT_STORE_CONNECTION_GOOGLE_PROJECT<br>
Google project. Defaults to $GITLAB_OBJECT_STORE_CONNECTION_GOOGLE_PROJECT

GITLAB_PACKAGES_OBJECT_STORE_CONNECTION_GOOGLE_CLIENT_EMAIL<br>
Google service account. Defaults to $GITLAB_OBJECT_STORE_CONNECTION_GOOGLE_CLIENT_EMAIL

GITLAB_PACKAGES_OBJECT_STORE_CONNECTION_GOOGLE_JSON_KEY_LOCATION<br>
Default Google key file. Defaults to $GITLAB_OBJECT_STORE_CONNECTION_GOOGLE_JSON_KEY_LOCATION (/gcs/key.json)

GITLAB_TERRAFORM_STATE_ENABLED<br>
Enable/Disable Terraform State support. Defaults to true.

GITLAB_TERRAFORM_STATE_STORAGE_PATH<br>
Directory to store the terraform state data. Defaults to $GITLAB_SHARED_DIR/terraform_state

GITLAB_TERRAFORM_STATE_OBJECT_STORE_ENABLED<br>
Enables Object Store for Terraform state that will be remote stored. Defaults to false

GITLAB_TERRAFORM_STATE_OBJECT_STORE_REMOTE_DIRECTORY<br>
Bucket name to store the Terraform state. Defaults to terraform_state

GITLAB_TERRAFORM_STATE_OBJECT_STORE_CONNECTION_PROVIDER<br>
Connection Provider for the Object Store (AWS or Google). Defaults to $GITLAB_OBJECT_STORE_CONNECTION_PROVIDER (i.e. AWS).

GITLAB_TERRAFORM_STATE_OBJECT_STORE_CONNECTION_AWS_ACCESS_KEY_ID<br>
AWS Access Key ID for the Bucket. Defaults to $AWS_ACCESS_KEY_ID

GITLAB_TERRAFORM_STATE_OBJECT_STORE_CONNECTION_AWS_SECRET_ACCESS_KEY<br>
AWS Secret Access Key. Defaults to $AWS_SECRET_ACCESS_KEY

GITLAB_TERRAFORM_STATE_OBJECT_STORE_CONNECTION_AWS_REGION<br>
AWS Region. Defaults to $AWS_REGION

GITLAB_TERRAFORM_STATE_OBJECT_STORE_CONNECTION_AWS_HOST<br>
Configure this for an compatible AWS host like minio. Defaults to $AWS_HOST

GITLAB_TERRAFORM_STATE_OBJECT_STORE_CONNECTION_AWS_ENDPOINT<br>
AWS Endpoint like http://127.0.0.1:9000. Defaults to $AWS_ENDPOINT

GITLAB_TERRAFORM_STATE_OBJECT_STORE_CONNECTION_AWS_PATH_STYLE<br>
Changes AWS Path Style to 'host/bucket_name/object' instead of 'bucket_name.host/object'. Defaults to AWS_PATH_STYLE

GITLAB_TERRAFORM_STATE_OBJECT_STORE_CONNECTION_GOOGLE_PROJECT<br>
Google project. Defaults to $GITLAB_OBJECT_STORE_CONNECTION_GOOGLE_PROJECT

GITLAB_TERRAFORM_STATE_OBJECT_STORE_CONNECTION_GOOGLE_CLIENT_EMAIL<br>
Google service account. Defaults to $GITLAB_OBJECT_STORE_CONNECTION_GOOGLE_CLIENT_EMAIL

GITLAB_TERRAFORM_STATE_OBJECT_STORE_CONNECTION_GOOGLE_JSON_KEY_LOCATION<br>
Default Google key file. Defaults to $GITLAB_OBJECT_STORE_CONNECTION_GOOGLE_JSON_KEY_LOCATION (/gcs/key.json)

GITLAB_UPLOADS_STORAGE_PATH<br>
The location where uploads objects are stored. Defaults to $GITLAB_SHARED_DIR/public.

GITLAB_UPLOADS_BASE_DIR<br>
Mapping for the GITLAB_UPLOADS_STORAGE_PATH. Defaults to uploads/-/system

GITLAB_UPLOADS_OBJECT_STORE_ENABLED<br>
Enables Object Store for UPLOADS that will be remote stored. Defaults to false

GITLAB_UPLOADS_OBJECT_STORE_REMOTE_DIRECTORY<br>
Bucket name to store the UPLOADS. Defaults to uploads

GITLAB_UPLOADS_OBJECT_STORE_BACKGROUND_UPLOAD<br>
Temporary option to limit automatic upload. Defaults to false

GITLAB_UPLOADS_OBJECT_STORE_PROXY_DOWNLOAD<br>
Passthrough all downloads via GitLab instead of using Redirects to Object Storage. Defaults to false

GITLAB_UPLOADS_OBJECT_STORE_CONNECTION_PROVIDER<br>
Connection Provider for the Object Store. (AWS or Google) Defaults to $GITLAB_OBJECT_STORE_CONNECTION_PROVIDER (AWS)

GITLAB_UPLOADS_OBJECT_STORE_CONNECTION_AWS_ACCESS_KEY_ID<br>
AWS Access Key ID for the Bucket. Defaults to AWS_ACCESS_KEY_ID

GITLAB_UPLOADS_OBJECT_STORE_CONNECTION_AWS_SECRET_ACCESS_KEY<br>
AWS Secret Access Key. Defaults to AWS_SECRET_ACCESS_KEY

GITLAB_UPLOADS_OBJECT_STORE_CONNECTION_AWS_REGION<br>
AWS Region. Defaults to $AWS_REGION

GITLAB_UPLOADS_OBJECT_STORE_CONNECTION_AWS_HOST<br>
Configure this for an compatible AWS host like minio. Defaults to $AWS_HOST

GITLAB_UPLOADS_OBJECT_STORE_CONNECTION_AWS_ENDPOINT<br>
AWS Endpoint like http://127.0.0.1:9000. Defaults to $AWS_ENDPOINT

GITLAB_UPLOADS_OBJECT_STORE_CONNECTION_AWS_PATH_STYLE<br>
Changes AWS Path Style to 'host/bucket_name/object' instead of 'bucket_name.host/object'. Defaults to AWS_PATH_STYLE

GITLAB_UPLOADS_OBJECT_STORE_CONNECTION_GOOGLE_PROJECT<br>
Google project. Defaults to $GITLAB_OBJECT_STORE_CONNECTION_GOOGLE_PROJECT

GITLAB_UPLOADS_OBJECT_STORE_CONNECTION_GOOGLE_CLIENT_EMAIL<br>
Google service account. Defaults to $GITLAB_OBJECT_STORE_CONNECTION_GOOGLE_CLIENT_EMAIL

GITLAB_UPLOADS_OBJECT_STORE_CONNECTION_GOOGLE_JSON_KEY_LOCATION<br>
Default Google key file. Defaults to $GITLAB_OBJECT_STORE_CONNECTION_GOOGLE_JSON_KEY_LOCATION (/gcs/key.json)

GITLAB_MATTERMOST_ENABLED<br>
Enable/Disable GitLab Mattermost for Add Mattermost button. Defaults to false.

GITLAB_MATTERMOST_URL<br>
Sets Mattermost URL. Defaults to https://mattermost.example.com.

GITLAB_BACKUP_SCHEDULE<br>
Setup cron job to automatic backups. Possible values disable, daily, weekly or monthly. Disabled by default

GITLAB_BACKUP_EXPIRY<br>
Configure how long (in seconds) to keep backups before they are deleted. By default when automated backups are disabled backups are kept forever (0 seconds), else the backups expire in 7 days (604800 seconds).

GITLAB_BACKUP_PG_SCHEMA<br>
Specify the PostgreSQL schema for the backups. No defaults, which means that all schemas will be backed up. see #524

GITLAB_BACKUP_ARCHIVE_PERMISSIONS<br>
Sets the permissions of the backup archives. Defaults to 0600. See

GITLAB_BACKUP_TIME<br>
Set a time for the automatic backups in HH:MM format. Defaults to 04:00.

GITLAB_BACKUP_SKIP<br>
Specified sections are skipped by the backups. Defaults to empty, i.e. lfs,uploads. See

GITLAB_SSH_HOST<br>
The ssh host. Defaults to GITLAB_HOST.

GITLAB_SSH_LISTEN_PORT<br>
The ssh port for SSHD to listen on. Defaults to 22

GITLAB_SSH_MAXSTARTUPS<br>
The ssh "MaxStartups" parameter, defaults to 10:30:60.

GITLAB_SSH_PORT<br>
The ssh port number. Defaults to $GITLAB_SSH_LISTEN_PORT.

GITLAB_RELATIVE_URL_ROOT<br>
The relative url of the GitLab server, e.g. /git. No default.

GITLAB_TRUSTED_PROXIES<br>
Add IP address reverse proxy to trusted proxy list, otherwise users will appear signed in from that address. Currently only a single entry is permitted. No defaults.

GITLAB_REGISTRY_ENABLED<br>
Enables the GitLab Container Registry. Defaults to false.

GITLAB_REGISTRY_HOST<br>
Sets the GitLab Registry Host. Defaults to registry.example.com

GITLAB_REGISTRY_PORT<br>
Sets the GitLab Registry Port. Defaults to 443.

GITLAB_REGISTRY_API_URL<br>
Sets the GitLab Registry API URL. Defaults to http://localhost:5000

GITLAB_REGISTRY_KEY_PATH<br>
Sets the GitLab Registry Key Path. Defaults to config/registry.key

GITLAB_REGISTRY_DIR<br>
Directory to store the container images will be shared with registry. Defaults to $GITLAB_SHARED_DIR/registry

GITLAB_REGISTRY_ISSUER<br>
Sets the GitLab Registry Issuer. Defaults to gitlab-issuer.

GITLAB_REGISTRY_GENERATE_INTERNAL_CERTIFICATES<br>
Set to true to generate SSL internal Registry keys. Used to communicate between a Docker Registry and GitLab. It will generate a self-signed certificate key at the location given by $GITLAB_REGISTRY_KEY_PATH, e.g. /certs/registry.key. And will generate the certificate file at the same location, with the same name, but changing the extension from key to crt, e.g. /certs/registry.crt

GITLAB_PAGES_ENABLED<br>
Enables the GitLab Pages. Defaults to false.

GITLAB_PAGES_DOMAIN<br>
Sets the GitLab Pages Domain. Defaults to example.com

GITLAB_PAGES_DIR<br>
Sets GitLab Pages directory where all pages will be stored. Defaults to $GITLAB_SHARED_DIR/pages

GITLAB_PAGES_PORT<br>
Sets GitLab Pages Port that will be used in NGINX. Defaults to 80

GITLAB_PAGES_HTTPS<br>
Sets GitLab Pages to HTTPS and the gitlab-pages-ssl config will be used. Defaults to false

GITLAB_PAGES_ARTIFACTS_SERVER<br>
Set to true to enable pages artifactsserver, enabled by default.

GITLAB_PAGES_ARTIFACTS_SERVER_URL<br>
If GITLAB_PAGES_ARTIFACTS_SERVER is enabled, set to API endpoint for GitLab Pages (e.g. https://example.com/api/v4). No default.

GITLAB_PAGES_EXTERNAL_HTTP<br>
Sets GitLab Pages external http to receive request on an independen port. Disabled by default

GITLAB_PAGES_EXTERNAL_HTTPS<br>
Sets GitLab Pages external https to receive request on an independen port. Disabled by default

GITLAB_PAGES_ACCESS_CONTROL<br>
Set to true to enable access control for pages. Allows access to a Pages site to be controlled based on a user’s membership to that project. Disabled by default.

GITLAB_PAGES_NGINX_PROXY<br>
Disable the nginx proxy for gitlab pages, defaults to true. When set to false this will turn off the nginx proxy to the gitlab pages daemon, used when the user provides their own http load balancer in combination with a gitlab pages custom domain setup.

GITLAB_PAGES_ACCESS_SECRET<br>
Secret Hash, minimal 32 characters, if omitted, it will be auto generated.

GITLAB_PAGES_ACCESS_CONTROL_SERVER<br>
Gitlab instance URI, example: https://gitlab.example.io

GITLAB_PAGES_ACCESS_CLIENT_ID<br>
Client ID from earlier generated OAuth application

GITLAB_PAGES_ACCESS_CLIENT_SECRET<br>
Client Secret from earlier genereated OAuth application

GITLAB_PAGES_ACCESS_REDIRECT_URI<br>
Redirect URI, non existing pages domain to redirect to pages daemon, https://projects.example.io/auth

GITLAB_HTTPS<br>
Set to true to enable https support, disabled by default.

GITALY_CLIENT_PATH<br>
Set default path for gitaly. defaults to /home/git/gitaly

GITALY_TOKEN<br>
Set a gitaly token, blank by default.

GITLAB_MONITORING_UNICORN_SAMPLER_INTERVAL<br>
Time between sampling of unicorn socket metrics, in seconds, defaults to 10

GITLAB_MONITORING_IP_WHITELIST<br>
IP whitelist to access monitoring endpoints, defaults to 0.0.0.0/8

GITLAB_MONITORING_SIDEKIQ_EXPORTER_ENABLED<br>
Set to true to enable the sidekiq exporter, enabled by default.

GITLAB_MONITORING_SIDEKIQ_EXPORTER_ADDRESS<br>
Sidekiq exporter address, defaults to 0.0.0.0

GITLAB_MONITORING_SIDEKIQ_EXPORTER_PORT<br>
Sidekiq exporter port, defaults to 3807

GITLAB_CONTENT_SECURITY_POLICY_ENABLED<br>
Set to true to enable Content Security Policy, enabled by default.

GITLAB_CONTENT_SECURITY_POLICY_REPORT_ONLY<br>
Set to true to set Content-Security-Policy-Report-Only header, disabled by default

GITLAB_CONTENT_SECURITY_POLICY_DIRECTIVES_BASE_URI<br>
The value of the base-uri directive in the Content-Security-Policy header

GITLAB_CONTENT_SECURITY_POLICY_DIRECTIVES_CHILD_SRC<br>
The value of the child-src directive in the Content-Security-Policy header

GITLAB_CONTENT_SECURITY_POLICY_DIRECTIVES_CONNECT_SRC<br>
The value of the connect-src directive in the Content-Security-Policy header. Default to 'self' http://localhost:* ws://localhost:* wss://localhost:*

GITLAB_CONTENT_SECURITY_POLICY_DIRECTIVES_DEFAULT_SRC<br>
The value of the default-src directive in the Content-Security-Policy header. Default to 'self'

GITLAB_CONTENT_SECURITY_POLICY_DIRECTIVES_FONT_SRC<br>
The value of the font-src directive in the Content-Security-Policy header

GITLAB_CONTENT_SECURITY_POLICY_DIRECTIVES_FORM_ACTION<br>
The value of the form-action directive in the Content-Security-Policy header

GITLAB_CONTENT_SECURITY_POLICY_DIRECTIVES_FRAME_ANCESTORS<br>
The value of the frame-ancestors directive in the Content-Security-Policy header. Default to 'self'

GITLAB_CONTENT_SECURITY_POLICY_DIRECTIVES_FRAME_SRC<br>
The value of the frame-src directive in the Content-Security-Policy header. Default to 'self' https://www.google.com/recaptcha/ https://www.recaptcha.net/ https://content.googleapis.com https://content-compute.googleapis.com https://content-cloudbilling.googleapis.com https://content-cloudresourcemanager.googleapis.com

GITLAB_CONTENT_SECURITY_POLICY_DIRECTIVES_IMG_SRC<br>
The value of the img-src directive in the Content-Security-Policy header. Default to * data: blob:

GITLAB_CONTENT_SECURITY_POLICY_DIRECTIVES_MANIFEST_SRC<br>
The value of the manifest-src directive in the Content-Security-Policy header

GITLAB_CONTENT_SECURITY_POLICY_DIRECTIVES_MEDIA_SRC<br>
The value of the media-src directive in the Content-Security-Policy header

GITLAB_CONTENT_SECURITY_POLICY_DIRECTIVES_OBJECT_SRC<br>
The value of the object-src directive in the Content-Security-Policy header. Default to 'none'

GITLAB_CONTENT_SECURITY_POLICY_DIRECTIVES_SCRIPT_SRC<br>
The value of the script-src directive in the Content-Security-Policy header. Default to 'self' 'unsafe-eval' http://localhost:* https://www.google.com/recaptcha/ https://www.recaptcha.net/ https://www.gstatic.com/recaptcha/ https://apis.google.com

GITLAB_CONTENT_SECURITY_POLICY_DIRECTIVES_STYLE_SRC<br>
The value of the style-src directive in the Content-Security-Policy header. Default to 'self' 'unsafe-inline'

GITLAB_CONTENT_SECURITY_POLICY_DIRECTIVES_WORKER_SRC<br>
The value of the worker-src directive in the Content-Security-Policy header. Default to 'self' blob:

GITLAB_CONTENT_SECURITY_POLICY_DIRECTIVES_REPORT_URI<br>
The value of the report-uri directive in the Content-Security-Policy header

SSL_SELF_SIGNED<br>
Set to true when using self signed ssl certificates. false by default.

SSL_CERTIFICATE_PATH<br>
Location of the ssl certificate. Defaults to /home/git/data/certs/gitlab.crt

SSL_KEY_PATH<br>
Location of the ssl private key. Defaults to /home/git/data/certs/gitlab.key

SSL_DHPARAM_PATH<br>
Location of the dhparam file. Defaults to /home/git/data/certs/dhparam.pem

SSL_VERIFY_CLIENT<br>
Enable verification of client certificates using the SSL_CA_CERTIFICATES_PATH file or setting this variable to on. Defaults to off

SSL_CA_CERTIFICATES_PATH<br>
List of SSL certificates to trust. Defaults to /home/git/data/certs/ca.crt.

SSL_REGISTRY_KEY_PATH<br>
Location of the ssl private key for gitlab container registry. Defaults to /home/git/data/certs/registry.key

SSL_REGISTRY_CERT_PATH<br>
Location of the ssl certificate for the gitlab container registry. Defaults to /home/git/data/certs/registry.crt

SSL_PAGES_KEY_PATH<br>
Location of the ssl private key for gitlab pages. Defaults to /home/git/data/certs/pages.key

SSL_PAGES_CERT_PATH<br>
Location of the ssl certificate for the gitlab pages. Defaults to /home/git/data/certs/pages.crt

SSL_CIPHERS<br>
List of supported SSL ciphers: Defaults to ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA:ECDHE-RSA-AES128-SHA:ECDHE-RSA-DES-CBC3-SHA:AES256-GCM-SHA384:AES128-GCM-SHA256:AES256-SHA256:AES128-SHA256:AES256-SHA:AES128-SHA:DES-CBC3-SHA:!aNULL:!eNULL:!EXPORT:!DES:!MD5:!PSK:!RC4

SSL_PROTOCOLS<br>
List of supported SSL protocols: Defaults to TLSv1 TLSv1.1 TLSv1.2 TLSv1.3

SSL_PAGES_CIPHERS<br>
List of supported SSL ciphers for the gitlab pages: Defaults to SSL_CIPHERS

SSL_PAGES_PROTOCOLS<br>
List of supported SSL protocols for the gitlab pages: Defaults to SSL_PROTOCOLS

SSL_REGISTRY_CIPHERS<br>
List of supported SSL ciphers for gitlab container registry: Defaults to SSL_CIPHERS

SSL_REGISTRY_PROTOCOLS<br>
List of supported SSL protocols for gitlab container registry: Defaults to SSL_PROTOCOLS

NGINX_WORKERS<br>
The number of nginx workers to start. Defaults to 1.

NGINX_SERVER_NAMES_HASH_BUCKET_SIZE<br>
Sets the bucket size for the server names hash tables. This is needed when you have long server_names or your an error message from nginx like nginx: [emerg] could not build server_names_hash, you should increase server_names_hash_bucket_size:... It should be only increment by a power of 2. Defaults to 32.

NGINX_HSTS_ENABLED<br>
Advanced configuration option for turning off the HSTS configuration. Applicable only when SSL is in use. Defaults to true. See #138 for use case scenario.

NGINX_HSTS_MAXAGE<br>
Advanced configuration option for setting the HSTS max-age in the gitlab nginx vHost configuration. Applicable only when SSL is in use. Defaults to 31536000.

NGINX_PROXY_BUFFERING<br>
Enable proxy_buffering. Defaults to off.

NGINX_ACCEL_BUFFERING<br>
Enable X-Accel-Buffering header. Default to no

NGINX_X_FORWARDED_PROTO<br>
Advanced configuration option for the proxy_set_header X-Forwarded-Proto setting in the gitlab nginx vHost configuration. Defaults to https when GITLAB_HTTPS is true, else defaults to $scheme.

NGINX_REAL_IP_RECURSIVE<br>
set to on if docker container runs behind a reverse proxy,you may not want the IP address of the proxy to show up as the client address. off by default.

NGINX_REAL_IP_TRUSTED_ADDRESSES<br>
You can have NGINX look for a different address to use by adding your reverse proxy to the NGINX_REAL_IP_TRUSTED_ADDRESSES. Currently only a single entry is permitted. No defaults.

NGINX_CUSTOM_GITLAB_SERVER_CONFIG<br>
Advanced configuration option. You can add custom configuration for nginx as you like (e.g. custom location proxy). This is similar to setting nginx['custom_gitlab_server_config'] to gitlab.rb for gitlab-omnibus. No defaults.

REDIS_HOST<br>
The hostname of the redis server. Defaults to localhost

REDIS_PORT<br>
The connection port of the redis server. Defaults to 6379.

REDIS_DB_NUMBER<br>
The redis database number. Defaults to '0'.

PUMA_WORKERS<br>
The number of puma workers to start. Defaults to 3.

PUMA_TIMEOUT<br>
Sets the timeout of puma worker processes. Defaults to 60 seconds.

PUMA_THREADS_MIN<br>
The number of puma minimum threads. Defaults to 1.

PUMA_THREADS_MAX<br>
The number of puma maximum threads. Defaults to 16.

PUMA_PER_WORKER_MAX_MEMORY_MB<br>
Maximum memory size of per puma worker process. Defaults to 1024.

PUMA_MASTER_MAX_MEMORY_MB<br>
Maximum memory size of puma master process. Defaults to 800.

SIDEKIQ_CONCURRENCY<br>
The number of concurrent sidekiq jobs to run. Defaults to 25

SIDEKIQ_SHUTDOWN_TIMEOUT<br>
Timeout for sidekiq shutdown. Defaults to 4

SIDEKIQ_MEMORY_KILLER_MAX_RSS<br>
Non-zero value enables the SidekiqMemoryKiller. Defaults to 1000000. For additional options refer Configuring the MemoryKiller

GITLAB_SIDEKIQ_LOG_FORMAT<br>
Sidekiq log format that will be used. Defaults to json

DB_ADAPTER<br>
The database type. Currently only postgresql is supported. Over 12.1 postgres force. Possible values: postgresql. Defaults to postgresql.

DB_ENCODING<br>
The database encoding. For DB_ADAPTER values postresql this parameter defaults and utf8 respectively.

DB_HOST<br>
The database server hostname. Defaults to localhost.

DB_PORT<br>
The database server port. Defaults to 5432 for postgresql.

DB_NAME<br>
The database database name. Defaults to gitlabhq_production

DB_USER<br>
The database database user. Defaults to root

DB_PASS<br>
The database database password. Defaults to no password

DB_POOL<br>
The database database connection pool count. Defaults to 10.

DB_PREPARED_STATEMENTS<br>
Whether use database prepared statements. No defaults. But set to false if you want to use with PgBouncer

SMTP_ENABLED<br>
Enable mail delivery via SMTP. Defaults to true if SMTP_USER is defined, else defaults to false.

SMTP_DOMAIN<br>
SMTP domain. Defaults to www.gmail.com

SMTP_HOST<br>
SMTP server host. Defaults to smtp.gmail.com.

SMTP_PORT<br>
SMTP server port. Defaults to 587.

SMTP_USER<br>
SMTP username.

SMTP_PASS<br>
SMTP password.

SMTP_STARTTLS<br>
Enable STARTTLS. Defaults to true.

SMTP_TLS<br>
Enable SSL/TLS. Defaults to false.

SMTP_OPENSSL_VERIFY_MODE<br>
SMTP openssl verification mode. Accepted values are none, peer, client_once and fail_if_no_peer_cert. Defaults to none.

SMTP_AUTHENTICATION<br>
Specify the SMTP authentication method. Defaults to login if SMTP_USER is set.

SMTP_CA_ENABLED<br>
Enable custom CA certificates for SMTP email configuration. Defaults to false.

SMTP_CA_PATH<br>
Specify the ca_path parameter for SMTP email configuration. Defaults to /home/git/data/certs.

SMTP_CA_FILE<br>
Specify the ca_file parameter for SMTP email configuration. Defaults to /home/git/data/certs/ca.crt.

IMAP_ENABLED<br>
Enable mail delivery via IMAP. Defaults to true if IMAP_USER is defined, else defaults to false.

IMAP_HOST<br>
IMAP server host. Defaults to imap.gmail.com.

IMAP_PORT<br>
IMAP server port. Defaults to 993.

IMAP_USER<br>
IMAP username.

IMAP_PASS<br>
IMAP password.

IMAP_SSL<br>
Enable SSL. Defaults to true.

IMAP_STARTTLS<br>
Enable STARTSSL. Defaults to false.

IMAP_MAILBOX<br>
The name of the mailbox where incoming mail will end up. Defaults to inbox.

LDAP_ENABLED<br>
Enable LDAP. Defaults to false

LDAP_LABEL<br>
Label to show on login tab for LDAP server. Defaults to 'LDAP'

LDAP_HOST<br>
LDAP Host

LDAP_PORT<br>
LDAP Port. Defaults to 389

LDAP_UID<br>
LDAP UID. Defaults to sAMAccountName

LDAP_METHOD<br>
LDAP method, Possible values are simple_tls, start_tls and plain. Defaults to plain

LDAP_VERIFY_SSL<br>
LDAP verify ssl certificate for installations that are using LDAP_METHOD: 'simple_tls' or LDAP_METHOD: 'start_tls'. Defaults to true

LDAP_CA_FILE<br>
Specifies the path to a file containing a PEM-format CA certificate. Defaults to ``

LDAP_SSL_VERSION<br>
Specifies the SSL version for OpenSSL to use, if the OpenSSL default is not appropriate. Example: 'TLSv1_1'. Defaults to ``

LDAP_BIND_DN<br>
No default.

LDAP_PASS<br>
LDAP password

LDAP_TIMEOUT<br>
Timeout, in seconds, for LDAP queries. Defaults to 10.

LDAP_ACTIVE_DIRECTORY<br>
Specifies if LDAP server is Active Directory LDAP server. If your LDAP server is not AD, set this to false. Defaults to true,

LDAP_ALLOW_USERNAME_OR_EMAIL_LOGIN<br>
If enabled, GitLab will ignore everything after the first '@' in the LDAP username submitted by the user on login. Defaults to false if LDAP_UID is userPrincipalName, else true.

LDAP_BLOCK_AUTO_CREATED_USERS<br>
Locks down those users until they have been cleared by the admin. Defaults to false.

LDAP_BASE<br>
Base where we can search for users. No default.

LDAP_USER_FILTER<br>
Filter LDAP users. No default.

LDAP_USER_ATTRIBUTE_USERNAME<br>
Attribute fields for the identification of a user. Default to ['uid', 'userid', 'sAMAccountName']

LDAP_USER_ATTRIBUTE_MAIL<br>
Attribute fields for the shown mail address. Default to ['mail', 'email', 'userPrincipalName']

LDAP_USER_ATTRIBUTE_NAME<br>
Attribute field for the used username of a user. Default to cn.

LDAP_USER_ATTRIBUTE_FIRSTNAME<br>
Attribute field for the forename of a user. Default to givenName

LDAP_USER_ATTRIBUTE_LASTNAME<br>
Attribute field for the surname of a user. Default to sn

LDAP_LOWERCASE_USERNAMES<br>
GitLab will lower case the username for the LDAP Server. Defaults to false

LDAP_PREVENT_LDAP_SIGN_IN<br>
Set to true to Disable LDAP web sign in, defaults to false

OAUTH_ENABLED<br>
Enable OAuth support. Defaults to true if any of the support OAuth providers is configured, else defaults to false.

OAUTH_AUTO_SIGN_IN_WITH_PROVIDER<br>
Automatically sign in with a specific OAuth provider without showing GitLab sign-in page. Accepted values are cas3, github, bitbucket, gitlab, google_oauth2, facebook, twitter, saml, crowd, auth0 and azure_oauth2. No default.

OAUTH_ALLOW_SSO<br>
Comma separated list of oauth providers for single sign-on. This allows users to login without having a user account. The account is created automatically when authentication is successful. Accepted values are cas3, github, bitbucket, gitlab, google_oauth2, facebook, twitter, saml, crowd, auth0 and azure_oauth2. No default.

OAUTH_BLOCK_AUTO_CREATED_USERS<br>
Locks down those users until they have been cleared by the admin. Defaults to true.

OAUTH_AUTO_LINK_LDAP_USER<br>
Look up new users in LDAP servers. If a match is found (same uid), automatically link the omniauth identity with the LDAP account. Defaults to false.

OAUTH_AUTO_LINK_SAML_USER<br>
Allow users with existing accounts to login and auto link their account via SAML login, without having to do a manual login first and manually add SAML. Defaults to false.

OAUTH_AUTO_LINK_USER<br>
Allow users with existing accounts to login and auto link their account via the defined Omniauth providers login, without having to do a manual login first and manually connect their chosen provider. Defaults to [].

OAUTH_EXTERNAL_PROVIDERS<br>
Comma separated list if oauth providers to disallow access to internal projects. Users creating accounts via these providers will have access internal projects. Accepted values are cas3, github, bitbucket, gitlab, google_oauth2, facebook, twitter, saml, crowd, auth0 and azure_oauth2. No default.

OAUTH_CAS3_LABEL<br>
The "Sign in with" button label. Defaults to "cas3".

OAUTH_CAS3_SERVER<br>
CAS3 server URL. No defaults.

OAUTH_CAS3_DISABLE_SSL_VERIFICATION<br>
Disable CAS3 SSL verification. Defaults to false.

OAUTH_CAS3_LOGIN_URL<br>
CAS3 login URL. Defaults to /cas/login

OAUTH_CAS3_VALIDATE_URL<br>
CAS3 validation URL. Defaults to /cas/p3/serviceValidate

OAUTH_CAS3_LOGOUT_URL<br>
CAS3 logout URL. Defaults to /cas/logout

OAUTH_GOOGLE_API_KEY<br>
Google App Client ID. No defaults.

OAUTH_GOOGLE_APP_SECRET<br>
Google App Client Secret. No defaults.

OAUTH_GOOGLE_RESTRICT_DOMAIN<br>
List of Google App restricted domains. Value is comma separated list of single quoted groups. Example: 'exemple.com','exemple2.com'. No defaults.

OAUTH_FACEBOOK_API_KEY<br>
Facebook App API key. No defaults.

OAUTH_FACEBOOK_APP_SECRET<br>
Facebook App API secret. No defaults.

OAUTH_TWITTER_API_KEY<br>
Twitter App API key. No defaults.

OAUTH_TWITTER_APP_SECRET<br>
Twitter App API secret. No defaults.

OAUTH_AUTHENTIQ_CLIENT_ID<br>
authentiq Client ID. No defaults.

OAUTH_AUTHENTIQ_CLIENT_SECRET<br>
authentiq Client secret. No defaults.

OAUTH_AUTHENTIQ_SCOPE<br>
Scope of Authentiq Application Defaults to 'aq:name email~rs address aq:push'

OAUTH_AUTHENTIQ_REDIRECT_URI<br>
Callback URL for Authentiq. No defaults.

OAUTH_GITHUB_API_KEY<br>
GitHub App Client ID. No defaults.

OAUTH_GITHUB_APP_SECRET<br>
GitHub App Client secret. No defaults.

OAUTH_GITHUB_URL<br>
Url to the GitHub Enterprise server. Defaults to https://github.com

OAUTH_GITHUB_VERIFY_SSL<br>
Enable SSL verification while communicating with the GitHub server. Defaults to true.

OAUTH_GITLAB_API_KEY<br>
GitLab App Client ID. No defaults.

OAUTH_GITLAB_APP_SECRET<br>
GitLab App Client secret. No defaults.

OAUTH_BITBUCKET_API_KEY<br>
BitBucket App Client ID. No defaults.

OAUTH_BITBUCKET_APP_SECRET<br>
BitBucket App Client secret. No defaults.

OAUTH_BITBUCKET_URL<br>
Bitbucket URL. Defaults: https://bitbucket.org/

OAUTH_SAML_ASSERTION_CONSUMER_SERVICE_URL<br>
The URL at which the SAML assertion should be received. When GITLAB_HTTPS=true, defaults to https://${GITLAB_HOST}/users/auth/saml/callback else defaults to http://${GITLAB_HOST}/users/auth/saml/callback.

OAUTH_SAML_IDP_CERT_FINGERPRINT<br>
The SHA1 fingerprint of the certificate. No Defaults.

OAUTH_SAML_IDP_SSO_TARGET_URL<br>
The URL to which the authentication request should be sent. No defaults.

OAUTH_SAML_ISSUER<br>
The name of your application. When GITLAB_HTTPS=true, defaults to https://${GITLAB_HOST} else defaults to http://${GITLAB_HOST}.

OAUTH_SAML_LABEL<br>
The "Sign in with" button label. Defaults to "Our SAML Provider".

OAUTH_SAML_NAME_IDENTIFIER_FORMAT<br>
Describes the format of the username required by GitLab, Defaults to urn:oasis:names:tc:SAML:2.0:nameid-format:transient

OAUTH_SAML_GROUPS_ATTRIBUTE<br>
Map groups attribute in a SAMLResponse to external groups. No defaults.

OAUTH_SAML_EXTERNAL_GROUPS<br>
List of external groups in a SAMLResponse. Value is comma separated list of single quoted groups. Example: 'group1','group2'. No defaults.

OAUTH_SAML_ATTRIBUTE_STATEMENTS_EMAIL<br>
Map 'email' attribute name in a SAMLResponse to entries in the OmniAuth info hash, No defaults. See GitLab documentation for more details.

OAUTH_SAML_ATTRIBUTE_STATEMENTS_USERNAME<br>
Map 'username' attribute in a SAMLResponse to entries in the OmniAuth info hash, No defaults. See GitLab documentation for more details.

OAUTH_SAML_ATTRIBUTE_STATEMENTS_NAME<br>
Map 'name' attribute in a SAMLResponse to entries in the OmniAuth info hash, No defaults. See GitLab documentation for more details.

OAUTH_SAML_ATTRIBUTE_STATEMENTS_FIRST_NAME<br>
Map 'first_name' attribute in a SAMLResponse to entries in the OmniAuth info hash, No defaults. See GitLab documentation for more details.

OAUTH_SAML_ATTRIBUTE_STATEMENTS_LAST_NAME<br>
Map 'last_name' attribute in a SAMLResponse to entries in the OmniAuth info hash, No defaults. See GitLab documentation for more details.

OAUTH_CROWD_SERVER_URL<br>
Crowd server url. No defaults.

OAUTH_CROWD_APP_NAME<br>
Crowd server application name. No defaults.

OAUTH_CROWD_APP_PASSWORD<br>
Crowd server application password. No defaults.

OAUTH_AUTH0_CLIENT_ID<br>
Auth0 Client ID. No defaults.

OAUTH_AUTH0_CLIENT_SECRET<br>
Auth0 Client secret. No defaults.

OAUTH_AUTH0_DOMAIN<br>
Auth0 Domain. No defaults.

OAUTH_AUTH0_SCOPE<br>
Auth0 Scope. Defaults to openid profile email.

OAUTH_AZURE_API_KEY<br>
Azure Client ID. No defaults.

OAUTH_AZURE_API_SECRET<br>
Azure Client secret. No defaults.

OAUTH_AZURE_TENANT_ID<br>
Azure Tenant ID. No defaults.

OAUTH_AZURE_ACTIVEDIRECTORY_V2_CLIENT_ID<br>
Client ID for oauth provider azure_activedirectory_v2. If not set, corresponding oauth provider configuration will be removed from gitlab.yml during container startup. No defaults.

OAUTH_AZURE_ACTIVEDIRECTORY_V2_CLIENT_SECRET<br>
Client secret for oauth provider azure_activedirectory_v2. If not set, corresponding oauth provider configuration will be removed from gitlab.yml during container startup. No defaults.

OAUTH_AZURE_ACTIVEDIRECTORY_V2_TENANT_ID<br>
Tenant ID for oauth provider azure_activedirectory_v2. If not set, corresponding oauth provider configuration will be removed from gitlab.yml during container startup. No defaults.

OAUTH_AZURE_ACTIVEDIRECTORY_V2_LABEL<br>
Optional label for login button for azure_activedirectory_v2. Defaults to Azure AD v2

OAUTH2_GENERIC_APP_ID<br>
Your OAuth2 App ID. No defaults.

OAUTH2_GENERIC_APP_SECRET<br>
Your OAuth2 App Secret. No defaults.

OAUTH2_GENERIC_CLIENT_SITE<br>
The OAuth2 generic client site. No defaults

OAUTH2_GENERIC_CLIENT_USER_INFO_URL<br>
The OAuth2 generic client user info url. No defaults

OAUTH2_GENERIC_CLIENT_AUTHORIZE_URL<br>
The OAuth2 generic client authorize url. No defaults

OAUTH2_GENERIC_CLIENT_TOKEN_URL<br>
The OAuth2 generic client token url. No defaults

OAUTH2_GENERIC_CLIENT_END_SESSION_ENDPOINT<br>
The OAuth2 generic client end session endpoint. No defaults

OAUTH2_GENERIC_ID_PATH<br>
The OAuth2 generic id path. No defaults

OAUTH2_GENERIC_USER_UID<br><br>
The OAuth2 generic user id path. No defaults

OAUTH2_GENERIC_USER_NAME<br>
The OAuth2 generic user name. No defaults

OAUTH2_GENERIC_USER_EMAIL<br>
The OAuth2 generic user email. No defaults

OAUTH2_GENERIC_NAME<br>
The name of your OAuth2 provider. No defaults

GITLAB_GRAVATAR_ENABLED<br>
Enables gravatar integration. Defaults to true.

GITLAB_GRAVATAR_HTTP_URL<br>
Sets a custom gravatar url. Defaults to http://www.gravatar.com/avatar/%{hash}?s=%{size}&d=identicon. This can be used for Libravatar integration.

GITLAB_GRAVATAR_HTTPS_URL<br>
Same as above, but for https. Defaults to https://secure.gravatar.com/avatar/%{hash}?s=%{size}&d=identicon.

USERMAP_UID<br>
Sets the uid for user git to the specified uid. Defaults to 1000.

USERMAP_GID<br>
Sets the gid for group git to the specified gid. Defaults to USERMAP_UID if defined, else defaults to 1000.

GOOGLE_ANALYTICS_ID<br>
Google Analytics ID. No defaults.

PIWIK_URL<br>
Sets the Piwik URL. No defaults.

PIWIK_SITE_ID<br>
Sets the Piwik site ID. No defaults.

AWS_BACKUPS<br>
Enables automatic uploads to an Amazon S3 instance. Defaults to false.

AWS_BACKUP_REGION<br>
AWS region. No defaults.

AWS_BACKUP_ENDPOINT<br>
AWS endpoint. No defaults.

AWS_BACKUP_ACCESS_KEY_ID<br>
AWS access key id. No defaults.

AWS_BACKUP_SECRET_ACCESS_KEY<br>
AWS secret access key. No defaults.

AWS_BACKUP_BUCKET<br>
AWS bucket for backup uploads. No defaults.

AWS_BACKUP_MULTIPART_CHUNK_SIZE<br>
Enables mulitpart uploads when file size reaches a defined size. See at AWS S3 Docs

AWS_BACKUP_ENCRYPTION<br>
Turns on AWS Server-Side Encryption. Defaults to false. See at AWS S3 Docs

AWS_BACKUP_STORAGE_CLASS<br>
Configure the storage class for the item. Defaults to STANDARD See at AWS S3 Docs

AWS_BACKUP_SIGNATURE_VERSION<br>
Configure the storage signature version. Defaults to 4 See at AWS S3 Docs

GCS_BACKUPS<br>
Enables automatic uploads to an Google Cloud Storage (GCS) instance. Defaults to false.

GCS_BACKUP_ACCESS_KEY_ID<br>
GCS access key id. No defaults

GCS_BACKUP_SECRET_ACCESS_KEY<br>
GCS secret access key. No defaults

GCS_BACKUP_BUCKET<br>
GCS bucket for backup uploads. No defaults

GITLAB_ROBOTS_PATH<br>
Location of custom robots.txt. Uses GitLab's default robots.txt configuration by default. See www.robotstxt.org for examples.

RACK_ATTACK_ENABLED<br>
Enable/disable rack middleware for blocking & throttling abusive requests Defaults to true.

RACK_ATTACK_WHITELIST<br>
Always allow requests from whitelisted host. Defaults to 127.0.0.1

RACK_ATTACK_MAXRETRY<br>
Number of failed auth attempts before which an IP should be banned. Defaults to 10

RACK_ATTACK_FINDTIME<br>
Number of seconds before resetting the per IP auth attempt counter. Defaults to 60.

RACK_ATTACK_BANTIME<br>
Number of seconds an IP should be banned after too many auth attempts. Defaults to 3600.

GITLAB_WORKHORSE_TIMEOUT<br>
Timeout for gitlab workhorse http proxy. Defaults to 5m0s.

SENTRY_ENABLED<br>
Enables Error Reporting and Logging with Sentry. Defaults to false.

SENTRY_DSN<br>
Sentry DSN. No defaults.

SENTRY_CLIENTSIDE_DSN<br>
Sentry clientside DSN. No defaults.

SENTRY_ENVIRONMENT<br>
Sentry environment. Defaults to production.
