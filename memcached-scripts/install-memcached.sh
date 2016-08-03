#!/bin/bash -x

currHostName=`hostname`
currFilename=$(basename "$0")

# A command separated list of my.cnf section names
currPort=$(ctx node properties port)
ctx logger info "${currHostName}:${currFilename} :curr memcached port ${currPort}"

# args:
# $1 the error code of the last command (should be explicitly passed)
# $2 the message to print in case of an error
# 
# an error message is printed and the script exists with the provided error code
function error_exit {
	echo "$2 : error code: $1"
	exit ${1}
}

function killMemcachdProcess {
	ctx logger info "${currHostName}:${currFilename} sudo service memcached stop..."
	sudo service memcached stop
	ps -ef | grep -iE "memcache" | grep -ivE "diamond|grep|cfy|cloudify|${currFilename}"
	if [ $? -eq 0 ] ; then 
		ctx logger info "${currHostName}:${currFilename} xargs sudo kill -9 memcached..."
		ps -ef | grep -iE "memcache" | grep -ivE "diamond|grep|cfy|cloudify|${currFilename}" | awk '{print $2}' | xargs sudo kill -9
	fi  
}

export PATH=$PATH:/usr/sbin:/sbin:/usr/bin || error_exit $? "Failed on: export PATH=$PATH:/usr/sbin:/sbin"

if sudo grep -q -E '[^!]requiretty' /etc/sudoers; then
	ctx logger info "${currHostName}:${currFilename} Setting requiretty..."
    echo "Defaults:`whoami` !requiretty" | sudo tee /etc/sudoers.d/`whoami` >/dev/null
    ctx logger info "${currHostName}:${currFilename} Chmodding /etc/sudoers.d..."
	sudo chmod 0440 /etc/sudoers.d/`whoami`
fi

# The existence of the usingAptGet file in the ext folder will later serve as a flag that "we" are on Ubuntu or Debian or Mint

ctx logger info "${currHostName}:${currFilename} Invoking apt-get -y -q update ..."
sudo apt-get -y -q update || error_exit $? "Failed on: sudo apt-get -y update"

ctx logger info "${currHostName}:${currFilename} #1 Killing old memcached process if exists..."
killMemcachdProcess

ctx logger info "${currHostName}:${currFilename} Invoking apt-get install -y -q memcached ..."
sudo apt-get install -y -q memcached || error_exit $? "Failed on: sudo apt-get install -y -q memcached"

ctx logger info "${currHostName}:${currFilename} #2 Killing old memcached process if exists..."
killMemcachdProcess

memcachePsEf=`ps -ef | grep -iE "memcache" | grep -ivE "diamond|cfy|cloudify|grep|${currFilename}"`
ctx logger info "${currHostName}:${currFilename} :curr memcached memcachePsEf ${memcachePsEf}"

echo "${currFilename} End of ${currFilename}"
ctx logger info "${currHostName}:${currFilename} End of ${currFilename}"