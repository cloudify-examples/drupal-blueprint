#!/bin/bash -x

currHostName=`hostname`
currFilename=$(basename "$0")

# args:
# $1 the error code of the last command (should be explicitly passed)
# $2 the message to print in case of an error
# 
# an error message is printed and the script exists with the provided error code
function error_exit {
	echo "$2 : error code: $1"
	exit ${1}
}

export PATH=$PATH:/usr/sbin:/sbin:/usr/bin || error_exit $? "Failed on: export PATH=$PATH:/usr/sbin:/sbin"

pushd ~

dbName=$(ctx source node properties dbName)
ctx logger info "${currHostName}:${currFilename} :Creating db ${dbName} with root..."
queryOutput=`mysqladmin -u root create $dbName`
ctx logger info "${currHostName}:${currFilename} :Created db ${dbName} output is:\r\n${queryOutput}"
      
dbUser=$(ctx source node properties dbUserName)
ctx logger info "${currHostName}:${currFilename} :dbUser is ${dbUser}"

dbPassW=$(ctx source node properties dbUserPassword)

createLocalUser="CREATE USER '${dbUser}'@'localhost' IDENTIFIED BY '${dbPassW}';"
currQuery="mysql -u root ${dbName} -e ${createLocalUser}"
ctx logger info "${currHostName}:${currFilename} :currQuery is: ${currQuery}"
queryOutput=`mysql -u root $dbName -e "${createLocalUser}"`
ctx logger info "${currHostName}:${currFilename} :createLocalUser output is:\r\n${queryOutput}"

createGlobalUser="CREATE USER '${dbUser}'@'%' IDENTIFIED BY '${dbPassW}';"
currQuery="mysql -u root ${dbName} -e ${createGlobalUser}"
ctx logger info "${currHostName}:${currFilename} :currQuery is: ${currQuery}"	
queryOutput=`mysql -u root $dbName -e "${createGlobalUser}"`
ctx logger info "${currHostName}:${currFilename} :createGlobalUser output is:\r\n${queryOutput}"

grantUsageLocalUser="grant usage on *.* to ${dbUser}@localhost identified by '${dbPassW}';"
currQuery="mysql -u root ${dbName} -e ${grantUsageLocalUser}"
ctx logger info "${currHostName}:${currFilename} :currQuery is: ${currQuery}"	
queryOutput=`mysql -u root $dbName -e "${grantUsageLocalUser}"`
ctx logger info "${currHostName}:${currFilename} :grantUsageLocalUser output is:\r\n${queryOutput}"

grantUsageGlobalUser="grant usage on *.* to ${dbUser}@'%' identified by '${dbPassW}';"
currQuery="mysql -u root ${dbName} -e ${grantUsageGlobalUser}"
ctx logger info "${currHostName}:${currFilename} :currQuery is: ${currQuery}"	
queryOutput=`mysql -u root $dbName -e "${grantUsageGlobalUser}"`
ctx logger info "${currHostName}:${currFilename} :grantUsageGlobalUser output is:\r\n${queryOutput}"

grantPrivLocalUser="grant all privileges on *.* to ${dbUser}@'localhost' with grant option;"				
currQuery="mysql -u root ${dbName} -e ${grantPrivLocalUser}"
ctx logger info "${currHostName}:${currFilename} :currQuery is: ${currQuery}"
queryOutput=`mysql -u root $dbName -e "${grantPrivLocalUser}"`
ctx logger info "${currHostName}:${currFilename} :grantPrivLocalUser output is:\r\n${queryOutput}"

grantPrivGlobalUser="grant all privileges on *.* to ${dbUser}@'%' with grant option;"
currQuery="mysql -u root ${dbName} -e ${grantPrivGlobalUser}"
ctx logger info "${currHostName}:${currFilename} :currQuery is: ${currQuery}"
queryOutput=`mysql -u root $dbName -e "${grantPrivGlobalUser}"`
ctx logger info "${currHostName}:${currFilename} :grantPrivGlobalUser output is:\r\n${queryOutput}"

export currSchema=$(ctx target node properties schemaurl)
ctx logger info "${currHostName}:${currFilename} schemaurl of the source node is ${currSchema} ... "

export currLoc=`pwd`
export currZip=currZip.zip
ctx logger info "${currHostName}:${currFilename} :Wgetting ${currSchema} to ${currLoc}/${currZip}..."

wget -O $currZip $currSchema
ctx logger info "${currHostName}:${currFilename} :Wgot ${currSchema} to ${currLoc}/${currZip}"

type unzip
retVal=$?
ctx logger info "${currHostName}:${currFilename} :retVal is ${retVal}..."
if [ $retVal -ne 0 ]; then
  ctx logger info "${currHostName}:${currFilename} :Apt-getting unzip ..."
  sudo apt-get install -y -q unzip
  ctx logger info "${currHostName}:${currFilename} :Apt-got unzip ..."
fi

ctx logger info "${currHostName}:${currFilename} :Unzipping ${currZip} ..."
unzip -o $currZip

ctx logger info "${currHostName}:${currFilename} :Deleting ${currZip} ..."
rm $currZip
currSQL=`ls *.sql`

	
ctx logger info "${currHostName}:${currFilename} :Importing ${currSQL} to ${dbName} with root..."
mysql -u root $dbName < $currSQL

export dbQuery=$(ctx target node properties query)
ctx logger info "${currHostName}:${currFilename} :Running ${dbQuery} on ${dbName} with root..."

queryOutput=`mysql -u root $dbName -e "${dbQuery}"`
ctx logger info "${currHostName}:${currFilename} :Query output is:\r\n${queryOutput}"

popd
ctx logger info "${currHostName}:${currFilename} :End of ${currHostName}:$0"
echo "End of ${currHostName}:$0"
