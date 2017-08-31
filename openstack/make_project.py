import argparse
import yaml
from auth import init_openstack
from auth import init_session
from auth import init_auth
from ptpython.repl import embed
import logging

logging.basicConfig(filename = 'create_project_logfile.log', level = logging.DEBUG)


QUOTA_DEFAULT_INSTANCE = 20
QUOTA_DEFAULT_CORES = 50
QUOTA_DEFAULT_FLOATING_IP = 50
QUOTA_DEFAULT_GIGABYTES = 5000
QUOTA_DEFAULT_VOLUMES = 100
QUOTA_DEFAULT_KEY_PAIRS = 100
QUOTA_DEFAULT_RAM = 51200
QUOTA_DEFAULT_SECGROUP_RULE = 100
QUOTA_DEFAULT_SECGROUPS = 10

NETWORK_RANGE = "192.168.0.0/24"
NETWORK_GATEWAY = "192.168.0.1"
DEFAULT_DNS = "8.8.8.8"


class Makeproject:
    def __init__(self):
        try:
            logging.info('Init quota setting config')
            with open("config.yml",'r') as ymlfile:
                cfg = yaml.load(ymlfile)
            self.router_body = {
                'network_id' : cfg['openstack']['public_network_id'],
                'enable_snat' : True
            }
            self.domain_id = cfg["openstack"]["domain_id"]
            self.public_network_id = cfg["openstack"]["public_network_id"]
            self.admin_users = cfg["openstack"]["admin_users"]
            self.quota_instance = QUOTA_DEFAULT_INSTANCE
            self.quota_cores = QUOTA_DEFAULT_CORES
            self.quota_floatingip = QUOTA_DEFAULT_FLOATING_IP
            self.quota_gigabytes = QUOTA_DEFAULT_GIGABYTES
            self.quota_volumes = QUOTA_DEFAULT_VOLUMES
            self.quota_key_pairs = QUOTA_DEFAULT_KEY_PAIRS
            self.quota_ram = QUOTA_DEFAULT_RAM
            self.quota_secgroup_rule = QUOTA_DEFAULT_SECGROUP_RULE
            self.quota_sercgroups = QUOTA_DEFAULT_SECGROUPS
            ss = init_auth(3)
            self.conn = init_openstack()
            self.nova = init_session(ss,'nova')
            self.cinder = init_session(ss,"cinder")
            self.neutron = init_session(ss,"neutron")
            self.keystone = init_session(ss,"keystone")
        except Exception, e:
            logging.error('Init quota config failed'+str(e))
            

    def Create_project(self, project_name, project_description ):
        try:
            logging.info('Create project')
            identity = self.conn.identity
            project_obj = identity.create_project(name = project_name, description = project_description, domain_id = self.domain_id)
            return project_obj
        except Exception, e:
            logging.error('Create project failed'+str(e))

    def Insert_rule(self, id, users_name = None, group_name = None):
        try:
            identity = self.conn.identity
            user_role_id = identity.find_role(name_or_id = "user").id
            admin_role_id = identity.find_role(name_or_id = "admin").id
            admin_user_list = []
            admin_user_list = self.admin_users.split(',')
            for admin_user in admin_user_list:
                user_id = identity.find_user(name_or_id = admin_user).id
                self.keystone.roles.grant(admin_role_id, user = user_id, project = id)

            embed(globals(), locals())
            if(users_name == None):
                group_obj = identity.find_group(name_or_id = group_name)
                self.keystone.roles.grant(admin_role_id, group = group_id, project = id)
            elif(group_name == None):
                user_name_list = []
                user_name_list = users_name.split(',')
                for user_name in user_name_list:
                    user_id = identity.find_user(name_or_id = user_name).id
                    self.keystone.roles.grant(admin_role_id, user = user_id, project = id)
            else:
                logging.error('Insert_rule variable was not inputed')
                exit(1)
        except Exception, e:
            logging.error('While insert role'+str(e))

    def Set_quota_project(self, id, instances = None , cores = None, ram = None, floating_ips = None, gigabytes = None, key_pairs = None):
        resources = {}	
	if instances is not None:
            resources['instances'] = instances
        else:
            resources['instances'] = None
        if cores is not None:
            resources['cores'] = cores
        else:
            resources['cores'] = None
        if ram is not None:
            resources['ram'] = ram
        else:
            resources['ram'] = None
        if key_pairs is not None:
            resources['key_pairs'] = key_pairs
        else:
            resources['key_pairs'] = None
        if floating_ips is not None:
            resources['floating_ips'] = floating_ips
        else:
            resources['floating_ips'] = None
        if gigabytes is not None:
            resources['gigabytes'] = gigabytes
        else:
            resources['gigabytes'] = 5000
        self.nova.quotas.update(id, instances = resources['instances'], cores = resources['cores'], ram = resources['ram'], key_pairs = resources['key_pairs'], 
                                floating_ips = resources['floating_ips'])
        self.cinder.quotas.update(id, gigabytes = resources['gigabytes'])

    def Create_network(self, project_name, project_id):
        network_body = {'name':project_name+'_network', 'tenant_id': project_id}
	router = self.conn.network.create_router(name = project_name+"_dvr_router", project_id = project_id)
        network = self.neutron.create_network({'network':network_body})
        subnet_body = {'subnets': [{'ip_version': 4, 'network_id': network['network']['id'], 'cidr': NETWORK_RANGE}]}
	subnet = self.neutron.create_subnet(subnet_body)
        self.neutron.add_gateway_router(router.id, self.router_body)
        subnet_body_id = {}
        subnet_body_id['subnet_id'] = subnet['subnets'][0]['id']
        self.neutron.add_interface_router(router.id, subnet_body_id)

def parse_args():
    parser = argparse.ArgumentParser(
        description="create_project")
    parser.add_argument('--project_name')
    parser.add_argument('--project_description')
    parser.add_argument('--users', nargs = '?')
    parser.add_argument('--groups', nargs = '?')
    parser.add_argument('--instances', nargs = '?')
    parser.add_argument('--cores', nargs = '?')
    parser.add_argument('--ram', nargs = '?')
    parser.add_argument('--floating_ips')
    parser.add_argument('--gigabytes')
    parser.add_argument('--key_pairs')
    return parser.parse_args()






def main():
    arg = parse_args()
    m_project = Makeproject()
    project_obj = m_project.Create_project(arg.project_name, arg.project_description)
    project_id = project_obj.id
    project_name = project_obj.name
    m_project.Insert_rule(project_id, arg.users, arg.groups)
    m_project.Set_quota_project(id = project_id, instances = arg.instances , cores = arg.cores, ram = arg.ram, floating_ips = arg.floating_ips, gigabytes = arg.gigabytes, key_pairs = arg.key_pairs)
    m_project.Create_network(project_name, project_id)

if __name__ == "__main__":
    main()







