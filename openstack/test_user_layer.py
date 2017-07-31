from auth import init_auth
from auth import init_session
from auth import init_openstack
import time
import json
from ptpython.repl import embed
import unicodedata
import yaml
import subprocess
import logging



#log
logging.basicConfig(filename='logfile.log', level=logging.DEBUG)
def listing_host(nova):
    host_list = nova.hosts.list()
    host_info = []
    for host in host_list:
        if host.zone.encode('ascii','ignore') == "internal":
            continue
        h = (host.zone+":"+host.host_name)
        host_info.append(h)
    return host_info

def create_server(nova, conn, host_info, cfg):
    i = 1
    server_list = []
    for host in host_info:
        server = nova.servers.create(name = 'maintenance_test'+`i`, image = cfg['openstack']['image_id'], flavor = cfg['openstack']['flavor_id'], availability_zone = host, key_name = cfg['openstack']['key_name'])
        server_list.append(server)
        i += 1

        print server.id + " is creating"

    time.sleep(60)
    return server_list

def delete_server(conn, server_list):
    for server in server_list:
        conn.compute.delete_server(server = server.id)

def delete_floatingip_port(conn, port_list):
    for port in port_list:
        conn.network.delete_ip(floating_ip = port.id)

def attach_floatingip(conn, server_list, cfg):
    floatingip_port_list = []
    for server in server_list:
        port = conn.network.create_ip(floating_network_id = cfg['openstack']['public_network_id'])
        conn.compute.add_floating_ip_to_server(server = server.id, address = port.floating_ip_address)
        floatingip_port_list.append(port)
    return floatingip_port_list

def get_stdout_from_cmd(cmd):
        try:
                return subprocess.check_output(cmd.split(' '),True).rstrip()
        except:
                return "error"
                pass

def fping_cmd(ip):
        ping_cmd = "fping "+ip
        return get_stdout_from_cmd("fping "+ip)


def ping(port_list):
    try:
        logging.debug('we are in ping loop')
        for port in port_list:
            logging.info('enter into the first statement')
            h_result=fping_cmd(port.floating_ip_address)
            if h_result=="error":
                    print (port.floating_ip_address+" "+h_result)
            print (h_result)
    except Exception, e:
        print e




def main():
    with open("config.yml", 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    ss = init_auth(3)
    heat = init_session(ss, 'heat')
    nova = init_session(ss, 'nova')
    neutron = init_session(ss, 'neutron')
    conn = init_openstack()
    embed(globals(), locals())

    host_info=listing_host(nova)
    server_list = create_server(nova, conn, host_info, cfg)
    port_list = attach_floatingip(conn, server_list, cfg)
    ping(port_list)
    delete_floatingip_port(conn, port_list)
    delete_server(conn=conn, server_list=server_list)

#    ping(server_info)





if __name__ == "__main__":
    main()
