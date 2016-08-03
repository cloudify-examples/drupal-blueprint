import sys
from influxdb.influxdb08 import InfluxDBClient
from influxdb.influxdb08.client import InfluxDBClientError
import json 
from os import utime
from os import getpid 
from os import path
import time
import datetime


def run_query(input_str):
    influx_client = InfluxDBClient(host='localhost', port=8086, database='cloudify')
    q_string = 'SELECT value FROM /' + '.*' + input_str + '.*' + '/' + ' WHERE  time > now() - 40s'
    try:
        result = influx_client.query(q_string)
        print 'Query result is {0} \n'.format(result)
        if not result:
            print "There are no results {0}".format()
        else:
            print result
    except InfluxDBClientError as ee:
        print 'DBClienterror {0}\n'.format(str(ee))
    except Exception as e:
        print str(e)


def main(argv):
    input_str = argv[1]
    run_query(input_str)

if __name__ == '__main__':
    main(sys.argv)
