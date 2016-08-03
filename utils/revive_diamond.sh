#! /bin/bash


host_id=$1
interval=$2
mngr_ip_addr=$3

exit

while true; do
  ps -ef | grep "diamond" | grep configfile | grep -v grep
  if [ $? -ne 0 ]; then
    base_connection="/home/ubuntu/${host_id}/env/local/lib/python2.7/site-packages/pika/adapters/base_connection.py"
    origStr="self.params.host"
    #sudo sed -i -e "s/$origStr/$mngr_ip_addr/g" ${base_connection}
    echo sudo sed -i -e s/$origStr/$mngr_ip_addr/g ${base_connection}
    echo /home/ubuntu/${instance_id}/env/bin/python /home/ubuntu/${host_id}/env/bin/diamond --configfile /home/ubuntu/${host_id}/diamond/etc/diamond.conf
    COMMAND=/home/ubuntu/${instance_id}/env/bin/python /home/ubuntu/${host_id}/env/bin/diamond --configfile /home/ubuntu/${host_id}/diamond/etc/diamond.conf
    nohup ${COMMAND} > /dev/null 2>&1 &
    #exit
  fi
  sleep $2
done


exit


# Replace addresses = socket.getaddrinfo(self.params.host, self.params.port)
# with
# Replace addresses = socket.getaddrinfo('10.67.79.3', self.params.port)
# in base_connection.py


# /home/ubuntu/${instance_id}/env/bin/python /home/ubuntu/${host_id}/env/bin/diamond --configfile /home/ubuntu/${host_id}/diamond/etc/diamond.conf

echo /home/ubuntu/${instance_id}/env/bin/python /home/ubuntu/${host_id}/env/bin/diamond --configfile /home/ubuntu/${host_id}/diamond/etc/diamond.conf
