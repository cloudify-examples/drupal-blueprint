#########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  * See the License for the specific language governing permissions and
#  * limitations under the License.

import json
import os
import sys

from cloudify import context
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError, RecoverableError
from functools import wraps
import constants
from SoftLayer.API import Client
from SoftLayer.exceptions import \
    SoftLayerAPIError, TransportError, Unauthenticated


def with_softlayer_client(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        _put_client_in_kwargs(kwargs)

        try:
            return f(*args, **kwargs)
        except TransportError, e:
            _re_raise(e, recoverable=True, retry_after=_retry_after(kwargs))
        except Unauthenticated, e:
                _re_raise(e, recoverable=False)
    return wrapper


def _retry_after(kwargs):
    try:
        return int(kwargs.pop('retry_after'))
    except (KeyError, ValueError):
        return 0


def authenticate(client):
    try:
        client[constants.ACCOUNT].getObject()
    except SoftLayerAPIError:
        raise NonRecoverableError('Failed validate username and api_key')


def _put_client_in_kwargs(kwargs):
    client_name = constants.SL_CLIENT_NAME
    if client_name in kwargs:
        return
    if ctx.type == context.NODE_INSTANCE:
        config = ctx.node.properties.get(constants.API_CONFIG)
    elif ctx.type == context.RELATIONSHIP_INSTANCE:
        config = ctx.source.node.properties.get(constants.API_CONFIG)
        if not config:
            config = ctx.target.node.properties.get(constants.API_CONFIG)
    else:
        raise 'config property is available ' \
              'only on context type "NODE_INSTANCE" ' \
              'or "RELATIONSHIP_INSTANCE"'
    config = config or {}
    add_missing_configuration_from_file(config)
    validate_credentials_exist(config)
    client = Client(**config)
    authenticate(client)
    kwargs[client_name] = client


def _re_raise(e, recoverable, retry_after=None, status_code=None):
    exc_type, exc, traceback = sys.exc_info()
    message = e.message
    if status_code is not None:
        message = '{0} [status_code={1}]'.format(message, status_code)
    if recoverable:
        if retry_after == 0:
            retry_after = None
        raise RecoverableError(
            message=message,
            retry_after=retry_after), None, traceback
    else:
        raise NonRecoverableError(message), None, traceback


def generate_hostname(hostname, prefix=''):
    final_pref = prefix
    if len(final_pref) > constants.HOST_PREFIX_LEN:
        final_pref = final_pref[:constants.HOST_PREFIX_LEN]
        ctx.logger.info(
            'prefix is too long, updating prefix from {0} to {1}'
            .format(final_pref, final_pref))
    remain_len = constants.MAX_HOSTNAME_CHARS - len(final_pref) - 1
    name = hostname
    if len(name) > remain_len:
        name = hostname[-remain_len:]
    if final_pref:
        final_hostname = "{0}-{1}".format(final_pref, name)
    else:
        final_hostname = name
    final_hostname = final_hostname.replace('_', '-').replace('--', '-')
    return final_hostname


def list_host_names_by_domain(vs_manager, domain):
    list_instances = vs_manager.list_instances(domain=domain)
    return [instance[constants.HOSTNAME] for instance in list_instances]


def add_missing_configuration_from_file(config):
    config_path = constants.DEFAULT_SOFTLAYER_CONFIG_PATH
    config_path = os.path.expanduser(config_path)
    if not os.path.exists(config_path):
        ctx.logger.debug(
            'Softlayer configuration file does not exist [{0}]'
            .format(config_path))
        return
    try:
        with open(config_path) as f:
            file_config = json.loads(f.read())
        # update config with missing values from configuration file
        for key, value in file_config.items():
            if not config.get(key):
                ctx.logger.info(
                    'updating {0} from file [{1}]'
                    .format(key, config_path))
                config[key] = value
    except IOError as e:
        ctx.logger.warn(
            'failed to open configuration file [{0}]: {1}'
            .format(config_path, str(e)))


def validate_credentials_exist(config):
    username = config[constants.API_CONFIG_USERNAME]
    api_key = config[constants.API_CONFIG_API_KEY]
    if not username:
        if not os.environ.get(constants.SL_USERNAME):
            raise NonRecoverableError(
                'username is missing - should be declared in blueprint '
                'or be set in environment variable: {0}'
                .format(constants.SL_USERNAME))
    if not api_key:
        if not os.environ.get(constants.SL_API_KEY):
            raise NonRecoverableError(
                'api_key is missing - should be declared in blueprint '
                'or be set in environment variable: {0}'
                .format(constants.SL_API_KEY))
