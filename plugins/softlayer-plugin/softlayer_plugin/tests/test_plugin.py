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

import shutil
import tempfile
import SoftLayer
from cloudify import state
import mock
import unittest
from os import path

from SoftLayer.API import Client

import softlayer_plugin
from cloudify.exceptions import NonRecoverableError
from cloudify.mocks import MockCloudifyContext
from cloudify.workflows import local
from softlayer_plugin import constants
from softlayer_plugin import extended_vs_manager
from softlayer_plugin import server


class CreateValidationTests(unittest.TestCase):

    def setUp(self):
        self.properties = {}
        self.error_message = ''
        self.node_id = ''
        self.mock_ctx = None

    def _get_required_properties(self):
        properties = {
            constants.API_CONFIG: {},
            constants.DOMAIN: 'test.cloudify.org',
            constants.LOCATION: '168642',
            constants.RAM: 864,
            constants.OS: 4248,
            constants.CPU: 859,
            constants.DISK: 1178,
            constants.ADDITIONAL_IDS: [],
            constants.PORT_SPEED: '',
            constants.PRIVATE_NETWORK_ONLY: False
            }
        return properties

    def test_mutually_exclusive_properties(self):
        self.properties = self._get_required_properties()
        group = [constants.IMAGE_TEMPLATE_ID,
                 constants.IMAGE_TEMPLATE_GLOBAL_ID, constants.OS]
        self.error_message = 'Can only specify one of {0} '.format(group)
        self.node_id = 'test_mutually_exclusive_properties'

        # declare os, image_template_id and image_template_global_id
        self.properties[constants.IMAGE_TEMPLATE_ID] = \
            constants.IMAGE_TEMPLATE_ID
        self.properties[constants.IMAGE_TEMPLATE_GLOBAL_ID] = \
            constants.IMAGE_TEMPLATE_GLOBAL_ID
        self._test_wrong_properties()

        # declare image_template_id and image_template_global_id
        self.properties.pop(constants.OS)
        self.properties[constants.IMAGE_TEMPLATE_ID] = \
            constants.IMAGE_TEMPLATE_ID
        self._test_wrong_properties()

        # declare image_template_id and os
        self.properties.pop(constants.IMAGE_TEMPLATE_GLOBAL_ID)
        self.properties[constants.OS] = 4248
        self._test_wrong_properties()

        # declare os and image_template_global_id
        self.properties.pop(constants.IMAGE_TEMPLATE_ID)
        self.properties[constants.IMAGE_TEMPLATE_GLOBAL_ID] = \
            constants.IMAGE_TEMPLATE_GLOBAL_ID
        self._test_wrong_properties()

    def test_public_vlan_with_private_only(self):
        self.properties = self._get_required_properties()
        self.properties[constants.PRIVATE_NETWORK_ONLY] = True
        self.properties[constants.PUBLIC_VLAN] = 123
        self.error_message = 'Can only specify one of'
        self.node_id = 'test_public_vlan_with_private_only'
        self._test_wrong_properties()

    def _test_wrong_properties_in_create(self):
        try:
            server.create(ctx=self.mock_ctx, softlayer_client=Client(),
                          retry_interval_secs=10)
            self.fail('Expected failure [{0}]'.format(self.error_message))
        except NonRecoverableError as e:
            self.assertIn(self.error_message, e.message)

    def _test_wrong_properties_in_bootstrap(self):
        try:
            server.creation_validation(ctx=self.mock_ctx, softlayer_client='')
            self.fail('Expected failure [{0}]'.format(self.error_message))
        except NonRecoverableError as e:
            self.assertIn(self.error_message, e.message)

    def _test_wrong_properties(self):
        self.mock_ctx = MockCloudifyContext(
            node_id=self.node_id,
            properties=self.properties
        )
        self._test_wrong_properties_in_create()
        self._test_wrong_properties_in_bootstrap()

    def test_missing_domain(self):
        self.properties = self._get_required_properties()
        self.properties.pop('domain')
        self.node_id = 'test_missing_domain'
        self.error_message = 'are required'
        self._test_wrong_properties()

    def test_missing_location(self):
        self.properties = self._get_required_properties()
        self.properties.pop(constants.LOCATION)
        self.node_id = 'test_missing_location'
        self.error_message = 'are required'
        self._test_wrong_properties()

    def test_missing_ram(self):
        self.properties = self._get_required_properties()
        self.properties.pop(constants.RAM)
        self.error_message = 'are required'
        self.node_id = 'test_missing_ram'
        self._test_wrong_properties()

    def test_missing_os(self):
        self.properties = self._get_required_properties()
        self.properties.pop(constants.OS)
        self.error_message = "At least one of ['os', 'image_template_id', " \
                             "'image_template_global_id'] is required"
        self.node_id = 'test_missing_os'
        self._test_wrong_properties()

    def test_missing_cpu(self):
        self.properties = self._get_required_properties()
        self.properties.pop(constants.CPU)
        self.error_message = 'are required'
        self.node_id = 'test_missing_cpu'
        self._test_wrong_properties()

    def test_missing_disk(self):
        self.properties = self._get_required_properties()
        self.properties.pop(constants.DISK)
        self.error_message = 'are required'
        self.node_id = 'test_missing_disk'
        self._test_wrong_properties()


