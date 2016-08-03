#!/bin/bash

currHostName=`hostname`
currFilename=$(basename "$0")

export PATH=$PATH:/usr/sbin:/sbin:/usr/bin

memcachedPort=$(ctx node properties port)
ctx logger info "${currHostName}:${currFilename} :memcached port ${memcachedPort}"

memcachedHost=$(ctx instance host_ip)
ctx logger info "xxx ${currHostName}:${currFilename} :memcached host ${memcachedHost}"

currRequiredmemory=$(ctx node properties requiredmemory)
ctx logger info "${currHostName}:${currFilename} :Setting memory value to ${currRequiredmemory} in /etc/memcached.conf"
sudo sed -i -e "s/64/${currRequiredmemory}/g" /etc/memcached.conf

ctx logger info "${currHostName}:${currFilename} :Configuring the listening host ${memcachedHost} in /etc/memcached.conf"
origIP=127.0.0.1
sudo sed -i -e "s/${origIP}/${memcachedHost}/g" /etc/memcached.conf

memcachePsEf=`ps -ef | grep -iE "memcache" | grep -ivE "diamond|cfy|cloudify|grep|${currFilename}"`
ctx logger info "${currHostName}:${currFilename} :curr memcached memcachePsEf ${memcachePsEf}"

echo "${currHostName}:${currFilename} End of ${currFilename}"
ctx logger info "${currHostName}:${currFilename} End of ${currFilename}"