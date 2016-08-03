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

import softlayer_plugin
from SoftLayer.exceptions import SoftLayerAPIError

import constants
from cloudify.decorators import operation
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError
from constants import COMPUTE_PROPERTIES
from extended_vs_manager import ExtendedVSManager
from softlayer_plugin import list_host_names_by_domain, with_softlayer_client


def _validate_required_properties(**kwargs):
    required_keys = COMPUTE_PROPERTIES['required_items']
    required_values = [kwargs.get(item) for item in required_keys]
    if not all(required_values):
        raise NonRecoverableError('%s are required' % required_keys)

    required_at_least_one = COMPUTE_PROPERTIES['required_at_least_one_item']
    required_at_least_one_values = \
        [kwargs.get(item) for item in required_at_least_one]
    if not any(required_at_least_one_values):
        raise NonRecoverableError(
            'At least one of %s is required' % required_at_least_one)

    mutually_exclusive_keys = COMPUTE_PROPERTIES['mutually_exclusive_items']
    for me_group in mutually_exclusive_keys:
        has_value = []
        for item in me_group:
            if kwargs.get(item):
                if has_value:
                    raise NonRecoverableError('Can only specify one of {0} '
                                              '(both {1} and {2} have values)'
                                              .format(me_group,
                                                      has_value[0], item))
                has_value.append(item)


def _generate_price_ids(options, instance_properties):
    price_ids = []
    item_ids = _get_item_ids_from_node_properties(**instance_properties)
    # converting all additional item ids to the corresponding price ids.
    for item_id in instance_properties[constants.ADDITIONAL_IDS]:
        item = options.get(item_id)
        if not item:
            raise NonRecoverableError('additional item id {0} does not exist'
                                      .format(item_id))
        price_ids.append(item['price_id'])
    # converting all item ids to the corresponding price ids.
    for cat, item_id in item_ids.items():
        item = options.get(item_id)
        # validating that the item exists at the client's catalog
        # under the expected category.
        if not item:
            raise NonRecoverableError('item id [{0}] (declared for {1}) '
                                      'does not exist'
                                      .format(item_id, cat))
        group_codes = item['group_codes']
        expected_group_code = COMPUTE_PROPERTIES['items'][cat]
        if expected_group_code not in group_codes:
            raise NonRecoverableError('item id {0} belongs to '
                                      'category group {1} and not to {2} '
                                      '(property name: {3})'
                                      .format(item_id, group_codes,
                                              expected_group_code, cat))
        price_ids.append(item['price_id'])
    return price_ids


def _generate_hostname(hosts, hostname, prefix=''):
    name = softlayer_plugin.generate_hostname(hostname, prefix)
    if name in hosts:
        raise NonRecoverableError('hostname [{0}] already exists'.format(name))
    return name


def _get_item_ids_from_node_properties(**instance_properties):
    items_ids = {}
    for item in COMPUTE_PROPERTIES['items']:
        value = instance_properties.get(item)
        if value:
            items_ids[item] = value
    return items_ids


def _create_order_options(instance_properties, price_ids, vs_manager):
    hosts = list_host_names_by_domain(vs_manager,
                                      instance_properties[constants.DOMAIN])
    prefix = ctx.bootstrap_context.resources_prefix
    if prefix:
        ctx.logger.info(
            'got prefix from bootstrap_context: {0}'.format(prefix))
    hostname = instance_properties.get(constants.HOSTNAME) or ctx.instance.id
    order = {
        'hostname': _generate_hostname(hosts, hostname, prefix),
        'price_ids': price_ids
    }
    for item in COMPUTE_PROPERTIES['order_options']:
        order[item] = instance_properties[item]

    if not order[constants.SSH_KEYS]:
        # update ssh_keys from provider context
        order[constants.SSH_KEYS] = \
            ctx.provider_context.get(constants.SSH_KEYS) or []

    return order


def _get_transaction_full_name(active_transaction):
    if not active_transaction:
        return ''
    status = active_transaction[constants.TRANSACTION_STATUS]
    name = status.get(constants.TRANSACTION_FRIENDLY_NAME)
    if not name:
        name = status[constants.TRANSACTION_NAME]
    full_name = 'name: {0}'.format(name)
    transaction_group = active_transaction.get(constants.TRANSACTION_GROUP)
    if transaction_group:
        full_name = '{0}, group: {1}'.format(
            full_name, transaction_group[constants.TRANSACTION_NAME])
    return full_name


