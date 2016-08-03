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

PACKAGE_ID = 46
DEFAULT_PRIVATE_PORT_SPEED = 497
DEFAULT_SOFTLAYER_CONFIG_PATH = '~/softlayer_config.json'
DEFAULT_HOSTNAME_PREFIX = 'vs'
MAX_HOSTNAME_CHARS = 15
HOST_PREFIX_LEN = 5

SL_OBJECT_NOT_FOUND_ERROR = 'SoftLayer_Exception_ObjectNotFound'

# client
SL_CLIENT_NAME = 'softlayer_client'
VIRTUAL_GUEST = 'Virtual_Guest'
PRODUCT_PACKAGE = 'Product_Package'
ACCOUNT = 'Account'

# environment variables
SL_USERNAME = 'SL_USERNAME'
SL_API_KEY = 'SL_API_KEY'

# SL instance properties
VM_PUBLIC_IP = 'primaryIpAddress'
VM_PRIVATE_IP = 'primaryBackendIpAddress'
VM_OS = 'operatingSystem'
STATUS = 'status'
STATUS_KEY_NAME = 'keyName'
ACTIVE = 'ACTIVE'

# api_config
API_CONFIG_USERNAME = 'username'
API_CONFIG_API_KEY = 'api_key'

# SL power states
POWER_STATE_KEY_NAME = 'keyName'
RUNNING_STATE = 'RUNNING'
HALTED_STATE = 'HALTED'

# SL transaction properties
TRANSACTION_GROUP = 'transactionGroup'
TRANSACTION_STATUS = 'transactionStatus'
TRANSACTION_FRIENDLY_NAME = 'friendlyName'
TRANSACTION_NAME = 'name'

# runtime properties
DOMAIN = 'domain'
INSTANCE_ID = 'instance_id'
HOSTNAME = 'hostname'
PASSWORDS = 'passwords'
USERNAME = 'username'
PASSWORD = 'password'
PRIVATE_IP = 'ip'
PUBLIC_IP = 'public_ip'
STATUS = 'status'
CREATE_SENT = 'create_request_has_been_sent'
DELETE_SENT = 'delete_request_has_been_sent'
STARTED = 'start_completed'
STOPPED = 'stop_completed'


# instance properties
API_CONFIG = 'api_config'

LOCATION = 'location'
DOMAIN = 'domain'
RAM = 'ram'
OS = 'os'
CPU = 'cpu'
DISK = 'disk'

USE_HOURLY_PRICING = 'use_hourly_pricing'
QUANTITY = 'quantity'
PROVISION_SCRIPTS = 'provision_scripts'
PRIVATE_NETWORK_ONLY = 'private_network_only'
PRIVATE_VLAN = 'private_vlan'
PUBLIC_VLAN = 'public_vlan'
IMAGE_TEMPLATE_GLOBAL_ID = 'image_template_global_id'
IMAGE_TEMPLATE_ID = 'image_template_id'
SSH_KEYS = 'ssh_keys'
PORT_SPEED = 'port_speed'
PRICE_IDS = 'price_ids'
ADDITIONAL_IDS = 'additional_ids'

BAMDWIDTH = 'bandwidth'
PRI_IP_ADDRESSES = 'pri_ip_addresses'
MONITORING = 'monitoring'
NOTIFICATION = 'notification'
RESPONSE = 'response'
REMOTE_MANAGEMENT = 'remote_management'
VULNERABILITY_SCANNER = 'vulnerability_scanner'
VPN_MANAGEMENT = 'vpn_management'

# group codes
RAM_GROUP_CODE = 'ram'
OS_GROUP_CODE = 'os'
CPU_GROUP_CODE = 'guest_core'
DISK_GROUP_CODE = 'guest_disk0'
PORT_SPEED_GROUP_CODE = 'port_speed'
BAMDWIDTH_GROUP_CODE = 'bandwidth'
PRI_IP_ADDRESSES_GROUP_CODE = 'pri_ip_addresses'
MONITORING_GROUP_CODE = 'monitoring'
NOTIFICATION_GROUP_CODE = 'notification'
RESPONSE_GROUP_CODE = 'response'
REMOTE_MANAGEMENT_GROUP_CODE = 'remote_management'
VULNERABILITY_SCANNER_GROUP_CODE = 'vulnerability_scanner'
VPN_MANAGEMENT_GROUP_CODE = 'vpn_management'

# input properties
COMPUTE_PROPERTIES = {
    'order_options': {
        LOCATION,
        DOMAIN,
        USE_HOURLY_PRICING,
        QUANTITY,
        PROVISION_SCRIPTS,
        PRIVATE_NETWORK_ONLY,
        PRIVATE_VLAN,
        PUBLIC_VLAN,
        IMAGE_TEMPLATE_GLOBAL_ID,
        IMAGE_TEMPLATE_ID,
        SSH_KEYS,
    },
    'items': {
        # items and group codes
        RAM: 'ram',
        OS: 'os',
        CPU: CPU_GROUP_CODE,
        DISK: DISK_GROUP_CODE,
        PORT_SPEED: PORT_SPEED_GROUP_CODE,
        BAMDWIDTH: BAMDWIDTH_GROUP_CODE,
        PRI_IP_ADDRESSES: PRI_IP_ADDRESSES_GROUP_CODE,
        MONITORING: MONITORING_GROUP_CODE,
        NOTIFICATION: NOTIFICATION_GROUP_CODE,
        RESPONSE: RESPONSE_GROUP_CODE,
        REMOTE_MANAGEMENT: REMOTE_MANAGEMENT_GROUP_CODE,
        VULNERABILITY_SCANNER: VULNERABILITY_SCANNER_GROUP_CODE,
        VPN_MANAGEMENT: VPN_MANAGEMENT_GROUP_CODE
    },
    'required_items': [
        LOCATION,
        DOMAIN,
        RAM,
        CPU,
        DISK,
    ],
    'required_at_least_one_item': [
        OS,
        IMAGE_TEMPLATE_ID,
        IMAGE_TEMPLATE_GLOBAL_ID
    ],
    'mutually_exclusive_items': [
        [
            IMAGE_TEMPLATE_ID,
            IMAGE_TEMPLATE_GLOBAL_ID,
            OS
        ],
        [
            PRIVATE_NETWORK_ONLY,
            PUBLIC_VLAN
        ]
    ],
}
