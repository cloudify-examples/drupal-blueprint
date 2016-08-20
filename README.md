# drupal-blueprint
A Drupal (LAMP CMS) blueprint for OpenStack and Hybrid Cloud (OpenStack and vSphere)

This blueprint enables ypu to deploy, configure, monitor, heal and scale a Drupal 7 on OpenStack and on Hybrid Cloud (OpenStack and vSphere). <br>
Once installed, Cloudify enables you to perform Day-2 operations on your live environments. <br>
E.G :  Apply patches, invoke security updates etc. <br>


# Prerequisites

- An Ubuntu 14.04 image id from your OpenStack account and from your vSphere account <br>
- An flavor image id of your choice from your OpenStack account <br>

# Tested Version

This blueprint has been test with Cloudify version 3.4.0 and with Drupal 7.

# Usage

All you need to do is to set/specify (as an input to the blueprint) the OpenStack image id for Ubuntu 14.04 and the OpenStack flavor Id. <br>
If you use the Hybrid version, you need to set/specify (as an input to the blueprint) the vsphere_template_name for Ubuntu 14.04.


### Step 1: Installation

`cfy install upload -b <choose_blueprint_id> -p <blueprint_filename>` <br>

If you have or want to use an inputs file : <br>
`cfy install upload -b <choose_blueprint_id> -p <blueprint_filename> -i <your_inputs_file>` <br>

This process will create all the cloud resources needed for the application and the application itself ...: <br>

- VMs
- Floating IP's
- Security Groups

and everything else that is needed and declared in the blueprint.<br>

### Step 2: Verify installation

Once the workflow execution is complete, we can view the application endpoint by running: <br>

`cfy deployments outputs -d <deployment_id>`

Hit that URL to see the application running.

### Step 3: Demo the Day-2 Operation.

The following will change the theme of the Drupal site. <br>
It can be invoked from the Cloudify manager UI as well...

Here are instructions to run it from the Cloudify CLI: <br>

*export dep=<deployment_id>*
*export myTheme=mayo*
*cfy executions start -d $dep  -w drush_install -p "project_name=${myTheme}"*

This is how you invoke it from the drush_setvar workflow from the CFY CLI :

*cfy executions start -d $dep  -w drush_setvar -p "variable_name=theme_default;variable_value=${myTheme}"*

Now refresh the web page of the Drupal site and see that the theme has indeed changed.


### Step 4: Demo the Auto Scale Example

By using the apache IP & PORT which are in the output of the command above, you can run:

`ab -n 1000000 -c 200 http://$IP:$PORT/`

This will increase the number of requests to the application. As a result the CPU used by the Drupal VM will spike above the scale up threshold. This metric is monitored by the Diamond plugin, and the Riemann auto-scale policy calls the scale workflow trigger.

Killing this command should cause the CPU to drop below the scale down threshold, and the application will scale down.

You can simulate a failed host by stopping or suspending a running memcacheD VM. The Riemann failed host policy will recognize the lack of system cpu metrics reporting on the host and will trigger the heal workflow.

### Step 5: Uninstall

Now lets run the `uninstall` workflow. This will uninstall the application,
as well as delete all related resources. <br>

`cfy uninstall -d <deployment_id>`

### For more info, you can Watch [this video](https://www.youtube.com/watch?v=GaUMZKtS8ws)

