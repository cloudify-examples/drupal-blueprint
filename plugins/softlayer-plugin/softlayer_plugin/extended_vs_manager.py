########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
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

from SoftLayer.managers.vs import VSManager
from softlayer_plugin.constants import PACKAGE_ID


def _generate_prices_ids(price_ids):
    prices = []
    if price_ids:
        for price_id in price_ids:
            price_id_dict = dict(id=price_id)
            prices.append(price_id_dict)
    return prices


def _generate_virtual_guests_options(domain, hostname,
                                     private_network_only=False,
                                     public_vlan=None, private_vlan=None):
    virtual_guests = {
        'domain': domain,
        'hostname': hostname,
        'privateNetworkOnlyFlag': private_network_only
    }

    if public_vlan:
        virtual_guests['primaryNetworkComponent'] = {
            'networkVlan': {'id': int(public_vlan)}}
    if private_vlan:
        virtual_guests['primaryBackendNetworkComponent'] = {
            'networkVlan': {'id': int(private_vlan)}}

    return virtual_guests


def _generate_place_order_options(location,
                                  hostname,
                                  domain,
                                  use_hourly_pricing=False,
                                  quantity=1,
                                  provision_scripts=None,
                                  private_network_only=False,
                                  private_vlan=None,
                                  public_vlan=None,
                                  image_template_global_id=None,
                                  image_template_id=None,
                                  ssh_keys=None,
                                  price_ids=None):
    """ Generates the order options of the desired virtual guest

    :param location: The location to use.
    :param hostname: The hostname to use.
    :param domain: The domain to use.
    :param bool use_hourly_pricing: Flag to indicate
            if this server should be billed hourly (default) or monthly.
    :param quantity: The amount of servers to order.
    :param list provision_scripts: A list of the URIs of the post-install
                            scripts to run after reload.
    :param bool private_network_only:
            Flag to indicate whether the computing instance
            only has access to the private network.
    :param int public_vlan: The ID of the public VLAN on which you want
                            this VS placed.
    :param int private_vlan: The ID of the public VLAN on which you want
                             this VS placed.
    :param ssh_keys: The SSH keys to add to the root user.
    :param price_ids: The list of price ids.
    """

    virtual_guest = _generate_virtual_guests_options(
        domain=domain,
        hostname=hostname,
        private_network_only=private_network_only,
        private_vlan=private_vlan,
        public_vlan=public_vlan)

    order_options = {
        'packageId': PACKAGE_ID,
        'location': location,
        'prices': _generate_prices_ids(price_ids),
        'virtualGuests': [virtual_guest],
        'quantity': quantity,
        'useHourlyPricing': use_hourly_pricing,
        }

    if provision_scripts:
        order_options['provisionScripts'] = provision_scripts
    if ssh_keys:
        order_options['sshKeys'] = [{'sshKeyIds': ssh_keys}]
    if image_template_global_id:
        order_options['imageTemplateGlobalIdentifier'] = \
            image_template_global_id
    if image_template_id:
        order_options['imageTemplateId'] = image_template_id

    return order_options


class ExtendedVSManager(VSManager):

    def verify_place_order(self, **kwargs):
        """Verifies an order to create a VS.

        :param location:                The location to use.
        :param hostname:                The hostname to use.
        :param domain:                  The domain to use.
        :param bool use_hourly_pricing: Flag to indicate if this guest should
                                        be billed hourly (default) or monthly.
        :param quantity:                The amount of virtual guests to order.
        :param list provision_scripts:  A list of the URIs of the post-install
                                        scripts to run on the virtual guest.
        :param bool private_network_only:
                                        Flag to indicate whether the computing
                                        instance only has access to the private
                                        network.
        :param int private_vlan:        The ID of the public VLAN on which you
                                        want this VS placed.
        :param int public_vlan:         The ID of the public VLAN on which you
                                        want this VS placed.
        :param image_template_global_id:
                                        An image template global id to load the
                                        VS with. If an image is used, OS should
                                        not be specified.
        :param image_template_id:       An image template id to load the VS
                                        with. If an image is used, OS should
                                        not be specified.
        :param ssh_keys:                The SSH keys to add to the root user.
        :param price_ids:               A list of the required items price ids.
        """
        place_order_options = _generate_place_order_options(**kwargs)
        return self.client['Product_Order'].verifyOrder(place_order_options)

    def place_order(self, **kwargs):
        """Places an order to create a VS.

        :param location:                The location to use.
        :param hostname:                The hostname to use.
        :param domain:                  The domain to use.
        :param bool use_hourly_pricing: Flag to indicate if this guest should
                                        be billed hourly (default) or monthly.
        :param quantity:                The amount of virtual guests to order.
        :param list provision_scripts:  A list of the URIs of the post-install
                                        scripts to run on the virtual guest.
        :param bool private_network_only:
                                        Flag to indicate whether the computing
                                        instance only has access to the private
                                        network.
        :param int private_vlan:        The ID of the public VLAN on which you
                                        want this VS placed.
        :param int public_vlan:         The ID of the public VLAN on which you
                                        want this VS placed.
        :param image_template_global_id:
                                        An image template global id to load the
                                        VS with. If an image is used, OS should
                                        not be specified.
        :param image_template_id:       An image template id to load the VS
                                        with. If an image is used, OS should
                                        not be specified.
        :param ssh_keys:                The SSH keys to add to the root user.
        :param price_ids:               A list of the required items price ids.
        """
        place_order_options = _generate_place_order_options(**kwargs)
        return self.client['Product_Order'].placeOrder(place_order_options)
