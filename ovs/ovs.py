from subprocess import Popen, PIPE
import re

def clean_ovs():
    """ It finds and deletes unused virtual network interfaces such as veth and vnet.
        Now, it is only able to work with Openvswitch.
    """

    (list_br_stdout, list_br_error) = Popen(["sudo", "ovs-vsctl", "list-br"], stdout=PIPE).communicate()
    br_list = []
    for line in list_br_stdout.splitlines():
        br_list.append(line)

    (ip_link_stdout, ip_link_error) = Popen(["ip", "link"], stdout=PIPE).communicate()
    ifaces_being_used = []
    for line in ip_link_stdout.splitlines():
        if re.search("veth", line):
            ifaces_being_used.append(line.split(':')[1].strip().split('@')[0])
        if re.search("vnet", line):
            ifaces_being_used.append(line.split(':')[1].strip())


    ports_listed_in_ovs = []
    for br in br_list:
        (list_ports_stdout, list_ports_error) = Popen(["sudo", "ovs-vsctl", "list-ports", br], stdout=PIPE).communicate()
        for port in list_ports_stdout.splitlines():
            if re.search("veth|vnet", port):
                ports_listed_in_ovs.append([br, port])

    for port in ports_listed_in_ovs:
        isexisting = False
        for iface in ifaces_being_used:
            if port[1] == iface:
                print("{} exists.".format(port))
                isexisting = True
                break
        if not isexisting:
            print("Deleting {}...".format(port[1]))
            (del_port_stdout, del_port_error) = Popen(["sudo", "ovs-vsctl", "del-port", port[0], port[1]], stdout=PIPE).communicate()
            #print(del_port_stdout)

if __name__ == "__main__":
    clean_ovs()
