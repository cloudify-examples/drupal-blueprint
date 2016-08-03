#!/bin/bash

currHostName=`hostname`
currFilename=$(basename "$0")

needPhp=$(ctx node properties needPhp)
ctx logger info "${currHostName}:${currFilename} :needPhp ${needPhp}"

needMemcache=$(ctx node properties needMemcache)
ctx logger info "${currHostName}:${currFilename} :needMemcache ${needMemcache}"

dbType=$(ctx node properties dbType)
documentRoot=$(ctx node properties docRoot)
newPort=$(ctx node properties newPort)
ctx logger info "${currHostName}:${currFilename} :documentRoot ${documentRoot}"

# args:
# $1 the error code of the last command (should be explicitly passed)
# $2 the message to print in case of an error
# 
# an error message is printed and the script exists with the provided error code
function error_exit {
	ctx logger info "${currHostName}:${currFilename} $2 : error code: $1"
	exit ${1}
}


function killApacheProcess {
	ps -ef | grep -iE "apache2" | grep -viE "diamond|grep|cfy|cloudify"
	if [ $? -eq 0 ] ; then 
		ps -ef | grep -iE "apache2" | grep -viE "diamond|grep|cfy|cloudify" | awk '{print $2}' | xargs sudo kill -9
	fi  
}


export PATH=$PATH:/usr/sbin:/sbin:/usr/bin || error_exit $? "Failed on: export PATH=$PATH:/usr/sbin:/sbin"


ctx logger info "${currHostName}:${currFilename} apt-get -y -q update..."
sudo apt-get -y -q update || error_exit $? "Failed on: sudo apt-get -y update"

ctx logger info "${currHostName}:${currFilename} apt-get -y -q unzip..."
sudo apt-get -y -q install unzip

#sudo /etc/init.d/apache2 stop
# Just in case the above doesn't work
ctx logger info "${currHostName}:${currFilename} Killing old apache #1 if exists..."
killApacheProcess

if  [ "${needPhp}" == "yesplease" ] ; then
  ctx logger info "${currHostName}:${currFilename} Removing previous php installations if exist ..."
  sudo apt-get --purge -q -y remove php5* php* 
  sudo rm -rf  /etc/php* || error_exit $? "Failed on: sudo rm -rf  /etc/php*"
  sudo rm -rf  /usr/bin/php* || error_exit $? "Failed on: sudo rm -rf  /usr/bin/php"
  sudo rm -rf  /usr/share/php* || error_exit $? "Failed on: sudo rm -rf /usr/share/php"
else  
  ctx logger info "${currHostName}:${currFilename} No need for php"
fi  