def _get_vm_details():
    instance_id = ctx.instance.runtime_properties[constants.INSTANCE_ID]
    hostname = ctx.instance.runtime_properties[constants.HOSTNAME]
    return {
        'hostname': hostname,
        'instance_id': instance_id
    }


def _get_vm_details_for_print(details=None):
    if not details:
        details = _get_vm_details()
    hostname = details[constants.HOSTNAME]
    instance_id = details[constants.INSTANCE_ID]
    return 'hostname: {0}, id: {1}'.format(hostname, instance_id)


def get_active_transaction(virtual_guest_service, instance_id):
    try:
        return virtual_guest_service.getActiveTransaction(
            id=instance_id, mask=constants.TRANSACTION_GROUP)
    except SoftLayerAPIError as e:
        if e.faultCode == 'SoftLayer_Exception_ObjectNotFound':
            return ''
        raise e


def _validate_private_network_only(options, price_ids, **instance_properties):
    port_speed_id = instance_properties[constants.PORT_SPEED]
    if port_speed_id:
        item = options[port_speed_id]
        description = item['description']
        if instance_properties[constants.PRIVATE_NETWORK_ONLY]:
            if 'Public' in description:
                # change port speed id to private only
                port_speed_id = constants.DEFAULT_PRIVATE_PORT_SPEED
                private_port_speed_item = options[port_speed_id]
                price_ids.remove(item['price_id'])
                price_ids.append(private_port_speed_item['price_id'])
                description = private_port_speed_item['description']
                ctx.logger.info('private_network_only flag is set => '
                                'changing the port speed '
                                'to a private only type [{0}]'
                                .format(description))
        if 'Public' not in description:
            # private only
            if instance_properties[constants.PUBLIC_VLAN]:
                raise NonRecoverableError(
                    'A public network VLAN [{0}] cannot be specified '
                    'on a server that is private network only '
                    '[port speed item id - {1} description: {2}].'
                    .format(instance_properties[constants.PUBLIC_VLAN],
                            port_speed_id,
                            description))


def _get_create_options(client, package_id):
    # Parses data from the specified package into a dictionary.
    package = client[constants.PRODUCT_PACKAGE]
    results = {}
    for category in package.getCategories(id=package_id):
        for group in category['groups']:
            for price in group['prices']:
                group_code = category['categoryCode']
                itemId = price['itemId']
                resultItem = results.get(itemId)
                if resultItem:
                    group_codes = results[itemId]['group_codes']
                    group_codes.append(group_code)
                else:
                    group_codes = [group_code]
                results[price['itemId']] = {
                    'price_id': price['id'],
                    'group_codes': group_codes,
                    'description': price['item']['description']
                }
    return results


def _retrieve_vm_credentials(vm):
    vm_details = _get_vm_details_for_print()
    ctx.logger.info('retrieving credentials of VM [{0}]'
                    .format(vm_details))
    try:
        ctx.instance.runtime_properties[constants.PUBLIC_IP] \
            = vm.get(constants.VM_PUBLIC_IP)
        ctx.logger.debug('set public ip to {0}'.format(
            ctx.instance.runtime_properties[constants.PUBLIC_IP]))
        ctx.instance.runtime_properties[constants.PRIVATE_IP] \
            = vm.get(constants.VM_PRIVATE_IP)
        ctx.logger.debug('set private ip to {0}'.format(
            ctx.instance.runtime_properties[constants.PRIVATE_IP]))
        vm_operating_system = vm.get(constants.VM_OS)
        if not vm_operating_system:
            ctx.logger.info('Login information not available for VM [{0}]'
                            .format(vm_details))
        vm_passwords = vm_operating_system.get(constants.PASSWORDS)
        if len(vm_passwords) > 0:
            ctx.logger.info('Updating login information for VM [{0}]'
                            .format(vm_details))
            os_credentials = vm_passwords[0]
            ctx.instance.runtime_properties[constants.USERNAME] \
                = os_credentials[constants.USERNAME]
            ctx.instance.runtime_properties[constants.PASSWORD] \
                = os_credentials[constants.PASSWORD]
            return True
        else:
            ctx.logger.info('Login information not available for VM [{0}]'
                            .format(vm_details))
    except Exception:
        ctx.logger.info('Login information not available for VM [{0}].'
                        .format(vm_details))
    return False


