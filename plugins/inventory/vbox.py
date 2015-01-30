#!/usr/bin/env python

# This file is part of Ansible,
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import sys
from subprocess import check_output

try:
    import json
except ImportError:
    import simplejson as json


VBOX="VBoxManage"


def get_hosts(host=None):

    returned = {}
    try:
        if host:
            results = check_output([VBOX, 'showvminfo', host])
        else:
            returned = { 'all': set(), '_metadata': {}  }
            results = check_output([VBOX, 'list', '-l', 'vms'])
    except:
        sys.exit(1)

    hostvars = {}
    prevkey = pref_k = ''

    for line in results.splitlines():

        try:
            k,v = line.split(':',1)
        except:
            continue

        if k == '':
            continue

        v = v.strip()
        if k.startswith('Name'):
            if v not in hostvars:
                curname = v
                hostvars[curname] = {}
                try: # try to get network info
                    ip_info = check_output([VBOX, 'guestproperty', 'get', curname,"/VirtualBox/GuestInfo/Net/0/V4/IP"])
                    if 'Value' in ip_info:
                        a,ip = ip_info.split(':',1)
                        hostvars[curname]['ansible_ssh_host'] = ip.strip()
                except:
                    pass

            continue

        if not host:
            if k == 'Groups':
                for group in v.split('/'):
                    if group:
                        if group not in returned:
                            returned[group] = set()
                        returned[group].add(curname)
                    returned['all'].add(curname)
                continue

        pref_k = 'vbox_' + k.strip().replace(' ','_')
        if k.startswith(' '):
            if prevkey not in hostvars[curname]:
                hostvars[curname][prevkey] = {}
            hostvars[curname][prevkey][pref_k]= v
        else:
            if v != '':
                hostvars[curname][pref_k] = v

        prevkey = pref_k

    if not host:
        returned['_metadata']['hostvars'] = hostvars
    else:
        returned = hostvars[host]
    return returned


if __name__ == '__main__':

    inventory = {}
    hostname = None

    if len(sys.argv) > 1:
        if sys.argv[1] == "--host":
            hostname = sys.argv[2]

    if hostname:
        inventory = get_hosts(hostname)
    else:
        inventory = get_hosts()

    import pprint
    print pprint.pprint(inventory)
