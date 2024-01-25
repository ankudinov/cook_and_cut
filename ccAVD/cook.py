from ccAVD.cut import Cut
from ccAVD.tools import smart_update

class Cook(Cut):

    def start(self):
        # start all processing
        self.avd_leaf_uplinks()  # build AVD var for uplinks between leafs and spines
        self.convert_vrfs_vlans()  # convert vrf and vlan CSVs to a format easy to process in J2 template
        self.endpoints()  # convert endpoints

    def avd_leaf_uplinks(self):
        # build AVD variables for uplinks between leafs and spines

        for leaf_inventory, cabling_plan in [
            # if you have more than one leaf inventory and cabling plan, add them here
            ('fabric_leaf_inventory', 'fabric_cabling_plan')
        ]:

            for index, leaf in enumerate(self.cookiecutter_vars['in'][leaf_inventory].copy()):
                leaf_hostname = leaf['hostname']
                all_leaf_hostnames = [a_leaf['hostname'] for a_leaf in self.cookiecutter_vars['in'][leaf_inventory]]
                self.cookiecutter_vars['in'][leaf_inventory][index].update({
                    'uplink_switches': list(),
                    'uplink_switch_interfaces': list(),
                    'uplink_interfaces': list(),
                    'mlag_interfaces': list()
                })
                for a_link in self.cookiecutter_vars['in'][cabling_plan]:
                    if a_link['local_switch'] == leaf_hostname:
                        if a_link['remote_switch'] not in all_leaf_hostnames:
                            self.cookiecutter_vars['in'][leaf_inventory][index]['uplink_switches'].append(a_link['remote_switch'])
                            self.cookiecutter_vars['in'][leaf_inventory][index]['uplink_switch_interfaces'].append('Ethernet' + a_link['remote_interface'][1:])
                            self.cookiecutter_vars['in'][leaf_inventory][index]['uplink_interfaces'].append('Ethernet' + a_link['local_interface'][1:])
                        else:
                            self.cookiecutter_vars['in'][leaf_inventory][index]['mlag_interfaces'].append('Ethernet' + a_link['remote_interface'][1:])
                    elif a_link['remote_switch'] == leaf_hostname:
                        if a_link['remote_switch'] not in all_leaf_hostnames:
                            self.cookiecutter_vars['in'][leaf_inventory][index]['uplink_switches'].append(a_link['local_switch'])
                            self.cookiecutter_vars['in'][leaf_inventory][index]['uplink_switch_interfaces'].append('Ethernet' + a_link['local_interface'][1:])
                            self.cookiecutter_vars['in'][leaf_inventory][index]['uplink_interfaces'].append('Ethernet' + a_link['remote_interface'][1:])
                        else:
                            self.cookiecutter_vars['in'][leaf_inventory][index]['mlag_interfaces'].append('Ethernet' + a_link['local_interface'][1:])

    def convert_vrfs_vlans(self):
        # convert data from VLAN and VRF CSVs to the following format:
        #
        # tenants:
        #   - name: Tenant_A
        #     mac_vrf_vni_base: 10000
        #     vrfs:
        #       - name: Tenant_A_OP_Zone
        #         vrf_vni: 10
        #         vtep_diagnostic:
        #           loopback: 100
        #           loopback_ip_range: 10.255.1.0/24
        #         svis:
        #           - id: 110
        #             name: Tenant_A_OP_Zone_1
        #             tags: [opzone]
        #             enabled: true
        #             ip_address_virtual: 10.1.10.1/24
        #     l2vlans:
        #       - id: 160
        #         name: Tenant_A_VMOTION
        #         tags: [vmotion]

        self.cookiecutter_vars['out'].update({
            'tenants': list()
        })

        for vrf_inventory, vlan_inventory in [
            ('fabric_vrfs', 'fabric_vlans')
        ]:

            tenant_name_set = set([vrf_entry['tenant_name'] for vrf_entry in self.cookiecutter_vars['in'][vrf_inventory]])
            for tenant_name in tenant_name_set:
                tenant_dict = {
                    'name': tenant_name,
                    'vrfs': list(),
                    'l2vlans': list()
                }
                for vrf_entry in self.cookiecutter_vars['in'][vrf_inventory]:
                    smart_update(tenant_dict, 'mac_vrf_vni_base', vrf_entry, 'tenant_mac_vrf_base_vni', mandatory=True, convert_to='int')
                    vrf_dict = {
                        'svis': list()
                    }
                    smart_update(vrf_dict, 'name', vrf_entry, 'ip_vrf_name', mandatory=True)
                    smart_update(vrf_dict, 'vrf_vni', vrf_entry, 'ip_vrf_vni', mandatory=True, convert_to='int')
                    if ('vrf_diagnostic_loopback_number' in vrf_entry.keys()) and ('vrf_diagnostic_loopback_ip_range' in vrf_entry.keys()):
                        smart_update(vrf_dict, 'vtep_diagnostic.vrf_diagnostic_loopback_number', vrf_entry, 'vrf_diagnostic_loopback_number')
                        smart_update(vrf_dict, 'vtep_diagnostic.loopback_ip_range', vrf_entry, 'vrf_diagnostic_loopback_ip_range')

                    for vlan_entry in self.cookiecutter_vars['in'][vlan_inventory]:
                        if (vlan_entry['ip_vrf'] == vrf_entry['ip_vrf_name']) and (vlan_entry['tenant_name'] == tenant_name):
                            vlan_dict = {'enabled': 'true'}  # svi is enabled if defined in CSV
                            smart_update(vlan_dict, 'id', vlan_entry, 'vlan_number', mandatory=True, convert_to='int')
                            smart_update(vlan_dict, 'name', vlan_entry, 'vlan_name', mandatory=True)
                            smart_update(vlan_dict, 'tags', vlan_entry, 'filter_tags')
                            smart_update(vlan_dict, 'ip_address_virtual', vlan_entry, 'ip_virtual_address_and_mask')
                            vrf_dict['svis'].append(vlan_dict)

                    tenant_dict['vrfs'].append(vrf_dict)

                for vlan_entry in self.cookiecutter_vars['in'][vlan_inventory]:
                    l2_vlan_dict = dict()
                    if 'ip_vrf' in vlan_entry.keys():
                        if not vlan_entry['ip_vrf']:
                            smart_update(l2_vlan_dict, 'id', vlan_entry, 'vlan_number', mandatory=True, convert_to='int')
                            smart_update(l2_vlan_dict, 'name', vlan_entry, 'vlan_name', mandatory=True)
                            smart_update(l2_vlan_dict, 'tags', vlan_entry, 'filter_tags')
                            tenant_dict['l2vlans'].append(l2_vlan_dict)

                self.cookiecutter_vars['out']['tenants'].append(tenant_dict)

