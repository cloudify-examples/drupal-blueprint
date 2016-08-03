########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import logging

import os
from os import path

import unittest
import sys
import uuid
from SoftLayer.API import Client
from cloudify.workflows import local
from softlayer_plugin.extended_vs_manager import ExtendedVSManager
from softlayer_plugin.constants import SL_USERNAME, SL_API_KEY

DOMAIN = 'local.cloudify.org'
TASK_RETRIES = 50


def _get_credentials():
    return {
        'username': os.environ.get(SL_USERNAME),
        'api_key': os.environ.get(SL_API_KEY)
    }


class SoftlayerLocalTestUtils(unittest.TestCase):

    def setUp(self):
        super(SoftlayerLocalTestUtils, self).setUp()
        self._client = Client(_get_credentials())
        self._vs_manager = ExtendedVSManager(self.softlayer_client)
        self._domain = DOMAIN
        self.hostname = ''
        self._set_up()

    def _set_up(self, inputs=None):
        if not inputs:
            inputs = {}
        # set logger
        self.logger = logging.getLogger(self._testMethodName)
        self.logger.addHandler(logging.StreamHandler(sys.stdout))
        self.logger.setLevel(logging.INFO)
        # build blueprint path
        blueprint_path = path.join(
            path.dirname(path.dirname(__file__)),
            'resources',
            'linux-blueprint.yaml')

        creds = _get_credentials()
        if 'api_key' not in inputs:
            inputs['api_key'] = creds['api_key']
        if 'username' not in inputs:
            inputs['username'] = creds['username']
        inputs['domain'] = self.domain
        if 'hostname' not in inputs:
            inputs['hostname'] = 'linux'
        hostname_suffix = str(uuid.uuid4())[:3]
        inputs['hostname'] = '{0}{1}'.format(
            inputs['hostname'], hostname_suffix)
        self.hostname = inputs['hostname']
        # setup local workflow execution environment
        self.env = local.init_env(blueprint_path,
                                  name=self._testMethodName,
                                  inputs=inputs,
                                  ignored_modules=['worker_installer.tasks',
                                                   'plugin_installer.tasks'])

    @property
    def softlayer_client(self):
        return self._client

    @property
    def vs_manager(self):
        return self._vs_manager

    @property
    def domain(self):
        return self._domain

    def get_instance_id(self):
        instances = self.vs_manager.list_instances(
            domain=self.domain, hostname=self.hostname)
        self.assertEqual(1, len(instances),
                         'expected one instance with domain {0} '
                         'and hostname {1}'
                         .format(self.domain, self.hostname))
        return instances[0]['id']

    def tearDown(self):
        instances = self.vs_manager.list_instances(domain=self.domain)
        for instance in instances:
            try:
                self.logger.info(
                    'removing instance [id: {0}, hostname: {1}, domain: {2}]'
                    .format(instance['id'],
                            instance['hostname'], instance['domain']))
                self.vs_manager.cancel_instance(instance_id=instance['id'])
            except Exception as e:
                self.logger.info('failed to remove instance {0}: {1}'
                                 .format(instance['hostname'], e.message))
