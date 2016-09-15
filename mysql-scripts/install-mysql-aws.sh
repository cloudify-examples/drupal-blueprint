#!/bin/bash -x

currHostName=`hostname`
currFilename=$(basename "$0")

# A comma separated list of my.cnf section names

# $2 A comma separated list of my.cnf variable names

# $3 A comma separated list of my.cnf values for the above variable names


# args:
# $1 the error code of the last command (should be explicitly passed)
# $2 the message to print in case of an error
# 
# an error message is printed and the script exists with the provided error code
function error_exit {
	echo "$2 : error code: $1"
	exit ${1}
}

function killMySqlProcess {
	sudo service mysql stop
	ps -ef | grep -iE "mysqld" | grep -ivE "diamond|grep|cfy|cloudify"
	if [ $? -eq 0 ] ; then 
		ps -ef | grep -iE "mysqld" | grep -ivE "diamond|grep|cfy|cloudify" | awk '{print $2}' | xargs sudo kill -9
	fi  
}

export PATH=$PATH:/usr/sbin:/sbin:/usr/bin || error_exit $? "Failed on: export PATH=$PATH:/usr/sbin:/sbin"

if sudo grep -q -E '[^!]requiretty' /etc/sudoers; then
    echo "Defaults:`whoami` !requiretty" | sudo tee /etc/sudoers.d/`whoami` >/dev/null
	sudo chmod 0440 /etc/sudoers.d/`whoami`
fi

# The existence of the usingAptGet file in the ext folder will later serve as a flag that "we" are on Ubuntu or Debian or Mint

sudo apt-get -y -q update || error_exit $? "Failed on: sudo apt-get -y update"

killMySqlProcess

# Removing previous mysql installation if exists

sudo apt-get -y -q purge mysql-client* mysql-server* mysql-common*

# The following two statements are used since in some cases, there are leftovers after uninstall
echo "Removing old stuff if exists..."
sudo rm -rf /etc/mysql || error_exit $? "Failed on: sudo rm -rf /etc/mysql"


echo "Using apt-get. Updating apt-get on one of the following : Ubuntu, Debian, Mint" 
sudo DEBIAN_FRONTEND='noninteractive' apt-get -o Dpkg::Options::='--force-confnew' -q -y install mysql-server-core mysql-server mysql-client mysql-common || error_exit $? "Failed on: sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q  mysql-server ... "

echo "Killing old mysql process if exists b4 ending the installation..."
killMySqlProcess

myCnfPath=`sudo find / -name "my.cnf"`
sudo sed -i "s|127.0.0.1|0.0.0.0|g" $myCnfPath