sudo rm -rf $documentRoot/*

# Removing previous apache2 installations if exist
ctx logger info "${currHostName}:${currFilename} Removing previous apache2 installations if exist ..."
sudo apt-get -y -q purge apache2.2-common apache2* || error_exit $? "Failed on: sudo apt-get -y -q purge apache2*"

# The following statements are used since in some cases, there are leftovers after uninstall
sudo rm -rf /etc/apache2 || error_exit $? "Failed on: sudo rm -rf /etc/apache2"
sudo rm -rf /usr/sbin/apache2 || error_exit $? "Failed on: sudo rm -rf /usr/sbin/apache2"
sudo rm -rf /usr/lib/apache2 || error_exit $? "Failed on: sudo rm -rf /usr/lib/apache2"
sudo rm -rf /usr/share/apache2 || error_exit $? "Failed on: sudo rm -rf /usr/share/apache2"


ctx logger info "${currHostName}:${currFilename} apt-getting install -y -q apache2 ..."
sudo apt-get install -y -q apache2 || error_exit $? "Failed on: sudo apt-get install -y -q apache2"

#sudo /etc/init.d/apache2 stop
# Just in case the above doesn't work
ctx logger info "${currHostName}:${currFilename} Killing old apache #2 if exists..."
killApacheProcess

if [ "${needPhp}" == "yesplease" ] ; then
  needPhpdb=""
  if  [ "${dbType}" == "mysql" ] ; then
	needPhpdb="php5-mysql"
	ctx logger info "${currHostName}:${currFilename} will install ${needPhpdb} ..."
  else    
	echo "You need to implement code for another database (e.g. : for postgres)"
  fi

  ctx logger info "${currHostName}:${currFilename} apt-getting -y -q install php5 ..."
  sudo apt-get -y -q install php5 libapache2-mod-php5 php5-common php5-curl php5-cli php-pear $needPhpdb php5-gd php5-mcrypt php5-xmlrpc php5-sqlite php-xml-parser
  currStat=$?
  ctx logger info "${currHostName}:${currFilename} :sudo apt-getting -y -q install php5 currStat ${currStat}"
else
  ctx logger info "${currHostName}:${currFilename} Do not install php..."
fi 

if [ "${needMemcache}" == "yesplease" ] ; then
	ctx logger info "${currHostName}:${currFilename} Installing php-memcache (client) ..."
	ctx logger info "${currHostName}:${currFilename} sudo apt-get install php5-memcache ..."
	sudo apt-get install -y -q php5-memcache
	
	ctx logger info "${currHostName}:${currFilename} Installing php-memcached (client) ..."
	ctx logger info "${currHostName}:${currFilename} sudo apt-get install php5-memcached ..."
	sudo apt-get install -y -q php5-memcached
fi	

#php-pdo
#php-mbstring 
#php-xml 
#php-dom 

ctx logger info "${currHostName}:${currFilename} Killing old apache #3 if exist..."
killApacheProcess

ctx logger info "${currHostName}:${currFilename} Chmodding ${documentRoot}..."
sudo chmod -R 777 $documentRoot

origPort=80


apache2Location=`whereis apache2`
for i in ${apache2Location}
do    
	if [ -d "$i" ] ; then
		portsConf="$i/ports.conf"		
		if [ -f "${portsConf}" ] ; then
			ctx logger info "${currHostName}:${currFilename} portsConf is in ${portsConf}"					
			ctx logger info "${currHostName}:${currFilename} Replacing $origPort with $newPort in ${portsConf}..."
			sudo sed -i -e "s/$origPort/$newPort/g" ${portsConf} || error_exit $? "Failed on: sudo sed -i -e $origPort/$newPort in ${portsConf}"			
			ctx logger info "${currHostName}:$0 End of ${portsConf} replacements"

            defaultFile="$i/sites-available/default.conf"
            if [ ! -f "${defaultFile}" ] ; then
			    defaultFile="$i/sites-available/000-default.conf"
			    if [ ! -f "${defaultFile}" ] ; then
			        defaultFile="$i/sites-available/default"
			        if [ ! -f "${defaultFile}" ] ; then
                        defaultFile="$i/sites-available/000-default"
                    fi
			    fi
			fi
			ctx logger info "${currHostName}:${currFilename} defaultFile is ${defaultFile} "
			ctx logger info "${currHostName}:${currFilename} Replacing $origPort with $newPort in ${defaultFile}..."
			sudo sed -i -e "s/$origPort/$newPort/g" ${defaultFile} || error_exit $? "Failed on: sudo sed -i -e $origPort/$newPort in ${defaultFile}"
			ctx logger info "${currHostName}:${currFilename} Replacing AllowOverride None with AllowOverride All in ${defaultFile}..."
			sudo sed -i -e "s/AllowOverride None/AllowOverride All/g" ${defaultFile} || error_exit $? "Failed on: sudo sed -i -e AllowOverride None/AllowOverride All in ${defaultFile}"				
			ctx logger info "${currHostName}:${currFilename} End of ${defaultFile} replacements"			

            apacheConf="$i/apache2.conf"
            if [ -f "${apacheConf}" ] ; then
                ctx logger info "${currHostName}:${currFilename} Replacing AllowOverride None with AllowOverride All in ${apacheConf}..."
			    sudo sed -i -e "s/AllowOverride None/AllowOverride All/g" $apacheConf
			    ctx logger info "${currHostName}:${currFilename} Replacing Require all denied with Require all granted in ${apacheConf}..."
                sudo sed -i -e "s/Require all denied/Require all granted/g" $apacheConf
            else
                ctx logger info "${currHostName}:${currFilename} ${apacheConf} does not exist"
            fi


			ctx logger info "${currHostName}:${currFilename} :sudo a2enmod rewrite"
			sudo a2enmod rewrite
			currStat=$?
			ctx logger info "${currHostName}:${currFilename} :sudo a2enmod rewrite currStat ${currStat}"
			
			ctx logger info "${currHostName}:${currFilename} :sudo a2enmod php5"
			sudo a2enmod php5
			currStat=$?
			ctx logger info "${currHostName}:${currFilename} :sudo a2enmod php5 currStat ${currStat}"
		fi
	fi
done

ctx logger info "${currHostName}:${currFilename} End of ${currFilename}"
echo "End of ${currFilename}"




