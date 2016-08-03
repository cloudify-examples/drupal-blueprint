#!/bin/bash -x

currHostName=`hostname`
currFilename=$(basename "$0")

# A comma separated list of my.cnf section names
sectionNames=$(ctx node properties sectionNames)
ctx logger info "${currHostName}:${currFilename} :sectionNames ${sectionNames}"

# $2 A comma separated list of my.cnf variable names
variableNames=$(ctx node properties variableNames)
ctx logger info "${currHostName}:${currFilename} :variableNames ${variableNames}"

# $3 A comma separated list of my.cnf values for the above variable names
newValues=$(ctx node properties newValues)
ctx logger info "${currHostName}:${currFilename} :newValues ${newValues}"


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
	ctx logger info "${currHostName}:${currFilename} sudo service mysql stop..."
	sudo service mysql stop
	ps -ef | grep -iE "mysqld" | grep -ivE "diamond|grep|cfy|cloudify"
	if [ $? -eq 0 ] ; then 
		ctx logger info "${currHostName}:${currFilename} xargs sudo kill -9 mysql..."
		ps -ef | grep -iE "mysqld" | grep -ivE "diamond|grep|cfy|cloudify" | awk '{print $2}' | xargs sudo kill -9
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

ctx logger info "${currHostName}:${currFilename} #1 Killing old mysql process if exists..."
killMySqlProcess

# Removing previous mysql installation if exists

ctx logger info "${currHostName}:${currFilename} apt-get -y -q purge mysql..."
sudo apt-get -y -q purge mysql-client* mysql-server* mysql-common*

# The following two statements are used since in some cases, there are leftovers after uninstall
echo "Removing old stuff if exists..."
ctx logger info "${currHostName}:${currFilename} Removing old stuff if exists..."
sudo rm -rf /etc/mysql || error_exit $? "Failed on: sudo rm -rf /etc/mysql"


echo "Using apt-get. Updating apt-get on one of the following : Ubuntu, Debian, Mint" 
ctx logger info "${currHostName}:${currFilename} Using apt-get. Updating apt-get on one of the following : Ubuntu, Debian, Mint" 
sudo DEBIAN_FRONTEND='noninteractive' apt-get -o Dpkg::Options::='--force-confnew' -q -y install mysql-server-core mysql-server mysql-client mysql-common || error_exit $? "Failed on: sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q  mysql-server ... "

echo "Killing old mysql process if exists b4 ending the installation..."
ctx logger info "${currHostName}:${currFilename} Killing old mysql process if exists b4 ending the installation..."
killMySqlProcess

sectionNamesLen=`expr length "$sectionNames"`
if [ $sectionNamesLen -gt 0 ] ; then

	myCnfPath=`sudo find / -name "my.cnf"`
	if [ -f "${myCnfPath}" ] ; then
		IFS=, read -a sectionNamesArr <<< "$sectionNames"
		IFS=, read -a variableNamesArr <<< "$variableNames"
		IFS=, read -a newValuesArr <<< "$newValues"
		ctx logger info "${currHostName}:${currFilename} IFS is ${IFS}"
		ctx logger info "${currHostName}:${currFilename} ${sectionNamesArr[@]}"
		ctx logger info "${currHostName}:${currFilename} ${variableNamesArr[@]}"
		ctx logger info "${currHostName}:${currFilename} ${newValuesArr[@]}"

		variableCounter=${#variableNamesArr[@]}

		for (( i=0; i<${variableCounter}; i++ ));
		do
			currSection="\[${sectionNamesArr[$i]}\]"
			currVariable="${variableNamesArr[$i]}"
			currNewValue="${newValuesArr[$i]}"
			currNewLine="${currVariable}=${currNewValue}"
			ctx logger info "${currHostName}:${currFilename} Commenting $currVariable in $myCnfPath ... "
			sudo sed -i -e "s/^$currVariable/#$currVariable/g" $myCnfPath
			
			jointStr="${currSection}\n${currNewLine}"
			ctx logger info "${currHostName}:${currFilename} Setting ${currNewLine} in the ${currSection} section of $myCnfPath ... "
			sudo sed -i -e "s/$currSection/$jointStr/g" $myCnfPath		
		done
	fi
fi

ctx logger info "${currHostName}:${currFilename} End of ${currFilename}"