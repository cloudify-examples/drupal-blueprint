########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://0www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import os
import uuid

from SoftLayer.exceptions import SoftLayerAPIError

from cosmo_tester.framework.cfy_helper import DEFAULT_EXECUTE_TIMEOUT
from cosmo_tester.framework.testenv import TestCase
from softlayer_plugin import constants
from softlayer_plugin import generate_hostname
from softlayer_plugin.extended_vs_manager import ExtendedVSManager
from system_tests import softlayer_handler as handler

BLUEPRINTS_DIR_NAME = 'resources'
LINUX_BLUEPRINT_YAML = 'linux-blueprint.yaml'
WINDOWS_BLUEPRINT_YAML = 'windows-blueprint.yaml'
WIN_EXECUTE_TIMEOUT = 2400


class InstallTests(TestCase):

    def setUp(self):
        super(InstallTests, self).setUp()
        self.domain = handler.SYSTEM_TESTS_DOMAIN
        self.softlayer_client = self.env.softlayer_client
        self.vs_manager = ExtendedVSManager(self.softlayer_client)

    def _install_uninstall(self, blueprint_name, inputs={},
                           expected_node_properties=None,
                           timeout=DEFAULT_EXECUTE_TIMEOUT):
        resources_dir = os.path.join(os.path.dirname(handler.__file__),
                                     BLUEPRINTS_DIR_NAME)
        self.blueprint_yaml = os.path.join(resources_dir, blueprint_name)
        inputs['domain'] = self.domain
        if 'hostname' not in inputs:
            inputs['hostname'] = 'install'
        hostname_suffix = str(uuid.uuid4())[:3]
        inputs['hostname'] = '{0}{1}'.format(
            inputs['hostname'], hostname_suffix)
        inputs['install_agent'] = True
        self.upload_deploy_and_execute_install(execute_timeout=timeout,
                                               inputs=inputs)
        prefix = self.env.resources_prefix
        hostname = generate_hostname(
            hostname=inputs['hostname'], prefix=prefix)
        instance_id = self._get_instance_id(
            unique_domain=self.domain, hostname=hostname)
        self._assert_instance_properties(instance_id, expected_node_properties)

        self.execute_uninstall()

        self._validate_transactions_begun(instance_id)
        # waiting for instance to be deleted
        self.repetitive(
            func=self._assert_instance_not_exist,
            args={instance_id: instance_id},
            timeout=DEFAULT_EXECUTE_TIMEOUT)

    def test_install_uninstall_linux(self):
        inputs = {
            'hostname': 'linux',
        }
        self._install_uninstall(LINUX_BLUEPRINT_YAML,
                                inputs=inputs)

    def test_install_uninstall_windows(self):
        inputs = {
            'hostname': 'windows',
        }
        self._install_uninstall(blueprint_name=WINDOWS_BLUEPRINT_YAML,
                                inputs=inputs,
                                timeout=WIN_EXECUTE_TIMEOUT)

    def test_private_only_flag(self):
        # when the user set the private only flag,
        # the port speed should be set to a private only one
        inputs = {
            'hostname': 'private',
            'private_network_only': True
        }
        # Private only - the primaryIPaddress property should not be declared.
        # and the port speed should be set to private only
        expected_properties = {
            'public_ip': None,
            'port_speed': constants.DEFAULT_PRIVATE_PORT_SPEED
        }
        self._install_uninstall(blueprint_name=LINUX_BLUEPRINT_YAML,
                                inputs=inputs,
                                expected_node_properties=expected_properties)

    def _get_instance_id(self, unique_domain, hostname):
        instances = self.vs_manager.list_instances(
            domain=unique_domain, hostname=hostname)
        len_instances = len(instances)
        self.assertEqual(len_instances, 1, 'Expected one instance with domain'
                                           ' {0} amd hostname {1} but got {2}'
                         .format(unique_domain, hostname, len_instances))
        return instances[0]['id']

    def _assert_instance_properties(self, instance_id,
                                    expected_properties=None):
        # get tht inputs from the blueprint
        inputs = self.client.deployments.get(self.test_id).inputs
        # expected properties overrides properties in inputs
        if not expected_properties:
            expected_properties = inputs
        else:
            for key, value in expected_properties.items():
                inputs[key] = value
        instance = self.vs_manager.get_instance(instance_id=instance_id)
        # calculate instance properties
        instance_properties = self._get_instance_properties(instance)
        # compare expected properties with instance properties
        for key, expected_value in expected_properties.items():
            if not expected_value:
                # a property with empty default value (e.g. public_vlan)
                # the actual value is unknown in advance so we can't
                # compare it to actual value
                continue
            if key in instance_properties.keys():
                # compare the actual value with the expected one
                actual_value = instance_properties[key]
                self.assertEqual(
                    expected_value, actual_value,
                    'expected {0} = {1} [actual = {2}]'
                    .format(key, expected_value, actual_value))
            # if key doesn't exist in instance_properties,
            # it means that we don't have or can't achieve this information
            # from SoftLayer API, so no comparison in this case...

    def _get_instance_properties(self, instance):
        # calculates properties from properties that exist in SoftLayer API.
        # creates a dict containing keys that are matching the
        # expected keys (the node's properties as they appear in the blueprint)
        # they might be properties that cannot be concluded from SoftLayer API,
        # so no all expected properties will be found in the result dict.
        instance_properties = {}
        public_ip = instance.get(constants.VM_PUBLIC_IP)
        instance_properties[constants.PUBLIC_IP] = public_ip
        private_ip = instance[constants.VM_PRIVATE_IP]
        instance_properties[constants.PRIVATE_IP] = private_ip
        for item in instance['networkVlans']:
            if item['networkSpace'] == 'PRIVATE':
                instance_properties[constants.PRIVATE_VLAN] = item['id']
            if item['networkSpace'] == 'PUBLIC':
                instance_properties[constants.PUBLIC_VLAN] = item['id']

        options_by_group = self._get_create_options_by_category(
            constants.PACKAGE_ID)
        network_components = instance['networkComponents']
        for network_component in network_components:
            primary_ip_address = network_component.get('primaryIpAddress')
            if primary_ip_address and primary_ip_address == private_ip:
                speed = network_component['speed']
                port_speed_list = \
                    options_by_group[constants.PORT_SPEED][str(speed)]
                for item in port_speed_list:
                    description = item['description']
                    item_id = item['item_id']
                    if 'Public' in description:
                        public_port_speed = item_id
                    else:
                        private_port_speed = item_id
                port_speed = \
                    public_port_speed if public_ip else private_port_speed

                instance_properties[constants.PORT_SPEED] = port_speed

        instance_properties['location'] = instance['datacenter']['id']
        instance_properties['cpu'] = \
            instance['billingItem']['orderItem']['itemId']
        instance_properties['domain'] = instance['domain']
        ram_gb = instance['maxMemory']/1000
        ram_group = options_by_group['ram']
        instance_properties['ram'] = \
            ram_group.get(str(ram_gb))[0].get('item_id')
        instance_properties['use_hourly_pricing'] = \
            instance['hourlyBillingFlag']
        description_id = \
            instance['operatingSystem']['softwareLicense'].get(
                'softwareDescriptionId')
        for list_os in options_by_group['os'].values():
            for ops in list_os:
                if ops['softwareDescriptionId'] == description_id:
                    instance_properties['os'] = ops.get('item_id')
                    break
        instance_properties['private_network_only'] \
            = instance['privateNetworkOnlyFlag']
        return instance_properties

    def _get_create_options_by_category(self, package_id):
        # Parses data from the specified package into a dictionary.
        package = self.softlayer_client['Product_Package']
        results = {}
        for category in package.getCategories(id=package_id):
            category_code = category['categoryCode']
            results[category_code] = {}
            for group in category['groups']:
                for price in group['prices']:
                    capacity = price['item'].get('capacity')
                    if capacity:
                        item = {
                            'item_id': price['itemId'],
                            'price_id': price['id'],
                            'description': price['item']['description'],
                            'softwareDescriptionId':
                                price['item']['softwareDescriptionId']
                        }
                        if results[category_code].get(capacity):
                            results[category_code][capacity].append(item)
                        else:
                            results[category_code][capacity] = [item]
        return results

    def _get_active_transaction(self, instance_id):
        return self.softlayer_client[
            constants.VIRTUAL_GUEST].getActiveTransaction(id=instance_id)

    def _validate_transactions_begun(self, instance_id):
        transaction = self._get_active_transaction(instance_id)
        self.assertIsNotNone(transaction)
        self.assertNotEqual(transaction, '')

    def _assert_instance_not_exist(self, instance_id):
        try:
            self.vs_manager.get_instance(instance_id)
            self.fail('instance exists')
        except SoftLayerAPIError as e:
            self.assertEqual(e.faultCode, constants.SL_OBJECT_NOT_FOUND_ERROR)
