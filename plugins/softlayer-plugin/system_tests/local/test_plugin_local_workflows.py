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

import os
import time
from softlayer_plugin import constants
from softlayer_plugin import server
from SoftLayer.exceptions import SoftLayerAPIError

from cloudify.mocks import MockCloudifyContext

from softlayer_plugin.constants import \
    HOSTNAME, INSTANCE_ID, SL_USERNAME, SL_API_KEY, \
    HALTED_STATE, RUNNING_STATE
from system_tests.local.softlayer_test_utils import \
    SoftlayerLocalTestUtils, TASK_RETRIES

NODE_NAME = 'test_node'
TIMEOUT = 1200
INTERVAL_SECS = 10


class WrongCredentialsTests(SoftlayerLocalTestUtils):

    def test_wrong_api_key(self):
        try:
            self._set_up(inputs={'api_key': 'not-exist-api-key'})
            self.env.execute('install', task_retries=0)
            self.fail('Failure expected (wrong api key)')
        except RuntimeError as e:
            self.assertIn('Failed validate username and api_key', e.message)

    def test_wrong_username(self):
        try:
            self._set_up(inputs={'username': 'not-exist-username'})
            self.env.execute('install', task_retries=0)
            self.fail('Failure expected (wrong username)')
        except RuntimeError as e:
            self.assertIn('Failed validate username and api_key', e.message)

    def test_username_not_exist(self):
        username_env = os.environ.get(SL_USERNAME)
        try:
            self._set_up(inputs={'username': ''})
            if username_env:
                os.environ.pop(SL_USERNAME)
            self.env.execute('install', task_retries=0)
            self.fail('Failure expected (username does not exist)')
        except RuntimeError as e:
            self.assertIn('username is missing - '
                          'should be declared in blueprint '
                          'or be set in environment variable: {0}'
                          .format(SL_USERNAME), e.message)
        finally:
            if username_env:
                os.environ[SL_USERNAME] = username_env

    def test_api_key_not_exist(self):
        api_key_env = os.environ.get(SL_API_KEY)
        try:
            self._set_up(inputs={'api_key': ''})
            if api_key_env:
                os.environ.pop(SL_API_KEY)
            self.env.execute('install', task_retries=0)
            self.fail('Failure expected (api key does not exist)')
        except RuntimeError as e:
            self.assertIn('api_key is missing - '
                          'should be declared in blueprint '
                          'or be set in environment variable: {0}'
                          .format(SL_API_KEY), e.message)
        finally:
            if api_key_env:
                os.environ[SL_API_KEY] = api_key_env


class WrongInputsTests(SoftlayerLocalTestUtils):

    def test_wrong_item_id_for_group(self):
        inputs = {
            'ram': 859
        }
        self._set_up(inputs)
        try:
            self.env.execute('install', task_retries=0)
            self.fail('Failure expected '
                      '(the given item id does not belong to ram category')
        except RuntimeError as e:
            self.assertIn(
                "item id 859 belongs to category group ['guest_core']",
                e.message)

    def test_private_port_speed_with_public_vlan(self):
        # cannot declare both
        domain = 'private.cloudify.org'
        inputs = {
            'domain': domain,
            'private_network_only': False,
            'port_speed': 497,
            # 100 Mbps Private Network Uplink
            'public_vlan': 486454
            # Public VLAN 862 on fcr01a.hkg02
        }
        self._set_up(inputs)
        try:
            self.env.execute('install', task_retries=0)
            self.fail('Failure expected - '
                      'declared both public VLAN '
                      'and port speed of private only server')
        except RuntimeError as e:
            self.assertIn('A public network VLAN [486454] '
                          'cannot be specified on a server '
                          'that is private network only',
                          e.message)

    def test_private_only_flag_with_public_vlan(self):
        # cannot declare both
        domain = 'private.cloudify.org'
        inputs = {
            'domain': domain,
            'private_network_only': True,
            'public_vlan': 486454
            # Public VLAN 862 on fcr01a.hkg02
        }
        self._set_up(inputs)
        try:
            self.env.execute('install', task_retries=0)
            self.fail('Failure expected - '
                      'declared both public VLAN '
                      'and port speed of private only server')
        except RuntimeError as e:
            self.assertIn("Can only specify one of "
                          "['private_network_only', 'public_vlan']",
                          e.message)

    def test_not_exist_additional_item_id(self):
        inputs = {
            'additional_ids': [123]
        }
        self._set_up(inputs)
        try:
            self.env.execute('install', task_retries=0)
            self.fail('Failure expected (item id does not exist)')
        except RuntimeError as e:
            self.assertIn('additional item id 123 does not exist', e.message)

    def test_not_exist_item_id(self):
        inputs = {
            'port_speed': 123
        }
        self._set_up(inputs)
        try:
            self.env.execute('install', task_retries=0)
            self.fail('Failure expected (item id does not exist)')
        except RuntimeError as e:
            self.assertIn('item id [123] (declared for port_speed) '
                          'does not exist', e.message)


