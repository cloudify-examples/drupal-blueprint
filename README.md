[![CircleCI](https://circleci.com/gh/cloudify-examples/drupal-blueprint.svg?style=svg)](https://circleci.com/gh/cloudify-examples/drupal-blueprint)

# Drupal Blueprint

This blueprint deploys a Drupal CMS. This blueprint is part of the *End-to-end Solutions Package*, which demonstrates functionality in Cloudify using a Database, Load Balancer, and several front-end applications. Before installing this deployment, install the [MariaDB Blueprint](https://github.com/cloudify-examples/mariadb-blueprint), the [HAProxy Blueprint](https://github.com/cloudify-examples/haproxy-blueprint). Following the drupal deployment, continue with installing the [Kubernetes Cluster](http://docs.getcloudify.org/4.2.0/plugins/container-support/) and the [Wordpress Application](https://github.com/EarthmanT/db-lb-app).


## Compatibility

Tested with:
  * Cloudify 4.2


## Pre-installation steps

Upload the required plugins:

  * [Openstack Plugin](https://github.com/cloudify-cosmo/cloudify-openstack-plugin/releases).
  * [AWSSDK Plugin](https://github.com/cloudify-incubator/cloudify-awssdk-plugin/releases).
  * [AWS Plugin](https://github.com/cloudify-cosmo/cloudify-aws-plugin/releases).
  * [GCP Plugin](https://github.com/cloudify-incubator/cloudify-gcp-plugin/releases).
  * [Azure Plugin](https://github.com/cloudify-incubator/cloudify-azure-plugin/releases).
  * [Utilities Plugin](https://github.com/cloudify-incubator/cloudify-utilities-plugin/releases).
  * [DBLB Plugin](https://github.com/EarthmanT/cloudify-dblb/releases).

_Check the relevant blueprint for the latest version of the plugin._

**Install the relevant example network blueprint for the IaaS that you wish to deploy on:**

  * [Openstack Example Network](https://github.com/cloudify-examples/openstack-example-network)
  * [AWS Example Network](https://github.com/cloudify-examples/aws-example-network)
  * [GCP Example Network](https://github.com/cloudify-examples/gcp-example-network)
  * [Azure Example Network](https://github.com/cloudify-examples/azure-example-network)

In addition to the pre-requisites for your example network blueprint, you will need the following secrets:

  * `agent_key_private` and `agent_key_public`. If you do not already have these secrets, can generate them with the `keys.yaml` blueprint in the [helpful blueprint](https://github.com/cloudify-examples/helpful-blueprint) repo.

**Install the MariaDB Blueprint**

  * After installation is successful, check the deployment outputs. There is a single deployment output called `cluster_addresses`, which is a list of IP addresses. Select a single IP, this will be the value for your `application_ip` input in this blueprint, as a seed-IP.

**Install the HAproxy Blueprint**

There are no special instructions between deployment of HAProxy and Drupal.


## Installation

On your Cloudify Manager, navigate to _Local Blueprints_ select _Upload_.

[Right-click and copy URL](https://github.com/cloudify-examples/haproxy-blueprint/archive/master.zip). Paste the URL where it says _Enter blueprint url_. Provide a blueprint name, such as _lb_ in the field labeled _blueprint name_.

Select the blueprint for the relevant IaaS you wish to deploy on, for example _aws.yaml_ from _Blueprint filename_ menu. Click **Upload**.

After the new blueprint has been created, provide the seed `application_ip` input (see Install the MariaDB Blueprint above) click the **Deploy** button.

Navigate to _Deployments_, find your new deployment, select _Install_ from the _workflow_s menu. At this stage, you may provide your own values for any of the default _deployment inputs_.

For example, the _openstack.yaml_ blueprint requires that you provide a value for `image`. This is the ID of a _Centos 7_ image. You may also need to override the default `flavor` as the default value `2` may not be available in your account or appropriate.

You may also provide new values for the `db_deployment` and `lb_deployment` inputs. These are the deployment IDs of the *MariaDB Blueprint Deployment* and the *HAProxy Blueprint Deployment* respectively.


## Uninstallation

Navigate to the deployment and select `Uninstall`. When the uninstall workflow is finished, select `Delete deployment`.