@operation
@with_softlayer_client
def os_reload(softlayer_client, post_uri, ssh_keys, **_):

    vs_manager = ExtendedVSManager(softlayer_client)
    instance_id = ctx.instance.runtime_properties[constants.INSTANCE_ID]
    ctx.logger.info('os reload for server with'
                    ' instance Id {0}'.format(instance_id))

    vs_manager.reload_instance(instance_id,
                               post_uri=post_uri, ssh_keys=ssh_keys)
    ctx.logger.info('waiting for os reload on '
                    'server with Id {0} to become'
                    ' ready...'.format(instance_id))
    vs_manager.wait_for_ready(instance_id, pending=True)

    vm = vs_manager.get_instance(instance_id=instance_id)

    is_active = \
        vm is not None \
        and vm[constants.STATUS][constants.STATUS_KEY_NAME] == constants.ACTIVE
    if is_active:
        vs_ready = _retrieve_vm_credentials(vm)
    ctx.logger.info('VM [{0}] is {1} ready'.
                    format(vm['fullyQualifiedDomainName'],
                           ('' if vs_ready else 'not')))


def _validate_inputs_and_generate_price_ids(
        softlayer_client, **instance_properties):
    _validate_required_properties(**instance_properties)
    options = _get_create_options(client=softlayer_client,
                                  package_id=constants.PACKAGE_ID)
    price_ids = _generate_price_ids(options=options,
                                    instance_properties=instance_properties)
    _validate_private_network_only(options=options,
                                   price_ids=price_ids,
                                   **instance_properties)
    return price_ids


def _create(softlayer_client):

    # validate
    instance_properties = ctx.node.properties
    price_ids = _validate_inputs_and_generate_price_ids(
        softlayer_client, **instance_properties)

    # create the order
    vs_manager = ExtendedVSManager(softlayer_client)
    order = _create_order_options(instance_properties=instance_properties,
                                  price_ids=price_ids,
                                  vs_manager=vs_manager)

    # verify before placing the order
    ctx.logger.info('verifying order: {0}'.format(order))
    vs_manager.verify_place_order(**order)

    # place an order
    hostname = order[constants.HOSTNAME]
    ctx.logger.info('Placing an order for VM [{0}]'.format(hostname))
    order_result = vs_manager.place_order(**order)

    # store information in runtime properties
    instance_id = order_result['orderDetails']['virtualGuests'][0]['id']
    ctx.instance.runtime_properties[constants.INSTANCE_ID] = instance_id
    ctx.instance.runtime_properties[constants.HOSTNAME] = hostname
    ctx.logger.info('An order for creating host [id: {0}, hostname: {1}] '
                    'has been placed. waiting fot transactions to begin..'
                    .format(instance_id, hostname))
    ctx.instance.runtime_properties[constants.STATUS] = constants.CREATE_SENT


@operation
@with_softlayer_client
def create(softlayer_client, retry_interval_secs, **_):

    status = ctx.instance.runtime_properties.get(constants.STATUS)
    if not status == constants.CREATE_SENT:
        # create hasn't been called before or didn't finish successfully
        _create(softlayer_client)

    # verify the instance creation starts before the timeout is reached
    # (this means the VM creation began, not completed)
    instance_id = ctx.instance.runtime_properties.get(constants.INSTANCE_ID)
    active_transaction = get_active_transaction(
        softlayer_client[constants.VIRTUAL_GUEST], instance_id)
    if not active_transaction:
        return ctx.operation.retry(
            message='There is no active transaction on host [{0}], '
                    'waiting for transactions to begin... '
                    'operation will be retried'.format(_get_vm_details()),
            retry_after=retry_interval_secs)


