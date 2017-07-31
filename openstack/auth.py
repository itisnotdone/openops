import os
import sys
from pprint import pprint as pp
from ptpython.repl import embed
from openstack import connection

def init_auth(version=None):
    """Initialize authentication"""
    if version in {None, 3}:
        from keystoneauth1.identity import v3
        auth = v3.Password(
            auth_url=os.environ['OS_AUTH_URL'],
            username=os.environ['OS_USERNAME'],
            password=os.environ['OS_PASSWORD'],
            project_name=os.environ['OS_PROJECT_NAME'],
            project_domain_name=os.environ['OS_PROJECT_DOMAIN_NAME'],
            user_domain_name=os.environ['OS_USER_DOMAIN_NAME']
        )
    elif version == 2:
        from keystoneauth1.identity import v2
        auth = v2.Password(
            auth_url=os.environ['OS_AUTH_URL'],
            username=os.environ['OS_USERNAME'],
            password=os.environ['OS_PASSWORD'],
            tenant_id=os.environ['OS_TENANT_ID']
        )
    else:
        raise ValueError("No such version available.")

    from keystoneauth1 import session
    return session.Session(auth=auth, verify='ca.cert')

def init_openstack():
    conn = connection.Connection(auth_url=os.environ['OS_AUTH_URL'],
                                 project_name=os.environ['OS_PROJECT_NAME'],
                                 username=os.environ['OS_USERNAME'],
                                 password=os.environ['OS_PASSWORD'],
                                 project_domain_name=os.environ['OS_PROJECT_DOMAIN_NAME'],
                                 user_domain_name=os.environ['OS_USER_DOMAIN_NAME'])
    return conn

def init_session(sess, component, version=None):
    """Initialize sessions for each components"""
    if component == 'keystone':
        from keystoneclient.v3 import client
        return client.Client(session=sess)
    elif component == 'nova':
        from novaclient import client
        return client.Client(2, session=sess)
    elif component == 'cinder':
        from cinderclient import client
        return client.Client(2, session=sess)
    elif component == 'glance':
        from glanceclient import Client
        return Client(2, session=sess)
    elif component == 'neutron':
        from neutronclient.v2_0 import client
        return client.Client(session=sess)
    elif component == 'heat':
        from heatclient import client
        return client.Client(1, session=sess)
    else:
        raise ValueError("Invalid value has been assigned.")