class VSExtendedTests(unittest.TestCase):

    def setUp(self):
        self._price_ids = [1, 2, 3]
        self._expected_price_ids = [
            {"id": 1},
            {"id": 2},
            {"id": 3}
        ]
        self._virtual_guests_options = {
            constants.DOMAIN: 'domain',
            constants.HOSTNAME: 'hostname',
            constants.PUBLIC_VLAN: 12345
        }
        self._expected_virtual_guests_options = {
            constants.HOSTNAME: 'hostname',
            constants.DOMAIN: 'domain',
            "privateNetworkOnlyFlag": False,
            "primaryNetworkComponent":
                {
                    "networkVlan":
                        {
                            "id": 12345
                        }
                }
        }
        self._order = {
            constants.LOCATION: 12345,
            constants.HOSTNAME: 'hostname',
            constants.DOMAIN: 'domain',
            constants.PROVISION_SCRIPTS: ['script'],
            constants.PRIVATE_VLAN: 56789,
            constants.PRIVATE_NETWORK_ONLY: True,
            constants.IMAGE_TEMPLATE_GLOBAL_ID: 'itgi',
            constants.IMAGE_TEMPLATE_ID: 'iti',
            constants.SSH_KEYS: [54321],
            constants.PRICE_IDS: self._price_ids
        }
        self._expected_private_virtual_guests_options = {
            constants.HOSTNAME: "hostname",
            constants.DOMAIN: "domain",
            "privateNetworkOnlyFlag": True,
            "primaryBackendNetworkComponent":
                {
                    "networkVlan":
                        {
                            "id": 56789
                        }
                }
        }
        self._expected_order = {
            'packageId': constants.PACKAGE_ID,
            'location': 12345,
            'prices': self._expected_price_ids,
            'virtualGuests': [self._expected_private_virtual_guests_options],
            'quantity': 1,
            'useHourlyPricing': False,
            'provisionScripts': ['script'],
            'sshKeys': [{'sshKeyIds': [54321]}],
            'imageTemplateGlobalIdentifier': 'itgi',
            'imageTemplateId': 'iti'
        }

    def test_generate_price_ids(self):
        result = extended_vs_manager._generate_prices_ids(
            price_ids=self._price_ids)
        self.assertEqual(self._expected_price_ids, result)

    def test_generate_virtual_guests_options(self):
        result = extended_vs_manager._generate_virtual_guests_options(
            **self._virtual_guests_options)
        self.assertEqual(self._expected_virtual_guests_options, result)

    def test_generate_place_order_options(self):
        result = extended_vs_manager._generate_place_order_options(
            location=12345, hostname='hostname',
            domain='domain', provision_scripts=['script'],
            private_vlan=56789, private_network_only=True,
            image_template_global_id='itgi', image_template_id='iti',
            ssh_keys=[54321], price_ids=self._price_ids)

        self._expected_order = {
            'packageId': constants.PACKAGE_ID,
            'location': 12345,
            'prices': self._expected_price_ids,
            'virtualGuests': [self._expected_private_virtual_guests_options],
            'quantity': 1,
            'useHourlyPricing': False,
            'provisionScripts': ['script'],
            'sshKeys': [{'sshKeyIds': [54321]}],
            'imageTemplateGlobalIdentifier': 'itgi',
            'imageTemplateId': 'iti'
        }
        self.assertEqual(self._expected_order, result)

    def test_calling_client_verify_order(self):
        with mock.patch('SoftLayer.API.Client.call') as fake_call:
            extended_vs_manager.ExtendedVSManager(
                client=Client()).verify_place_order(**self._order)
            fake_call.assert_called_with(
                'Product_Order', 'verifyOrder', self._expected_order)

    def test_calling_client_place_order(self):
        with mock.patch('SoftLayer.API.Client.call') as fake_call:
            vs_manager = extended_vs_manager.ExtendedVSManager(client=Client())
            vs_manager.place_order(**self._order)
            fake_call.assert_called_with(
                'Product_Order', 'placeOrder', self._expected_order)