@operation
@with_softlayer_client
def start(softlayer_client, retry_interval_secs, **_):

    vm_details = _get_vm_details()
    instance_id = vm_details[constants.INSTANCE_ID]
    vm_details_to_print = _get_vm_details_for_print(vm_details)

    # retry if there is an active transaction
    virtual_guest_service = softlayer_client[constants.VIRTUAL_GUEST]
    transaction_name = _get_transaction_full_name(
        get_active_transaction(virtual_guest_service, instance_id))
    if transaction_name:
        return ctx.operation.retry(
            message='host [{0}] has active transaction [{1}], '
                    'waiting for transactions to end.. '
                    'operation will be retried'.format(vm_details_to_print,
                                                       transaction_name),
            retry_after=retry_interval_secs)

    # starting the server if the state is not RUNNING
    state = virtual_guest_service.getPowerState(id=instance_id)[
        constants.POWER_STATE_KEY_NAME]
    if state != constants.RUNNING_STATE:
        ctx.logger.info('starting server [{0}]'.format(vm_details_to_print))
        ok = virtual_guest_service.powerOn(id=instance_id)
        state = virtual_guest_service.getPowerState(id=instance_id)[
            constants.POWER_STATE_KEY_NAME]
        if ok and state == constants.RUNNING_STATE:
            ctx.logger.info('server [{0}] was started successfully'
                            .format(vm_details_to_print))
            ctx.instance.runtime_properties[
                constants.STATUS] = constants.STARTED
        else:
            raise NonRecoverableError(
                'failed to start server [{0}], power state: {1}'
                .format(vm_details_to_print, state))
    else:
        # state is RUNNING
        ctx.logger.info('server [{0}] '
                        'is already running, '
                        ' start will not be performed.'
                        .format(vm_details_to_print))
    vm = ExtendedVSManager(softlayer_client).get_instance(instance_id)
    if not _retrieve_vm_credentials(vm):
        raise NonRecoverableError(
            'Login information is not available for VM [{0}]'
            .format(vm_details_to_print))


@operation
@with_softlayer_client
def stop(softlayer_client, retry_interval_secs, **_):

    vm_details = _get_vm_details()
    instance_id = vm_details[constants.INSTANCE_ID]
    vm_details_to_print = _get_vm_details_for_print(vm_details)

    # retry if there is an active transaction
    virtual_guest_service = softlayer_client[constants.VIRTUAL_GUEST]
    transaction_name = _get_transaction_full_name(
        get_active_transaction(virtual_guest_service, instance_id))
    if transaction_name:
        return ctx.operation.retry(
            message='host [{0}] has active transaction [{1}], '
                    'waiting for transactions to end.. '
                    'operation will be retried'.format(vm_details_to_print,
                                                       transaction_name),
            retry_after=retry_interval_secs)

    # stopping the server if the state is RUNNING
    state = virtual_guest_service.getPowerState(id=instance_id)[
        constants.POWER_STATE_KEY_NAME]
    if state == constants.RUNNING_STATE:
        ctx.logger.info('stopping server [{0}]'.format(vm_details_to_print))
        ok = virtual_guest_service.powerOff(id=instance_id)
        state = virtual_guest_service.getPowerState(id=instance_id)[
            constants.POWER_STATE_KEY_NAME]
        if ok and state == constants.HALTED_STATE:
            ctx.logger.info('server [{0}] was stopped successfully'
                            .format(vm_details_to_print))
            ctx.instance.runtime_properties[
                constants.STATUS] = constants.STOPPED
        else:
            raise NonRecoverableError(
                'failed to stop server [{0}], power state: {1}'
                .format(vm_details_to_print, state))
    else:
        # state is not RUNNING
        ctx.logger.info('server [{0}] is not running, '
                        'power state is {1}, '
                        'stop will not be performed.'
                        .format(vm_details_to_print, state))


def _delete(softlayer_client):

    vm_details = _get_vm_details()
    ctx.logger.info('deleting server [{0}]'
                    .format(_get_vm_details_for_print(vm_details)))

    vs = ExtendedVSManager(softlayer_client)
    vs.cancel_instance(vm_details[constants.INSTANCE_ID])
    ctx.instance.runtime_properties[constants.STATUS] = constants.DELETE_SENT


@operation
@with_softlayer_client
def delete(softlayer_client, retry_interval_secs, **_):

    status = ctx.instance.runtime_properties.get(constants.STATUS)
    if not status == constants.DELETE_SENT:
        # delete hasn't been called before or didn't finish successfully
        _delete(softlayer_client)

    # retry until the instance deletion starts
    # (this means the VM deletion began, not completed)
    instance_id = ctx.instance.runtime_properties.get(constants.INSTANCE_ID)
    active_transaction = get_active_transaction(
        softlayer_client[constants.VIRTUAL_GUEST], instance_id)
    if not active_transaction:
        return ctx.operation.retry(
            message='There is no active transaction on host [{0}], '
                    'waiting for transactions to begin... '
                    'operation will be retried'.format(_get_vm_details()),
            retry_after=retry_interval_secs)


@operation
@with_softlayer_client
def creation_validation(softlayer_client, **_):
    _validate_inputs_and_generate_price_ids(
        softlayer_client, **ctx.node.properties)
