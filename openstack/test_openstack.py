import unittest
from ptpython.repl import embed
import os_scripts as stack
from pprint import pprint as pp

class AssignmentOne(unittest.TestCase):
    def setUp(self):
        print 'Setting up..'
        self.subject = 'pytest'
        self.network_name = self.subject + '_network'
        self.subnet_name = self.subject + '_subnet'
        self.gateway_port_name = self.subject + '_gateway_port'
        self.instance_port_name = self.subject + '_instance_port'
        self.router_name = self.subject + '_router'
        self.instance_name = self.subject + '_instance'

    def test_create_resources(self):
        print 'Creating network..'
        network_body = {
            'network': {
                'name': self.network_name,
                'admin_state_up': True
            }
        }
        network = stack.create_network(network_body)
        self.assertEqual(self.network_name, stack.find_network(self.network_name)['name'])

        print 'Creating subnet..'
        subnet_body = {
            'subnets': [
                {
                    'name': self.subnet_name,
                    'cidr': '192.168.0.0/24',
                    'ip_version': 4,
                    'network_id': network['network']['id']
                }
            ]
        }
        subnet = stack.create_subnet(subnet_body)
        self.assertEqual(self.subnet_name, stack.find_subnet(self.subnet_name)['name'])

        print 'Creating router..'
        router_body = {
            'router': {
                'name': self.router_name,
                'admin_state_up': True
            }
        }
        stack.create_router(router_body)
        router = stack.find_router(self.router_name)
        self.assertEqual(self.router_name, stack.find_router(self.router_name)['name'])

        print 'Creating gateway port..'
        gateway_port_body = {
            'port': {
                'admin_state_up': True,
                'device_id': router['id'],
                'name': self.gateway_port_name,
                'network_id': network['network']['id']
            }
        }
        gateway_port = stack.create_port(gateway_port_body)
        self.assertEqual(self.gateway_port_name, stack.find_port(self.gateway_port_name)['name'])

        print 'Creating instance port..'
        instance_port_body = {
            "port": {
                "admin_state_up": True,
                "name": self.instance_port_name,
                "network_id": network['network']['id']
            }
        }
        instance_port = stack.create_port(instance_port_body)
        self.assertEqual(self.instance_port_name, stack.find_port(self.instance_port_name)['name'])

        print 'Creating keypairs..'
        key = stack.create_keypair(self.subject)
        self.assertEqual(self.subject, stack.find_key(self.subject).name)

        print 'Creating instance..'
        instance = stack.create_instance(
            name = self.instance_name,
            volume_size = 10,
            image_name = stack.find_image('Ubuntu16.04'),
            flavor_name = stack.find_flavor('m1.tiny'),
            key_name = key.name,
            security_group_name = 'default',
            nic = instance_port['port']
        )

        print 'Investigating instance..'
        stack.investigator(instance)

    def tearDown(self):
        print 'Deleting instance..'
        stack.delete_instance(self.instance_name)
        print 'Deleting instance port..'
        stack.delete_port(self.network_name, self.instance_port_name)
        print 'Deleting gateway port..'
        stack.delete_port(self.network_name, self.gateway_port_name)
        print 'Deleting router..'
        stack.delete_router(self.router_name)
        print 'Deleting network..'
        stack.delete_network(self.network_name)
        print 'Deleting keypairs..'
        stack.delete_keypair(self.subject)

if __name__=="__main__":
    unittest.main()

#embed(globals(), locals())

