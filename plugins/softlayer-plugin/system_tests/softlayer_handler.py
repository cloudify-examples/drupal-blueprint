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

import SoftLayer

from cosmo_tester.framework.handlers import (
    BaseHandler, BaseCloudifyInputsConfigReader)
from softlayer_plugin import constants
from SoftLayer.exceptions import SoftLayerAPIError
from SoftLayer.managers.vs import VSManager

CLOUDIFY_TEST_NO_CLEANUP = 'CLOUDIFY_TEST_NO_CLEANUP'
MANAGER_BLUEPRINT = 'softlayer/softlayer-manager-blueprint.yaml'
SYSTEM_TESTS_DOMAIN = 'cloudify.org'
SYSTEM_TESTS_MANAGER_DOMAIN = 'manager.cloudify.org'

WAIT_FOR_DELETE_TIMEOUT = 300
WAIT_FOR_DELETE_INTERVAL = 10


class SoftLayerCleanupContext(BaseHandler.CleanupContext):

    def cleanup(self):
        super(SoftLayerCleanupContext, self).cleanup()
        resources_to_delete = self.get_resources_to_delete()
        if self.skip_cleanup:
            self.logger.warn('[{0}] SKIPPING cleanup: of the resources: {1}'
                             .format(self.context_name, resources_to_delete))
            return
        self.logger.info('[{0}] Performing cleanup: will try removing these '
                         'resources: {1}'
                         .format(self.context_name, resources_to_delete))

        leftovers = self.env.handler.remove_softlayer_resources(
            resources_to_delete)
        self.logger.info('[{0}] Leftover resources after cleanup: {1}'
                         .format(self.context_name, leftovers))

    def get_resources_to_delete(self):
        domain = SYSTEM_TESTS_DOMAIN
        if self.context_name == 'testenv':
            domain = SYSTEM_TESTS_MANAGER_DOMAIN
        return self.env.handler.list_instances(domain=domain)


class CloudifySoftLayerInputsConfigReader(BaseCloudifyInputsConfigReader):

    def __init__(self, cloudify_config, manager_blueprint_path, **kwargs):
        super(CloudifySoftLayerInputsConfigReader, self).__init__(
            cloudify_config, manager_blueprint_path=manager_blueprint_path,
            **kwargs)

    @property
    def username(self):
        return self.config['username']

    @property
    def api_key(self):
        return self.config['api_key']

    @property
    def endpoint_url(self):
        return self.config['endpoint_url']

    @property
    def management_user_name(self):
        return self.config['agents_user']

    @property
    def management_key_path(self):
        return self.config['ssh_key_filename']


class SoftLayerHandler(BaseHandler):

    manager_blueprint = MANAGER_BLUEPRINT
    CleanupContext = SoftLayerCleanupContext
    CloudifyConfigReader = None
    _softrlayer_client = None

    def __init__(self, env):
        super(SoftLayerHandler, self).__init__(env)
        self.CloudifyConfigReader = CloudifySoftLayerInputsConfigReader

    def _client_creds(self):
        return {
            'username': self.env.username,
            'api_key': self.env.api_key,
            'endpoint_url': self.env.endpoint_url
        }

    @property
    def softlayer_client(self):
        if self._softrlayer_client is None:
            creds = self._client_creds()
            self._softrlayer_client = SoftLayer.Client(**creds)
        return self._softrlayer_client

    @property
    def vs_manager(self):
        return VSManager(client=self.softlayer_client)

    def remove_softlayer_resources(self, resources_to_remove):
        leftovers = []
        for instance in resources_to_remove:
            instance_id = instance['id']
            leftover = {
                'instance': instance,
                'reason': ''
            }
            try:
                res = self.vs_manager.cancel_instance(instance_id=instance_id)
                if not res:
                    leftover['reason'] = 'cancel_instance returned False'
                elif not self._wait_for_instance_deletion(instance_id):
                    leftover['reason'] = \
                        'instance was not deleted in time, ' \
                        'waited for {0} seconds'\
                        .format(WAIT_FOR_DELETE_TIMEOUT)
            except SoftLayerAPIError as e:
                leftover['reason'] = e.message
            leftovers.append(instance)
        return leftovers

    def list_instances(self, domain):
        return self.vs_manager.list_instances(domain=domain)

    def _wait_for_instance_deletion(self, instance_id):
        timeout = time.time() + WAIT_FOR_DELETE_TIMEOUT
        while time.time() < timeout:
            try:
                self.vs_manager.get_instance(instance_id=instance_id)
                # instance with that id exists, try again in INTERVAL seconds
                time.sleep(WAIT_FOR_DELETE_INTERVAL)
            except SoftLayerAPIError as e:
                # instance removed as expected
                if e.faultCode == constants.SL_OBJECT_NOT_FOUND_ERROR:
                    return True
        return False
handler = SoftLayerHandler


def update_config(variables, **_):
    # used by tests
    os.environ[constants.SL_USERNAME] = variables[
        'system_tests_softlayer_username']
    os.environ[constants.SL_API_KEY] = variables[
        'system_tests_softlayer_api_key']
