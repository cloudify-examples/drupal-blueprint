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


# ctx is imported and used in operations
from cloudify.workflows import ctx

# put the workflow decorator on any function that is a task
from cloudify.decorators import workflow
import os


@workflow
def restart_vms(node_id, node_instance_id=None, my_input=None, **kwargs):
    ctx.logger.info("restart_vms node_id {0}".format(node_id))
    node = ctx.get_node(node_id)
    if my_input is None:
        ctx.logger.info("my_input is None. Setting it to NA")
        my_input = "N/A"

    if node_instance_id is None:
        ctx.logger.info("node_instance_id is None. Will run on all the instances of {0}".format(node_id))

    for instance in node.instances:
        instance_str = str(instance.id)
        ctx.logger.info("Checking instance.id : {0} of node {1}".format(instance_str, str(node_id)))
        if node_instance_id is None or node_instance_id == instance_str:
            ctx.logger.info("Running execute_operation(utils.ops.restart_vm_op) on {0}".format(instance_str))
            instance.execute_operation("utils.ops.restart_vm_op", kwargs={'process': {'args': [my_input]}})
            ctx.logger.info("Ran execute_operation(utils.ops.restart_vm_op) on {0}".format(instance_str))
    ctx.logger.info("End of restart_vms")
