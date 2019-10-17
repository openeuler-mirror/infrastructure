#!/bin/bash

###############################################################################
function prepare_database_setup {

  cd /srv/www/obs/api
  RAILS_ENV=production bin/rails db:migrate:status > /dev/null

  if [[ $? > 0 ]];then
    echo "Initialize MySQL databases (first time only)"
    echo " - reconfiguring /etc/my.cnf"
    perl -p -i -e 's#.*datadir\s*=\s*/var/lib/mysql$#datadir= /srv/obs/MySQL#' /etc/my.cnf
    echo " - installing to new datadir"
    mysql_install_db
    echo " - changing ownership for new datadir"
    chown mysql:mysql -R /srv/obs/MySQL
    echo " - restarting mysql"
    systemctl restart mysql
  do
    logline " - Doing 'rails $cmd'"
    RAILS_ENV=production bin/rails $cmd >> $apidir/log/db_migrate.log
    if [[ $? > 0 ]];then
      (>&2 echo "Command $cmd FAILED")
      exit 1
    echo " - setting new password for user root in mysql"
    mysqladmin -u root password "opensuse"
    if [[ $? > 0 ]];then
      echo "ERROR: Your mysql setup doesn't fit your rails setup"
      echo "Please check your database settings for mysql and rails"
      exit 1
    fi
    RUN_INITIAL_SETUP="true"
  fi

  RAKE_COMMANDS=""

  if [ -n "$RUN_INITIAL_SETUP" ]; then
    logline "Initialize OBS api database (first time only)"
    cd $apidir
    RAKE_COMMANDS="db:create db:setup writeconfiguration"
  else
    logline "Migrate OBS api database"
    cd $apidir
    RAKE_COMMANDS="db:migrate:with_data"
    echo
  fi

  logline "Setting ownership of '$backenddir' obsrun"
  chown obsrun.obsrun $backenddir

  logline "Setting up rails environment"
  for cmd in $RAKE_COMMANDS
  do
    logline " - Doing 'rails $cmd'"
    RAILS_ENV=production bin/rails $cmd >> $apidir/log/db_migrate.log
    if [[ $? > 0 ]];then
      (>&2 echo "Command $cmd FAILED")
      exit 1
    fi
  done

  if [ -n "$RUN_INITIAL_SETUP" ]; then
    if [[ ! "$SETUP_ONLY" ]];then
      `systemctl restart obsscheduler.service`
    fi
  fi
}