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

ctx logger info "xxx ${currHostName}:${currFilename} sudo service mysql start..."
sudo service mysql start || error_exit $? "Failed on: sudo service mysql start"

ps -ef | grep -i mysql | grep -ivE "cfy|cloudify|grep"

host_id2=$(ctx instance host_id)
host_id3=$(ctx instance runtime_properties host_id)
host_id4=$(ctx _node_instance host_id)
host_id=$(ctx instance _node_instance host_id)
ctx logger info "aaa host_id is ${host_id}"
mngr_ip_addr=`sudo find / -name "*.log" | grep -E "${host_id}/work/${host_id}" | xargs -I file grep -E "Connecting to.*5672" file | tail -1 | xargs -I file echo file | sed -e "s+\(.*\)\(Connecting to \)\(.*\)\(:5672\)+\3+g"`
ctx logger info "aaa mngr_ip_addr is ${mngr_ip_addr}"

mngr_ip_addr2=`sudo grep MANAGEMENT_IP /etc/default/celeryd-${host_id} | awk -F"=" '{ print $2 }'`
ctx logger info "aaa mngr_ip_addr2 is ${mngr_ip_addr2}"

ctx logger info "aaa MANAGEMENT_IP is ${MANAGEMENT_IP}"