def endpoints(self):
    # build AVD endpoints

    self.cookiecutter_vars['out'].update({
        'endpoint': list()
    })

    for endpoints_inventory in ['fabric_endpoints']:
        csv_entry_list = self.cookiecutter_vars['in'][endpoints_inventory]
        for csv_entry in csv_entry_list:
            server_name = csv_entry['server_name']
            if server_name not in endpoints.keys():
                endpoints.update({
                    server_name: {
                        'switch_ports': list(),
                        'switches': list()
                    }
                })
            endpoints[server_name]['switch_ports'].append(csv_entry['switch_port'])
            endpoints[server_name]['switches'].append(csv_entry['switch_hostname'])
            # find out if interface is in a port-channel
            if csv_entry['port_channel_mode']:
                endpoints[server_name].update({
                    "port_channel": {
                        "mode": csv_entry['port_channel_mode']
                    }
                })
            # set other parameters
            if csv_entry['switchport_mode']:
                endpoints[server_name].update({
                    "mode": csv_entry['switchport_mode']
                })
            if csv_entry['switchport_vlans']:
                endpoints[server_name].update({
                    "vlans": csv_entry['switchport_vlans']
                })
            if csv_entry['description']:
                endpoints[server_name].update({
                    "description": csv_entry['description']
                })
        # convert endpoints dict to AVD list
        for server,adapters in endpoints.items():
            self.cookiecutter_vars['out']['endpoints'].append({
                "name": server,
                "adapters": [
                    adapters
                ]
            })