class HostNameTests(unittest.TestCase):

    @mock.patch.object(state.current_ctx, 'get_ctx')
    def test_generate_hostname(self, mock_get_ctx):
        mock_get_ctx.return_value = MockCloudifyContext()
        long_prefix = 'long_prefix'
        node_id = '__illegal_underscores_very_long_id'
        name = softlayer_plugin.generate_hostname(
            hostname=node_id, prefix=long_prefix)
        self.assertLessEqual(len(name), constants.MAX_HOSTNAME_CHARS)
        prefix = long_prefix[:constants.HOST_PREFIX_LEN].replace('_', '-')
        self.assertEqual(name[:constants.HOST_PREFIX_LEN], prefix)
        id_len = constants.MAX_HOSTNAME_CHARS - constants.HOST_PREFIX_LEN - 1
        expected_id = node_id[-id_len:].replace('_', '-')
        self.assertEqual(name[constants.HOST_PREFIX_LEN:], expected_id)

    @mock.patch.object(state.current_ctx, 'get_ctx')
    def test_missing_prefix_hostname(self, mock_get_ctx):
        mock_get_ctx.return_value = MockCloudifyContext()
        hostname = 'test-id'
        name = softlayer_plugin.generate_hostname(hostname=hostname)
        self.assertEqual(name, hostname)

    @mock.patch.object(state.current_ctx, 'get_ctx')
    def test_already_exist_hostname(self, mock_get_ctx):
        mock_get_ctx.return_value = MockCloudifyContext()
        hostname = 'test-id'
        failure_msg = 'hostname [{0}] already exists'.format(hostname)
        try:
            server._generate_hostname([hostname], hostname='id', prefix='test')
            self.fail('Expected failure: {0}'.failure_msg)
        except NonRecoverableError as e:
            self.assertIn(failure_msg, e.message)


class DecoratorTests(unittest.TestCase):
    @mock.patch.object(state.current_ctx, 'get_ctx')
    def test_put_client_in_kwargs(self, mock_get_ctx):
        properties = {
            'api_config': {
                'username': 'test_username',
                'api_key': 'test_api'
            }
        }
        mock_get_ctx.return_value = MockCloudifyContext(
            node_id='test_put_client_in_kwargs', properties=properties)
        softlayer_plugin.authenticate = lambda x: True
        kwargs = {}
        softlayer_plugin._put_client_in_kwargs(kwargs)
        actual_client = kwargs['softlayer_client']
        expected_client = SoftLayer.API.Client(**properties['api_config'])
        self.assertEqual(expected_client.auth.api_key,
                         actual_client.auth.api_key)
        self.assertEqual(expected_client.auth.username,
                         actual_client.auth.username)

virtual_guest_service = mock.MagicMock()
virtual_guest_service.getPowerState = mock.MagicMock()


def mock_put_client_in_kwargs(kwargs):
    kwargs[constants.SL_CLIENT_NAME] = {
        constants.VIRTUAL_GUEST: virtual_guest_service
    }


def mock_vm_details():
    return {
        constants.HOSTNAME: 'hostname',
        constants.INSTANCE_ID: 'instance_id'
    }


class MockExtendedVSManager():
    def __init__(self, *_):
        pass

    def place_order(self, **_):
        return {
            'orderDetails': {
                'virtualGuests': [
                    {
                        'id': 'mock_id'
                    }
                ]
            }
        }

    def verify_place_order(self, **_):
        pass


