#!/usr/bin/python

# (c) 2017, ne_Sachirou <utakata.c4se@gmail.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

"""A module for argon/mas Mac App Store command-line interface."""

import re
import sys
from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = '''
---
module: osx_mas
short_description: A module for argon/mas Mac App Store command-line interface
version_added: "2.2"
description:
  - A module for argon/mas Mac App Store command-line interface.
options:
  id:
    description:
      - App ID in Mac App Store.
    required: true
    default: None
  state:
    description:
      - State of the app.
    required: false
    default: present
    choices: [ "present", "latest" ]
  account:
    description:
      - Your Apple account ID. This module automatically signin to App Store when necessary.
    required: true
    default: None
  password:
    description:
      - Your Apple account password.
    required: true
    default: None
author:
  - "ne_Sachirou (@ne-sachirou)"
'''
EXAMPLES = '''
# Install the app when it's not present.
- osx_mas: id=1111 state=present account=app@example.com password=PASSWD

# Install the app when it's not present, or update it when it's outdated.
- osx_mas: id=1111 state=latest account=app@example.com password=PASSWD
'''
RETURN = '''
signin:
  description: Returns the account when signin.
  returned: success
  type: string
  sample: "example@example.com"
id:
  description: State after execution.
  returned: success
  type: string
  sample: "1111"
state:
  description: State after execution.
  returned: success
  type: string
  sample: "present"
'''


class OsxMasError(Exception):
    """An error caused by mas command."""

    pass


class OsxMasRunner(object):
    """MAS command wrapper."""

    def signin(self, module):
        """Signin to App Store."""
        params = module.params
        result = module.run_command('mas account')
        if result[0] != 0:
            raise OsxMasError(result[2])
        if result[1].rstrip() == params['account']:
            return None
        if not module.check_mode:
            result = module.run_command('mas', ['signin', params['account'], params['password']])
            if result[0] != 0:
                raise OsxMasError(result[2])
        return params['account']

    def state_present(self, module):
        """Install the app when it's not installed."""
        if self.__is_installed(module, module.params['id']):
            return None
        if not module.check_mode:
            self.__install(module, module.params['id'])
        return 'present'

    def state_latest(self, module):
        """Install or update the app."""
        action = self.state_present(module)
        if action:
            return action
        if self.__is_latest(module, module.params['id']):
            return None
        if not module.check_mode:
            self.__install(module, module.params['id'])
        return 'latest'

    def __is_installed(self, module, app_id):
        result = module.run_command('mas list')
        if result[0] != 0:
            raise OsxMasError(result[2])
        return bool(re.search('^' + app_id + r'\s', result[1], re.M))

    def __is_latest(self, module, app_id):
        result = module.run_command('mas outdated')
        if result[0] != 0:
            raise OsxMasError(result[2])
        return not bool(re.search('^' + app_id + r'\s', result[1], re.M))

    def __install(self, module, app_id):
        result = module.run_command('mas install ' + app_id)
        if result[0] != 0:
            raise OsxMasError(result[2])
        return bool(re.search('^' + app_id + r'\s', result[1], re.M))


class OsxMas(object):
    """OS X mas (Mac App Store command-line interface) module."""

    def __init__(self):
        """Initialize the module."""
        self.__module = AnsibleModule(
            argument_spec=dict(
                id=dict(required=True),
                state=dict(required=False, default='present', choices=['present', 'latest']),
                account=dict(required=True),
                password=dict(required=True),
            ),
            no_log=True,
            supports_check_mode=True
        )

    def run(self):
        """Run this module."""
        mas = OsxMasRunner()
        signin = None
        state = None
        try:
            signin = mas.signin(self.__module)
            if self.__module.params['state'] == 'present':
                state = mas.state_present(self.__module)
            elif self.__module.params['state'] == 'latest':
                state = mas.state_latest(self.__module)
        except Exception:
            self.__module.fail_json(msg=sys.exc_info()[1])
        self.__module.exit_json(
            changed=bool(signin or state),
            signin=signin,
            id=self.__module.params['id'],
            state=state
        )


def main():
    """Main."""
    OsxMas().run()


if __name__ == '__main__':
    main()
