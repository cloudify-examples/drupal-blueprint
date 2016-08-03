#!/bin/bash

currHostName=`hostname`
currFilename=$(basename "$0")
export hostIP=`hostname -I`
ctx logger info "${currHostName}:${currFilename} in ${hostIP}"

ctx logger info "${currHostName}:${currFilename} id is `id`"
COMMAND="sudo reboot"
ctx logger info "${currHostName}:${currFilename} Running ${COMMAND} in ${hostIP}"
sudo nohup ${COMMAND} > /dev/null 2>&1 &
echo "End of ${currHostName}:${currFilename}"

exit

#cfy executions start -d $dep -w restart_vms -p '{ "node_id" :"apache_vm", "node_instance_id": null}