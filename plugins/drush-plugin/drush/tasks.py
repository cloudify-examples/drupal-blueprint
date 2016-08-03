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
def install_project(project_name,**kwargs):
    ctx.logger.info("install_project {}".format(project_name))

    # I can use this instead ,but for the exercise I used something else
    # node = ctx.get_node('drupal_app')

    for node in ctx.nodes:
        if node.id == 'drupal_app':
            ctx.logger.info("install_project is about to exec on node.id {}".format(node.id))
            # See docs http://getcloudify.org/guide/3.1/plugin-script.html
            for instance in node.instances:
                instance.execute_operation("drupal.interfaces.action.install_project",
                                           kwargs={'process': {'args': [project_name]}})
    ctx.logger.info("End of install_project")

@workflow
def set_variable(variable_name,variable_value,**kwargs):
    ctx.logger.info("set_variable variable_name is  {}".format(variable_name))
    ctx.logger.info("set_variable variable_value is {}".format(variable_value))

    for node in ctx.nodes:
        if node.id == 'drupal_app':
            ctx.logger.info("set_variable is about to exec on node.id {}".format(node.id))
            # See docs http://getcloudify.org/guide/3.1/plugin-script.html
            for instance in node.instances:
                instance.execute_operation("drupal.interfaces.action.set_variable",
                                           kwargs={'process': {'args': [variable_name, variable_value]}})
    ctx.logger.info("End of set_variable")