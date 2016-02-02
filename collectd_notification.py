#!/usr/bin/env python
# -*- coding: utf-8 -*- vim:fileencoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab

"""
python collectd module for notifications
"""

import collectd
import sys
import time
import pynsca
from pynsca import NSCANotifier
import json
import hashlib

PLUGIN_NAME = 'collectd_notification'

# notitifcation :
# severity => NOTIF_FAILURE || NOTIF_WARNING || NOTIF_OKAY,
# time     => time (),
# message  => 'status message',
# host     => $hostname_g,
# plugin   => 'myplugin',
# type     => 'mytype',
# plugin_instance => '',
# type_instance   => '',
# meta     => [ { name => <name>, value => <value> }, ... ]

# globals
# config from collectd.conf
config = {}
# contains status foreach data
status = []
# status is an array, status_keys has same index as status
# values are uniq keys  : host/plugin-instance/type-instance
status_keys = []

def create_key(notification):
    """Create the key for status_keys from notification
    in: notification
    return: the key
    """
    
    key = notification.host 
    key += '/'
    key += notification.plugin
    if notification.plugin_instance:
        key += '-'
        key += notification.plugin_instance
    
    key += notification.type 
    if notification.type_instance:
        key += '-'
        key += notification.type_instance

    sha = hashlib.sha1()
    sha.update(key)
    return sha.hexdigest()

def create_status_entry(notification, time):
    """ Create a dict from notification
    in: notification and time
    return : dict
    """
    # collectd severity : nagios satus
    #               1   : critical (2)
    #               2   : warning (1)
    #               4   : ok (0)
    severity={ 1:2, 2:1, 4:0 }
 
    return {
        'timestamp': time,
        'host': notification.host,
        'plugin' : notification.plugin,
        'plugin_instance': notification.plugin_instance,
        'type': notification.type,
        'type_instance': notification.type_instance,
        'severity':  notification.severity,
        'nagios_state': severity[notification.severity],
        'message': notification.message
    }

def notification_callback(notification):
    """ callback function
    in: notification
    """

    if notification.host and notification.plugin and notification.type:
        global status
      
        current_time = int(time.time() * 1000)
        key = create_key(notification)
        index = None
        last_severity = None

        if key in status_keys:
            index = status_keys.index(key)
            last_severity = status[index]['severity']
            status[index] = create_status_entry(notification, current_time)
        else:
            status_keys.append(key)
            status.append(create_status_entry(notification,current_time))
            index = len(status) - 1
        
        if config['nsca']:
            send_nsca(status[index])
        if last_severity != status[index]['severity']:
            if config['status']:
                write_status(status)

        

def write_status(status):
    """Write JSON status file
    in: status, the dict of status
    """
    with open(config['status_file'], 'w') as outfile:
            json.dump(status, outfile)

def send_nsca(status):
    """Send a nsca notification
    in: status
    """
    
    nagios_service = status['plugin']
    nagios_service += ':'
    if status['plugin_instance']:
        nagios_service += status['plugin_instance']
    nagios_service += ' '
    nagios_service += status['type']
    if status['type_instance']:
        nagios_service += ' '
        nagios_service += status['type_instance']

    notif = NSCANotifier("localhost")
    notif.svc_result(
        status['host'], 
        nagios_service, 
        status['nagios_state'], 
        status['message']
        )


def configure_callback(data):
    """configure callback function
    set global variable config
    in: configurationdata
    """

    global config
    for child in data.children:
        config[child.key] = child.values[0]

    if 'status_file' not in config:
        config['status_file'] = '/var/lib/collectd/status.json'

collectd.register_config(configure_callback)
#collectd.register_init(init_callback)
collectd.register_notification(notification_callback)
#collectd.register_shutdown(shutdown_callback)

