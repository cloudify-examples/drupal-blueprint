#! /bin/bash

ctx logger info "Retrieving nodes_to_monitor and deployment_id"

instance_id="$(ctx instance id)"
ctx logger info "instance_id = ${instance_id}"
DPLID=$(ctx deployment id)
currVenv=/root/${DPLID}/env
ctx logger info "deployment_id = ${DPLID}, virtual env is ${currVenv}"
pipPath=${currVenv}/bin/pip

ctx logger info "Downloading utils/revive_diamond.sh...."
LOC=$(ctx download-resource utils/revive_diamond.sh)
status_code=$?
ctx logger info "ctx download-resource status code is ${status_code}"
ctx logger info "LOC is ${LOC}"

COMMAND="${LOC} \"${instance_id}\" ${DPLID}"
crontab_file=/tmp/mycron
ctx logger info "Adding ${COMMAND} to ${crontab_file} ..."
echo "*/1 * * * * ${COMMAND}" >> ${crontab_file}
status_code=$?
ctx logger info "echo ${COMMAND} code is ${status_code}"
ctx logger info "Adding the task to the crontab : crontab ${crontab_file} ..."
sudo crontab ${crontab_file}
status_code=$?
ctx logger info "crontab ${crontab_file} status code is ${status_code}"
currCrontab=`sudo crontab -l`
ctx logger info "currCrontab is ${currCrontab}"
ctx logger info "Done adding the task to the crontab - Starting the healing dog"
