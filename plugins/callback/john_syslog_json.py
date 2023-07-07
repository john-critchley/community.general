# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    author: Unknown (!UNKNOWN)
    name: syslog_json
    type: notification
    requirements:
      - whitelist in configuration
    short_description: sends JSON events to syslog
    description:
      - This plugin logs ansible-playbook and ansible runs to a syslog server in JSON format.
      - Before Ansible 2.9 only environment variables were available for configuration.
    options:
      server:
        description: Syslog server that will receive the event.
        env:
        - name: SYSLOG_SERVER
        default: localhost
        ini:
          - section: callback_syslog_json
            key: syslog_server
      port:
        description: Port on which the syslog server is listening.
        env:
          - name: SYSLOG_PORT
        default: 514
        ini:
          - section: callback_syslog_json
            key: syslog_port
      facility:
        description: Syslog facility to log as.
        env:
          - name: SYSLOG_FACILITY
        default: user
        ini:
          - section: callback_syslog_json
            key: syslog_facility
      setup:
        description: Log setup tasks.
        env:
          - name: ANSIBLE_SYSLOG_SETUP
        type: bool
        default: true
        ini:
          - section: callback_syslog_json
            key: syslog_setup
        version_added: 4.5.0
'''

import pdb 
import logging
import logging.handlers

import socket

from ansible.plugins.callback import CallbackBase

def sanitize_task_name(result):
     result.task_name.replace(' ','_')

class CallbackModule(CallbackBase):
    """
    logs ansible-playbook and ansible runs to a syslog server in json format
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    #CALLBACK_NAME = 'community.general.syslog_json'
    CALLBACK_NAME = 'john_syslog_json'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):

        super(CallbackModule, self).__init__()

    def set_options(self, task_keys=None, var_options=None, direct=None):

        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        syslog_host = self.get_option("server")
        syslog_port = int(self.get_option("port"))
        syslog_facility = self.get_option("facility")

        self.logger = logging.getLogger('ansible logger')
        self.logger.setLevel(logging.DEBUG)

        self.handler = logging.handlers.SysLogHandler(
            address=(syslog_host, syslog_port),
            facility=syslog_facility
        )
        self.logger.addHandler(self.handler)
        self.hostname = socket.gethostname()

    def v2_playbook_on_stats(self, stats):
        pass
#        pdb.set_trace()
    def v2_playbook_on_start(self, playbook):
#        pdb.set_trace()
        self.logger.info('%s %s: playbook execution BEGIN', self.hostname, playbook._file_name)
        self.playbookinfo=playbook._file_name
        
    def v2_runner_on_failed(self, result, ignore_errors=False):
#        pdb.set_trace()
        res = result._result
        host = result._host.get_name()
        self.logger.error('%s %s: %s task execution FAILED; host: %s; message: %s', self.hostname, sanitize_task_name(result), self.playbookinfo, host, self._dump_results(res))

    def v2_runner_on_ok(self, result):
#        pdb.set_trace()
        res = result._result
        host = result._host.get_name()
        if result._task.action != "gather_facts" or self.get_option("setup"):
            self.logger.info('%s %s: %s task execution OK; host: %s; message: %s', self.hostname, sanitize_task_name(result), self.playbookinfo, host, self._dump_results(res))

    def v2_runner_on_skipped(self, result):
        host = result._host.get_name()
        self.logger.info('%s %s: %s task execution SKIPPED; host: %s; message: %s', self.hostname, sanitize_task_name(result), self.playbookinfo, host, 'skipped')

    def v2_runner_on_unreachable(self, result):
        res = result._result
        host = result._host.get_name()
        self.logger.error('%s %s: %s task execution UNREACHABLE; host: %s; message: %s', self.hostname, sanitize_task_name(result), self.playbookinfo, host, self._dump_results(res))

    def v2_runner_on_async_failed(self, result):
        res = result._result
        host = result._host.get_name()
        jid = result._result.get('ansible_job_id')
        self.logger.error('%s %s: %s task execution FAILED; host: %s; message: %s', self.hostname, sanitize_task_name(result), self.playbookinfo, host, self._dump_results(res))

    def v2_playbook_on_import_for_host(self, result, imported_file):
        host = result._host.get_name()
        self.logger.info('%s %s: playbook IMPORTED; host: %s; message: imported file %s', self.hostname, sanitize_task_name(result), host, imported_file)

    def v2_playbook_on_not_import_for_host(self, result, missing_file):
        host = result._host.get_name()
        self.logger.info('%s %s: playbook NOT IMPORTED; host: %s; message: missing file %s', self.hostname, sanitize_task_name(result), host, missing_file)
