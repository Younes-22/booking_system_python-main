#!/bin/sh
# Wait until MySQL is ready
while ! mysqladmin ping -h"$1" -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" --silent; do
    sleep 1
done
shift
exec "$@"