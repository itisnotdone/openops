#!/usr/bin/env python

# I referred the link below to solve this problem.
# http://alesnosek.com/blog/2015/05/25/openstack-nova-notifications-subscriber/

import sys
import logging as log
from kombu import BrokerConnection
from kombu import Exchange
from kombu import Queue
from kombu.mixins import ConsumerMixin
from ptpython.repl import embed
from pprint import pprint as pp
import pprint
import json
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import yaml

EXCHANGE_NAME="nova"
ROUTING_KEY="notifications.error"
QUEUE_NAME="nova_dump_queue"

with open("env.yml", "r") as stream:
    try:
        env = yaml.load(stream)
    except yaml.YAMLError as e:
        print(e)

BROKER_URI=env['broker_uri']

log.basicConfig(stream=sys.stdout, level=log.DEBUG)

class NotificationsDump(ConsumerMixin):

    def __init__(self, connection):
        self.connection = connection
        return

    def get_consumers(self, consumer, channel):
        exchange = Exchange(EXCHANGE_NAME, type="topic", durable=False)
        queue = Queue(QUEUE_NAME, exchange, routing_key = ROUTING_KEY, durable=False, auto_delete=True, no_ack=True)
        return [ consumer(queue, callbacks = [ self.on_message ]) ]

    def on_message(self, body, message):
        #embed(globals(), locals())
        message = json.loads(body['oslo.message'])
        mail_body = {}
        mail_body['request_id'] = message['_context_request_id']
        mail_body['timestamp'] = message['_context_timestamp']
        mail_body['unique_id'] = message['_unique_id']
        mail_body['event_type'] = message['event_type']
        mail_body['message_id'] = message['message_id']
        mail_body['payload'] = message['payload']
        mail_body['priority'] = message['priority']
        mail_body['publisher_id'] = message['publisher_id']
        mail_body['project_id'] = message['_context_project_id']
        mail_body['project_name'] = message['_context_project_name']
        mail_body['address'] = message['_context_remote_address']
        mail_body['service_catalog'] = message['_context_service_catalog']
        mail_body['user_id'] = message['_context_user_id']
        mail_body['user_name'] = message['_context_user_name']
        pp(mail_body)
        #log.info('Body: %r' % body)
        log.info('--------------------------------------------------------------------------')
        log.info('--------------------------------------------------------------------------')
        log.info('--------------------------------------------------------------------------')
        server = smtplib.SMTP(env['mail']['smtp_server'], 25)
        server.ehlo()
        msg = MIMEMultipart()
        msg['From'] = env['mail']['sender']
        msg['To'] = ", ".join(env['mail']['receiver'])
        msg['Subject'] = "Openstack: Notification"
        body = pprint.pformat(mail_body)
        msg.attach(MIMEText(body, 'plain'))
        #server.starttls()
        #server.login()
        text = msg.as_string()
        server.sendmail(env['mail']['sender'], env['mail']['receiver'], text)

if __name__ == "__main__":
    log.info("Connecting to broker {}".format(BROKER_URI))
    with BrokerConnection(BROKER_URI) as connection:
        NotificationsDump(connection).run()