class StartStopTests(SoftlayerLocalTestUtils):

    def setUp(self):
        super(StartStopTests, self).setUp()
        self.ctx = MockCloudifyContext(
            node_id='test_start_stop_operations',
            properties={}
        )

    def _update_ctx(self):
        instance_id = self.get_instance_id()
        instance = self.vs_manager.get_instance(instance_id=instance_id)
        hostname = instance['hostname']
        self.ctx.instance.runtime_properties[
            INSTANCE_ID] = instance_id
        self.ctx.instance.runtime_properties[HOSTNAME] = hostname
        self.instance_id = instance_id

    def _start(self):
        server.start(ctx=self.ctx,
                     softlayer_client=self.softlayer_client,
                     retry_interval_secs=15)

    def _stop(self):
        server.stop(ctx=self.ctx,
                    softlayer_client=self.softlayer_client,
                    retry_interval_secs=15)

    def _validate_state(self, expected_state):
        actual_state = self.softlayer_client['Virtual_Guest'].getPowerState(
            id=self.instance_id)['keyName']
        self.assertEqual(actual_state, expected_state)

    def test_start_stop_operations(self):
        self.env.execute('install', task_retries=TASK_RETRIES)
        self._update_ctx()
        # stop machine
        self._stop()
        self._validate_state(HALTED_STATE)
        # start machine
        self._start()
        self._validate_state(RUNNING_STATE)
        self.env.execute('uninstall', task_retries=TASK_RETRIES)

    def test_try_to_start_already_started_vm(self):
        self.env.execute('install', task_retries=TASK_RETRIES)
        self._update_ctx()
        self._start()
        self.env.execute('uninstall', task_retries=TASK_RETRIES)

    def _remove_vm(self):
        cancel_result = self.vs_manager.cancel_instance(self.instance_id)
        hostname = self.ctx.instance.runtime_properties['hostname']
        self.assertTrue(cancel_result,
                        'failed to cancel instance [hostname: {0}, id: {1}]'
                        .format(hostname, self.instance_id))
        # wait for vm to be deleted
        timeout = time.time() + TIMEOUT
        instances = self.vs_manager.list_instances(hostname=hostname)
        while time.time() < timeout and instances:
            time.sleep(INTERVAL_SECS)
            instances = self.vs_manager.list_instances(hostname=hostname)
        if instances:
            self.fail('waited for {0} seconds but the vm is still up'
                      .format(TIMEOUT))

    def test_try_to_start_not_exist_machine(self):
        self.env.execute('install', task_retries=TASK_RETRIES)
        self._update_ctx()
        self._remove_vm()
        try:
            self._start()
            self.fail('SoftLayerAPIError expected')
        except SoftLayerAPIError as e:
            self.assertEqual(e.faultCode, constants.SL_OBJECT_NOT_FOUND_ERROR)

    def test_try_to_stop_already_stopped_machine(self):
        self.env.execute('install', task_retries=TASK_RETRIES)
        self._update_ctx()
        self._stop()
        self._validate_state(HALTED_STATE)
        self._stop()
        self.env.execute('uninstall', task_retries=TASK_RETRIES)

    def test_try_to_stop_not_exist_vm(self):
        self.env.execute('install', task_retries=TASK_RETRIES)
        self._update_ctx()
        self._remove_vm()
        # the VM is down - try to stop
        try:
            self._stop()
            self.fail('SoftLayerAPIError expected')
        except SoftLayerAPIError as e:
            self.assertEqual(e.faultCode, constants.SL_OBJECT_NOT_FOUND_ERROR)


class HostnameTests(SoftlayerLocalTestUtils):

    def test_hostname_specified(self):
        hostname = 'hostname'
        inputs = {
            'hostname': hostname,
            'install_agent': False
        }
        self._set_up(inputs)
        self.env.execute('install', task_retries=TASK_RETRIES)
        instances = self._vs_manager.list_instances(hostname=self.hostname)
        self.assertEqual(1, len(instances))
        instance = instances[0]
        self.assertEqual(self.domain, instance['domain'])