class RetryTests(unittest.TestCase):

    def setUp(self):
        self.retry_count = 0
        blueprint_filename = 'simple-blueprint.yaml'
        blueprint_path = path.join(path.dirname(__file__),
                                   'resources',
                                   blueprint_filename)
        plugin_yaml_filename = 'plugin.yaml'
        plugin_yaml_path = path.realpath(
            path.join(path.dirname(softlayer_plugin.__file__),
                      '../{0}'.format(plugin_yaml_filename)))

        self.tempdir = tempfile.mkdtemp(prefix='softlayer-plugin-unit-tests-')

        temp_blueprint_path = path.join(self.tempdir, blueprint_filename)
        temp_plugin_yaml_path = path.join(self.tempdir, plugin_yaml_filename)

        shutil.copyfile(blueprint_path, temp_blueprint_path)
        shutil.copyfile(plugin_yaml_path, temp_plugin_yaml_path)

        self.env = local.init_env(
            temp_blueprint_path,
            name=self._testMethodName,
            ignored_modules=(
                'worker_installer.tasks',
                'plugin_installer.tasks'
            )
        )

    def tearDown(self):
        if path.exists(self.tempdir):
            shutil.rmtree(self.tempdir)

    @mock.patch('softlayer_plugin._put_client_in_kwargs',
                new=mock_put_client_in_kwargs)
    @mock.patch(
        'softlayer_plugin.server._validate_inputs_and_generate_price_ids')
    @mock.patch('softlayer_plugin.server.list_host_names_by_domain')
    @mock.patch('softlayer_plugin.server._create_order_options')
    @mock.patch('softlayer_plugin.server._get_vm_details')
    @mock.patch('softlayer_plugin.server.start')
    @mock.patch('softlayer_plugin.server.ExtendedVSManager')
    def test_lifecycle_create(self, mock_vs, *_):

        def mock_get_active_transaction(*_):
            transaction = dict()
            if self.retry_count == 2:
                transaction[constants.TRANSACTION_STATUS] = {
                    constants.TRANSACTION_FRIENDLY_NAME:
                        'transaction{0}'.format(self.retry_count)
                }
            self.retry_count += 1
            return transaction

        with mock.patch('softlayer_plugin.server.get_active_transaction',
                        new=mock_get_active_transaction):
            self.env.execute('install', task_retries=3)

        self.assertEqual(1, mock_vs.return_value.verify_place_order.call_count)
        self.assertEqual(1, mock_vs.return_value.place_order.call_count)
        self.assertEqual(3, self.retry_count)

    @mock.patch('softlayer_plugin._put_client_in_kwargs',
                new=mock_put_client_in_kwargs)
    @mock.patch('softlayer_plugin.server._get_vm_details', new=mock_vm_details)
    @mock.patch('softlayer_plugin.server.create')
    @mock.patch('softlayer_plugin.server.ExtendedVSManager')
    @mock.patch('softlayer_plugin.server._retrieve_vm_credentials',
                new=lambda x: True)
    def test_lifecycle_start(self, *_):

        def mock_get_active_transaction(*_):
            transaction = dict()
            transaction_name = 'transaction{0}'.format(self.retry_count)
            if self.retry_count < 2:
                transaction['transactionStatus'] = {
                    constants.TRANSACTION_FRIENDLY_NAME: transaction_name
                }
            else:
                virtual_guest_service.getPowerState.return_value = \
                    {constants.POWER_STATE_KEY_NAME: constants.RUNNING_STATE}
            self.retry_count += 1
            return transaction

        with mock.patch('softlayer_plugin.server.get_active_transaction',
                        new=mock_get_active_transaction):
            self.env.execute('install', task_retries=5)

        self.assertEqual(1, virtual_guest_service.getPowerState.call_count)
        self.assertEqual(0, virtual_guest_service.powerOn.call_count)
        self.assertEqual(3, self.retry_count)

    @mock.patch('softlayer_plugin._put_client_in_kwargs',
                new=mock_put_client_in_kwargs)
    @mock.patch('softlayer_plugin.server._get_vm_details', new=mock_vm_details)
    @mock.patch('softlayer_plugin.server.delete')
    @mock.patch('softlayer_plugin.server.ExtendedVSManager')
    @mock.patch('softlayer_plugin.server._retrieve_vm_credentials',
                new=lambda x: True)
    def test_lifecycle_stop(self, *_):

        def mock_get_active_transaction(*_):
            transaction = dict()
            transaction_name = 'transaction{0}'.format(self.retry_count)
            if self.retry_count < 2:
                transaction['transactionStatus'] = {
                    constants.TRANSACTION_FRIENDLY_NAME: transaction_name
                }
            else:
                virtual_guest_service.getPowerState = mock.MagicMock()
                virtual_guest_service.getPowerState.return_value = \
                    {constants.POWER_STATE_KEY_NAME: constants.HALTED_STATE}
            self.retry_count += 1
            return transaction

        with mock.patch('softlayer_plugin.server.get_active_transaction',
                        new=mock_get_active_transaction):
            self.env.execute('uninstall', task_retries=5)

        self.assertEqual(1, virtual_guest_service.getPowerState.call_count)
        self.assertEqual(0, virtual_guest_service.powerOff.call_count)
        self.assertEqual(3, self.retry_count)

    @mock.patch('softlayer_plugin._put_client_in_kwargs',
                new=mock_put_client_in_kwargs)
    @mock.patch('softlayer_plugin.server._create_order_options')
    @mock.patch('softlayer_plugin.server.stop')
    @mock.patch('softlayer_plugin.server._get_vm_details')
    @mock.patch('softlayer_plugin.server.ExtendedVSManager')
    def test_lifecycle_delete(self, mock_vs, *_):

        def mock_get_active_transaction(*_):
            transaction = dict()
            if self.retry_count == 2:
                transaction[constants.TRANSACTION_STATUS] = {
                    constants.TRANSACTION_FRIENDLY_NAME:
                        'transaction{0}'.format(self.retry_count)
                }

            self.retry_count += 1
            return transaction

        with mock.patch('softlayer_plugin.server.get_active_transaction',
                        new=mock_get_active_transaction):
            self.env.execute('uninstall', task_retries=3)

        self.assertEqual(1, mock_vs.return_value.cancel_instance.call_count)
        self.assertEqual(3, self.retry_count)
