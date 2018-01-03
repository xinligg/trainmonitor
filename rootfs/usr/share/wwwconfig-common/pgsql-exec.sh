#!/bin/sh
# File:		pgsql-exec.sh
# Changes:
#	20010224 Ola Lundqvist <opal@debian.org>
#	20011022 Luca De Vitis <luca@debian.org>
#		Introduced the error variable.
#	        Added the -d flag to $pgsqlcmd (not really needed but clearer)
#	20020116 Ola Lundqvist <opal@debian.org>
#		Documented the error variable.
#	20020125 Ola Lundqvist <opal@debian.org>
#		Added new status code.
#	20020126 Ola Lundqvist <opal@debian.org>
#		Removed need for $dbadmin.
#	20051009 Ola Lundqvist <opal@debian.org>
#		Use dbuser=false on check and then set it to true when exec.
#		Thanks to Christoph Martin <martin@uni-mainz.de>.
# Needs:	$dbname    - the database that user should have access to (optional)
#		$dbserver  - the server to connect to.
#		$dbadmin   - the administrator name.
#		$dbadmpass - the administrator password (not supported).
#		which
#		psql
#		/usr/share/wwwconfig-coomon/pgsql.get
# Description:	Creates or replaces a database user.
# Sets:		$status = {error, exec, execerror}
#		$error = error message (if $status = error)

status=error
error=""

. /usr/share/wwwconfig-common/pgsql.get

use_dbuser=false

if [ -z "$dbserver" ] ; then
    error="No database server specified."
elif [ ! -x $(which pgsql) ] ; then
    error="No pgsql client to execute, install the pgsql client package and
    run 'dpkg-reconfigure -plow packagename'."
elif ! eval $pgsqlcmd $systemdb -c "\"select usename from pg_shadow;\"" >/dev/null 2>&1 ; then
    error="Error when trying to connect to the pgsql database.
    This error can occur if you have no database to connect to, or
    if the password was incorrect.
	use: dpkg-reconfigure -plow packagename to reconfigure."
else
    log="${log}Executing command to pgsql."

    use_dbuser=true

    if eval $pgsqlcmd -d $dbname < $sqlfile > /dev/null 2>&1 ; then
	status=exec
    else
	status=execerror
	error="Unable to run the sql script ($sqlfile)."
    fi
fi
