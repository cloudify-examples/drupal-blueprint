#!/bin/bash

currHostName=`hostname`
currFilename=$(basename "$0")

documentRoot=$(ctx node properties docRoot)
ctx logger info "${currHostName}:${currFilename} :documentRoot ${documentRoot}"

# args:
# $1 the error code of the last command (should be explicitly passed)
# $2 the message to print in case of an error
# 
# an error message is printed and the script exists with the provided error code
function error_exit {
	echo "$2 : error code: $1"
	exit ${1}
}

sitesFolder="${documentRoot}/sites"

ctx logger info "${currHostName}:${currFilename} Invoking drush dl $1 and drush en -y $1..."

pushd $sitesFolder
drush dl $1
drush en -y $1

ctx logger info "${currHostName}:${currFilename} Invoking drush cc all ..."
drush cc all
popd 

ctx logger info "${currHostName}:${currFilename} :End of ${currHostName}:${currFilename}"
echo "End of ${currHostName}:${currFilename}"


exit

export dep=myDeployment
export myTheme=mayo
cfy executions start -d $dep  -w drush_install -p "project_name=${myTheme}"

This is how you invoke it from the drush_setvar workflow from the CFY CLI :

cfy executions start -d $dep  -w drush_setvar -p "variable_name=theme_default;variable_value=${myTheme}"