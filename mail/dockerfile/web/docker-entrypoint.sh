#! /bin/bash
set -e


function wait_for_postgres () {
	# Check if the default postgres database is up and accepting connections before
	# moving forward.
	# TODO: Use python's psycopg2 module to do this in python instead of
	# installing postgres-client in the image.
	until psql $DEFAULT_URL -c '\l'; do
		>&2 echo "Postgres is unavailable - sleeping"
		sleep 1
	done
	>&2 echo "Postgres is up - continuing"
}

function create_default_database() {
    if [[ "$( psql $DEFAULT_URL -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" )" = '1' ]]; then
        echo "Database already exists, skipping creating"
    else
        echo "creating new database for mailman web"
        psql $DEFAULT_URL -c "CREATE DATABASE $DB_NAME;"
    fi
}

if [[ ! -v SECRET_KEY ]]; then
	echo "SECRET_KEY is not defined. Aborting."
	exit 1
fi

if [[ ! -v DATABASE_URL_PREFIX ]]; then
	echo "DATABASE_URL_PREFIX is not defined. Aborting..."
	exit 1
fi

if [[ ! -v DB_NAME ]]; then
	echo "DB_NAME is not defined. Aborting..."
	exit 1
fi

export DATABASE_URL="$DATABASE_URL_PREFIX/$DB_NAME"
# this is the default database that will exist on a new created Postgres service on huaweicloud.
export DEFAULT_URL="$DATABASE_URL_PREFIX/postgres"

if [[ "$DATABASE_TYPE" = 'postgres' ]]
then
	wait_for_postgres
	create_default_database
else
	echo "Entrypoint.sh only support postgres, please check and update"
	exit 1
fi

# Check if we are in the correct directory before running commands.
if [[ ! $(pwd) == '/opt/mailman-web' ]]; then
	echo "Running in the wrong directory...switching to /opt/mailman-web"
	cd /opt/mailman-web
fi

# Check if the logs directory is setup.
if [[ ! -e /opt/mailman-web-data/logs/mailmanweb.log ]]; then
	echo "Creating log file for mailman web"
	mkdir -p /opt/mailman-web-data/logs/
	touch /opt/mailman-web-data/logs/mailmanweb.log
fi

if [[ ! -e /opt/mailman-web-data/logs/uwsgi.log ]]; then
	echo "Creating log file for uwsgi.."
	touch /opt/mailman-web-data/logs/uwsgi.log
fi

# Check if the settings_local.py file exists, if yes, copy it too.
if [[ -e /opt/mailman-web-data/settings_local.py ]]; then
	echo "Copying settings_local.py ..."
	cp /opt/mailman-web-data/settings_local.py /opt/mailman-web/settings_local.py
	chown mailman:mailman /opt/mailman-web/settings_local.py
else
	echo "settings_local.py not found, it is highly recommended that you provide one"
	echo "Using default configuration to run."
fi

# Collect static for the django installation.
python3 manage.py collectstatic --noinput

# Migrate all the data to the database if this is a new installation, otherwise
# this command will upgrade the database.
python3 manage.py migrate

# If MAILMAN_ADMIN_USER and MAILMAN_ADMIN_EMAIL is defined create a new
# superuser for Django. There is no password setup so it can't login yet unless
# the password is reset.
if [[ -v MAILMAN_ADMIN_USER ]] && [[ -v MAILMAN_ADMIN_EMAIL ]];
then
	echo "Creating admin user $MAILMAN_ADMIN_USER ..."
	python3 manage.py createsuperuser --noinput --username "$MAILMAN_ADMIN_USER"\
		   --email "$MAILMAN_ADMIN_EMAIL" 2> /dev/null || \
		echo "Superuser $MAILMAN_ADMIN_USER already exists"
fi

# If SERVE_FROM_DOMAIN is defined then rename the default `example.com`
# domain to the defined domain.
if [[ -v SERVE_FROM_DOMAIN ]];
then
	echo "Setting $SERVE_FROM_DOMAIN as the default domain ..."
	python3 manage.py shell -c \
	"from django.contrib.sites.models import Site; Site.objects.filter(domain='example.com').update(domain='$SERVE_FROM_DOMAIN', name='$SERVE_FROM_DOMAIN')"
fi

# Create a mailman user with the specific UID and GID and do not create home
# directory for it. Also chown the logs directory to write the files.
chown mailman:mailman /opt/mailman-web-data -R

exec $@
