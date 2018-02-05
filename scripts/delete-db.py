#!/usr/bin/env python

import os
from cloudify import ctx
from cloudify.state import ctx_parameters as inputs

try:
    import mysql.connector as mariadb
except ImportError:
    import pip
    pip.main(['install', 'mysql-connector-python-rf'])
    import mysql.connector as mariadb


if __name__ == '__main__':

    db_name = inputs.get('db_name')
    db_username = inputs.get('db_user_name')
    db_host = inputs.get('db_host')
    db_password = inputs.get('db_password')
    db = mariadb.connect(
        user=db_username, passwd=db_password, host=db_host, db='mysql')
    cur = db.cursor()
    cur.execute(
        "DROP DATABASE {0}".format(db_name))
    db.close()
