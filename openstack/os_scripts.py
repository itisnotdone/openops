import time
import os
import yaml
import collections
from ptpython.repl import embed
from auth import init_auth
from auth import init_session
from pprint import pprint as pp

ss = init_auth(3)

nova = init_session(ss, 'nova')
cinder = init_session(ss, 'cinder')
glance = init_session(ss, 'glance')
neutron = init_session(ss, 'neutron')

def find_image(name):
    images = []
    for i in glance.images.list():
        images.append(i)

    for i in images:
        if i['name'] == name:
            return i['id']

def find_flavor(name):
    return nova.flavors.find(name=name).id

def find_security_group(name):
    return neutron.find_resource(resource='security_group', name_or_id=name)['id']

def find_network(name):
    return neutron.find_resource(resource='network', name_or_id=name)

def find_subnet(name):
    return neutron.find_resource(resource='subnet', name_or_id=name)

def find_router(name):
    return neutron.find_resource(resource='router', name_or_id=name)

def find_port(name):
    return neutron.find_resource(resource='port', name_or_id=name)

def find_key(name):
    return nova.keypairs.find(name=name)

def find_instance(name):
    return nova.servers.find(name=name)

def create_network(body):
    network = neutron.create_network(body=body)
    return network

def create_subnet(body):
    subnet = neutron.create_subnet(body=body)

def delete_network(name):
    neutron.delete_network(find_network(name)['id'])

def create_router(body):
    router = neutron.create_router(body)

def delete_router(name):
    neutron.delete_router(find_router(name)['id'])

def create_port(body):
    return neutron.create_port(body=body)

def delete_port(network_name, name=None):
    if name == None:
        for p in neutron.list_ports(find_network(network_name)['id'])['ports']:
            if p['device_owner'] != 'network:dhcp':
                neutron.delete_port(p['id'])
    else:
        for p in neutron.list_ports(find_network(network_name)['id'])['ports']:
            if p['name'] != 'name':
                neutron.delete_port(p['id'])

def create_keypair(name):
    key = nova.keypairs.create(name)
    key_dir = os.getenv("HOME") + '/.ssh'
    if not os.path.exists(key_dir):
            os.makedirs(key_dir)
    public_key = open(key_dir + '/' + name + '.pub', 'w')
    public_key.write(key.public_key)
    public_key.close()
    private_key = open(key_dir + '/' + name + '.pem', 'w')
    private_key.write(key.private_key)
    private_key.close()
    return key

def delete_keypair(name):
    nova.keypairs.delete(name)
    key_dir = os.getenv("HOME") + '/.ssh'
    public_key = key_dir + '/' + name + '.pub'
    os.remove(public_key)
    private_key = key_dir + '/' + name + '.pem'
    os.remove(private_key)

def create_volume(name, size, image_name):
    volume = cinder.volumes.create(name=name, size=size, imageRef=image_name)
    while True:
        print volume.name + " is being created.."
        time.sleep(1)
        if volume.status == 'available':
            break
        # status does not get changed sometimes somehow..
        volume = cinder.volumes.find(id=volume.id)
    return volume

def create_instance(name, volume_size, image_name, flavor_name, key_name, security_group_name, nic):
    volume = create_volume(name=name, size=volume_size, image_name=image_name)
    instance = nova.servers.create(
        name = name,
        image = image_name,
        flavor = flavor_name,
        key_name = key_name,
        security_groups = [security_group_name],
        nics = [{"port-id": nic['id']}],
        block_device_mapping = {
            'vda': volume.id + ":volume:"+ str(volume.size) +":true"
        }
    )
    while True:
        print instance.name + " is being created.."
        time.sleep(1)
        if instance.status == 'ACTIVE':
            break
        # status does not get changed sometimes somehow..
        instance = nova.servers.find(id = instance.id)
    return instance

def delete_instance(name):
    id = find_instance(name).id
    nova.servers.delete(id)

def investigator(instance):
    instance = instance.to_dict()
    resources = []
    resources.append({"instance": instance})
    resources.append({
        "Flavor": nova.flavors.find(id=instance['flavor']['id']).to_dict()
    })
    resources.append({
        "Image": glance.images.get(instance['image']['id']).__dict__
    })
    resources.append({
        "Volume": cinder.volumes.find(id=instance['os-extended-volumes:volumes_attached'][0]['id']).to_dict()
    })
    resources.append({
        "Security_groups": neutron.find_resource(resource='security_group', name_or_id=instance['security_groups'][0]['name'])
    })
    # TODO: It should be able to find resources based on the instance.
    resources.append({
        "Network": neutron.list_networks()['networks'][0]
    })
    resources.append({
        "Subnet": neutron.list_subnets()['subnets'][0]
    })
    resources.append({
        "DHCP_port": neutron.list_ports()['ports'][0]
    })
    resources.append({
        "Gateway_port": neutron.list_ports()['ports'][1]
    })
    resources.append({
        "Instance_port": neutron.list_ports()['ports'][2]
    })
    file = open('instance.yml', 'w')
    for rsrc in resources:
        file.write("#=======================================================#  ")
        yaml.dump(convert(rsrc), file, default_flow_style=False)

def convert(data):
    if isinstance(data, basestring):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data

#embed(globals(), locals())
