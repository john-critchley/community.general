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
      - This plugin logs ansible-playbook summary to a syslog server.
      - Before Ansible 2.9 only environment variables were available for configuration.
    options:
      server:
        description: Syslog server that will receive the event.
        env:
        - name: SYSLOG_SERVER
        default: localhost
        ini:
          - section: callback_syslog_summary
            key: syslog_server
      port:
        description: Port on which the syslog server is listening.
        env:
          - name: SYSLOG_PORT
        default: 514
        ini:
          - section: callback_syslog_summary
            key: syslog_port
      facility:
        description: Syslog facility to log as.
        env:
          - name: SYSLOG_FACILITY
        default: user
        ini:
          - section: callback_syslog_summary
            key: syslog_facility
      setup:
        description: Log setup tasks.
        env:
          - name: ANSIBLE_SYSLOG_SETUP
        type: bool
        default: true
        ini:
          - section: callback_syslog_summary
            key: syslog_setup
        version_added: 4.5.0
'''

import pdb 
import logging
import logging.handlers

import sys
import os

import socket

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    """
    logs ansible-playbook summary to a syslog server
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'syslog_summary'
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

    def _parent_has_callback(self):
        return hasattr(super(CallbackModule, self), sys._getframe(1).f_code.co_name)


    def v2_playbook_on_start(self, playbook):
        self._syslog_summary_playbook = playbook

        if self._parent_has_callback():
            super(CallbackModule, self).v2_playbook_on_start(playbook)

    def v2_playbook_on_stats(self, stats):
        """Log info about playbook statistics."""
        # pdb.set_trace()
        # self.printed_last_task = False

        hosts = sorted(stats.processed.keys())
        playbook=os.path.join(self._syslog_summary_playbook._basedir, self._syslog_summary_playbook._file_name)

        for host in hosts:
            s0 = stats.summarize(host)
            if not 's' in locals():
                s={'ok':s0['ok'], 'changed':s0['changed'], 'failures':s0['failures'], 'unreachable':s0['unreachable'], 'rescued':s0['rescued'], 'ignored':s0['ignored']}
            else:
                for k in s.keys():
                    s[k]+=s0[k]

        if s['failures'] or s['unreachable']:
          self.logger.error('%s : FAIL : ok=%s, changed=%s, failed=%s, unreachable=%s, rescued=%s, ignored=%s', playbook, s['ok'], s['changed'], s['failures'], s['unreachable'], s['rescued'], s['ignored'])
        else:
          self.logger.info('%s : OK: ok=%s, changed=%s, failed=%s, unreachable=%s, rescued=%s, ignored=%s', playbook, s['ok'], s['changed'], s['failures'], s['unreachable'], s['rescued'], s['ignored'])

        if self._parent_has_callback():
            super(CallbackModule, self).v2_playbook_on_stats(stats)
