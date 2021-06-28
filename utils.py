#!/usr/bin/env python

import os

from schema import Schema, And, Use
from happi import Client

# Base Schema for IOC generation
# Assumes base pv is given via prefix
base_ioc_schema = Schema({'ioc_engineer': And(str),
                          'ioc_release': And(str),
                          'ioc_location': And(str),
                          'ioc_arch': And(str,
                                          lambda s: s in
                                              ('linux-x86',
                                               'linux-x86_64',
                                               'rhel5-x86_64',
                                               'rhel7-x86_64',
                                               'rhel7-gcc494-x86_64')),
                          }, ignore_extra_keys=True)


def make_Makefile(location):
    """
    Write a Makefile for our standard templated IOCs to the specified location.
    The specified directory must already exist. 
    """ 
    # Check location for ending '/' and remove if it exists
    while(location.endswith('/')):
        location = location[:-1]

    filename = '/Makefile'

    if os.path.isfile(location+filename):
        # File exists, so return
        print("Found Makefile in {}. Continuing...".format(location))
        return 0
    else: # We need to make the file
        with open(location+filename, 'w') as f:
            f.write("# SLAC PCDS Makefile for building templated IOC instances\n")
            f.write("IOC_CFG  += $(wildcard *.cfg)\n")
            f.write("include /reg/g/pcds/controls/macro/RULES_EXPAND\n")
            return 0

ell_schema = Schema({**base_ioc_schema.schema,
                     'ioc_channel': And(str,
                                    lambda s: s.lower() in ('1', '2', '3', '4',
                                                            '5', '6', '7', '8',
                                                            '9', 'a', 'b', 'c',
                                                            'd', 'e', 'f')),
                     'prefix': And(str),
                     'ioc_serial': And(str),
                     'ioc_base': And(str),
                     'ioc_alias': And(str),
                     'ioc_name': And(str),
                     'ioc_model': And(str,
                                      lambda s: s.lower() in ('ell6', 'ell9',
                                                              'ell14', 'ell18', 
                                                              'ell20'))
                    }, ignore_extra_keys=True)


def MakeElliptecConfig(devices, serial, location, template):
    """
    Write a Thorlabs Elliptec motor controller configuration file.
    
    Arguments
    ---------
    devices : list of happi.SearchResult
        List of devices from a Happi database search

    serial : str
        Serial number for the Elliptec controller. 

    location : str
        Directory to write the configuration file to.
    """
    # Compare given metadata against defined schema. Should help guard against
    # empty or mal-formed entries.
    valid = []
    for device in devices:
        if device['ioc_serial'] == serial:
            try:
                valid.append(ell_schema.validate(device.metadata))
            except Exception as e:
                print("Found execption with device {}".format(device['name']))
                print(e)
    if len(valid) == 0:
        print("No valid configs for serial {} found".format(serial))
        return 0

    # Do some more data validation; check for inconsistencies
    channels = [d['ioc_channel'] for d in valid]
    if len(channels) > len(set(channels)):  # Check for duplicates
        raise ValueError("Multiple identical channels for controller"
                         " serial number {}".format(serial))
    common = ['ioc_release', 'ioc_base', 'ioc_arch', 'ioc_name']
    for field in common:
        vals = []
        for v in valid:
            vals.append(v[field])
        if len(set(vals)) > 1:
            err = "Multiple values for field {} detected".format(field)
            raise ValueError(err)

    # Data seems valid, make the config
    filename = valid[0]['ioc_name'] + '.cfg'
    print("Writing {}".format(location+'/'+filename))
    conf = template.render(devs=devices)
    with open(location+'/'+filename, 'w') as f:
        f.write(conf)
    return 0


def MakeElliptecConfigs(devices, location, template):
    """
    Function to make all Elliptec configurations found in the given device
    list. Searches through the data for unique serial numbers, then calls
    make_elliptec_config for each unique serial number found.
    """
    serials = []
    for device in devices:
        serials.append(device['ioc_serial'])
    for serial in set(serials):
        print("Writing elliptec configurations to {}".format(location))
        MakeElliptecConfig(devices, serial, location, template)


qmini_schema = Schema({**base_ioc_schema.schema,
                       'prefix': And(str),
                       'ioc_serial': And(str),
                       'ioc_name': And(str),
                       'ioc_use_evr': And(str, Use(str.lower),
                                          lambda s: s in ('yes', 'no')),
                       'ioc_evr_channel': And(str, Use(str.upper),
                                             lambda s: s in ('0', '1', '2',
                                                             '3', '4', '5', 
                                                             '6', '7', '8',
                                                             '9', 'A', 'B')),
                      }, ignore_extra_keys=True)


def MakeQminiConfig(device, location, template):
    """
    Write a Broadcom Qseries Spectrometer configuration file.
    
    Arguments
    ---------
    device : happi.SearchResult
        Search result from a Happi database search containing a qmini 
        container.

    location : str
        Directory to write the configuration file to.

    template: Jinja2 template
        Template used to create the configuration file.
    """
    # Compare given metadata against defined schema. Should help guard against
    # empty or mal-formed entries.
    try:
        qmini_schema.validate(device.metadata)
    except Exception as e:
        print("Found execption with device {}".format(device['name']))
        print(e)
        return 0
    # Data seems valid, make the config
    filename = device['ioc_name'] + '.cfg'
    print("Writing {}".format(location+'/'+filename))
    conf = template.render(device=device)
    with open(location+'/'+filename, 'w') as f:
        f.write(conf)
    return 0


def MakeQminiConfigs(devices, location, template):
    """
    Function to make all Qmini configurations found in the given device
    list. 
    """
    for device in devices:
        print("Writing qmini configurations to {}".format(location))
        MakeQminiConfig(device, location, template)


basler_schema = Schema({**base_ioc_schema.schema,
                       'prefix': And(str),
                       'ioc_name': And(str),
                       'ioc_use_evr': And(str, Use(str.lower),
                                          lambda s: s in ('yes', 'no')),
                       'ioc_evr_channel': And(str, Use(str.upper),
                                             lambda s: s in ('0', '1', '2',
                                                             '3', '4', '5', 
                                                             '6', '7', '8',
                                                             '9', 'A', 'B')),
                       'ioc_cam_model': And(str),
                       'ioc_ip': And(str),
                       'ioc_net_if': And(str),
                       'ioc_net_if_num': And(str),
                       'ioc_http_port': And(str)
                      }, ignore_extra_keys=True)


def MakeBaslerConfig(device, location, template):
    """
    Write a Basler camera configuration file.
    
    Arguments
    ---------
    device : happi.SearchResult
        Search result from a Happi database search containing a qmini 
        container.

    location : str
        Directory to write the configuration file to.

    template: Jinja2 template
        Template used to create the configuration file.
    """
    # Compare given metadata against defined schema. Should help guard against
    # empty or mal-formed entries.
    try:
        basler_schema.validate(device.metadata)
    except Exception as e:
        print("Found execption with device {}".format(device['name']))
        print(e)
        return 0
    # Data seems valid, make the config
    filename = device['ioc_name'] + '.cfg'
    print("Writing {}".format(location+'/'+filename))
    conf = template.render(device=device)
    with open(location+'/'+filename, 'w') as f:
        f.write(conf)
    return 0


def MakeBaslerConfigs(devices, location, template):
    """
    Function to make all Basler configurations found in the given device
    list. 
    """
    for device in devices:
        print("Writing Basler configurations to {}".format(location))
        MakeBaslerConfig(device, location, template)

thorlabs_wfs_schema = Schema({**base_ioc_schema.schema,
                              'prefix': And(str),
                              'ioc_name': And(str),
                              'ioc_use_evr': And(str, Use(str.lower),
                                                 lambda s: s in ('yes', 'no')),
                              'ioc_evr_channel': And(str, Use(str.upper),
                                                    lambda s: s in
                                                        ('0', '1', '2',
                                                         '3', '4', '5', 
                                                         '6', '7', '8',
                                                         '9', 'A', 'B')),
                              'ioc_model': And(str),
                              'ioc_id_num': And(str),
                              'ioc_lenslet_pitch': And(str),
                             }, ignore_extra_keys=True)


def MakeThorlabsWfsConfig(device, location, template):
    """
    Write a Thorlabs WFS configuration file.
    
    Arguments
    ---------
    device : happi.SearchResult
        Search result from a Happi database search containing a qmini 
        container.

    location : str
        Directory to write the configuration file to.

    template: Jinja2 template
        Template used to create the configuration file.
    """
    # Compare given metadata against defined schema. Should help guard against
    # empty or mal-formed entries.
    try:
        thorlabs_wfs_schema.validate(device.metadata)
    except Exception as e:
        print("Found execption with device {}".format(device['name']))
        print(e)
        return 0
    # Data seems valid, make the config
    filename = device['ioc_name'] + '.cfg'
    print("Writing {}".format(location+'/'+filename))
    conf = template.render(device=device)
    with open(location+'/'+filename, 'w') as f:
        f.write(conf)
    return 0


def MakeThorlabsWfsConfigs(devices, location, template):
    """
    Function to make all Thorlabs WFS configurations found in the given device
    list. 
    """
    for device in devices:
        print("Writing Thorlabs WFS configurations to {}".format(location))
        MakeThorlabsWfsConfig(device, location, template)


smaract_schema = Schema({**base_ioc_schema.schema,
                         'prefix': And(str),
                         'ioc_ip': And(str),
                         'ioc_base': And(str),
                         'ioc_name': And(str),
                         'ioc_channel': And(str),
                         'ioc_alias': And(str),
                         'type': And(str)
                        }, ignore_extra_keys=True)

smaract_tt_schema = Schema({**base_ioc_schema.schema,
                            'prefix': And(str),
                            'ioc_ip': And(str),
                            'ioc_base': And(str),
                            'ioc_name': And(str),
                            'ioc_tilt_channel': And(str),
                            'ioc_tip_channel': And(str),
                            'ioc_tilt_suffix': And(str),
                            'ioc_tip_suffix': And(str),
                            'ioc_alias': And(str),
                            'type': And(str)
                           }, ignore_extra_keys=True)


def MakeSmarActConfig(devices, ip, location, template):
    """
    Write a motor SmarAct motor controller configuration file.
    
    Arguments
    ---------
    devices : list of happi.SearchResult
        List of devices from a Happi database search

    ip : str
        IP address (usually a netconfig entry name) for the controller.

    location : str
        Directory to write the configuration file to.

    template: Jinja2 template
        Template to apply to the device data. 
    """
    # Compare given metadata against defined schema. Should help guard against
    # empty or mal-formed entries.
    valid = []
    for device in devices:
        if device['ioc_ip'] == ip:
            if device['type'] == 'pcdsdevices.SmarActMotor':
                try:
                    valid.append(smaract_schema.validate(device.metadata))
                except Exception as e:
                    print("Found execption with device {}".format(device['name']))
                    print(e)
            elif device['type'] == 'pcdsdevices.SmarActTipTilt':
                try:
                    valid.append(smaract_tt_schema.validate(device.metadata))
                except Exception as e:
                    print("Found execption with device {}".format(device['name']))
                    print(e)
            else:
                print("Device {} is not a recognized SmarAct type.".format(device['name']))
    if len(valid) == 0:
        print("No valid configs for ip {} found".format(ip))
        return 0

    # Do some more data validation; check for inconsistencies
    channels = [d['ioc_channel'] for d in valid if d['type'] == 'SmarActMotor']
    channels += [d['ioc_tip_channel'] for d in valid if d['type'] == 'SmarActTipTilt']
    channels += [d['ioc_tilt_channel'] for d in valid if d['type'] == 'SmarActTipTilt']
    if len(channels) > len(set(channels)):  # Check for duplicates
        raise ValueError("Multiple identical channels for controller"
                         " ip address {}".format(ip))
    common = ['ioc_release', 'ioc_base', 'ioc_arch', 'ioc_name']
    for field in common:
        vals = []
        for v in valid:
            vals.append(v[field])
        if len(set(vals)) > 1:
            err = "Multiple values for field {} detected".format(field)
            raise ValueError(err)

    # Data seems valid, make the config
    filename = valid[0]['ioc_name'] + '.cfg'
    print("Writing {}".format(location+'/'+filename))
    conf = template.render(devs=devices)
    with open(location+'/'+filename, 'w') as f:
        f.write(conf)
    return 0


def MakeSmarActConfigs(devices, location, template):
    """
    Function to make all SmarAct configurations found in the given device
    list. Searches through the data for unique serial numbers, then calls
    MakeSmarActConfig for each unique controller ip number found.
    """
    ips = []
    for device in devices:
        ips.append(device['ioc_ip'])
    for ip in set(ips):
        print("Writing SmarAct configurations to {}".format(location))
        MakeSmarActConfig(devices, ip, location, template)


env_monitor_schema = Schema({**base_ioc_schema.schema,
                             'prefix': And(str),
                             'ioc_ip': And(str),
                             'ioc_base': And(str),
                            }, ignore_extra_keys=True)

el3174aich_schema = Schema({**base_ioc_schema.schema,
                        **env_monitor_schema,
                        'ioc_card_num': And(str),
                        'ioc_chan_num': And(str),
                        'ioc_alias': And(str)
                       }, ignore_extra_keys=True)

def MakeEk9000Config(devices, ip, location, template):
    """
    Write a EK9000 controller configuration file.
    
    Arguments
    ---------
    devices : list of happi.SearchResult
        List of devices from a Happi database search

    ip : str
        IP address (usually a netconfig entry name) for the controller.

    location : str
        Directory to write the configuration file to.

    template: Jinja2 template
        Template to apply to the device data. 
    """
    # Compare given metadata against defined schema. Should help guard against
    # empty or mal-formed entries.
    valid = []
    for device in devices:
        if device['ioc_ip'] == ip:
            if device['device_class'] == 'pcdsdevices.EnvironmentalMonitor':
                try:
                    valid.append(env_monitor_schema.validate(device.metadata))
                except Exception as e:
                    print("Found execption with device {}".format(device['name']))
                    print(e)
            elif device['device_class'] == 'pcdsdevices.El3174AiCh':
                try:
                    valid.append(el3174aich_schema.validate(device.metadata))
                except Exception as e:
                    print("Found execption with device {}".format(device['name']))
                    print(e)
            else:
                print("Device {} is not a recognized EK9000 type.".format(device['name']))
    if len(valid) == 0:
        print("No valid configs for ip {} found".format(ip))
        return 0

    # Do some more data validation; check for inconsistencies
    terms = {}
    for dev in valid:
    if dev['device_class'] == 'pcdsdevices.EnvironmentalMonitor':
        # It is assumed that in the laser system the environmental monitors
        # take up the first three connections of the first card.
        terms[1]: {'type': 'EL3174', 
                   'channels': '4', 
                   1: d['ioc_base'] + ':TEMP',
                   2: d['ioc_base'] + ':PRESS',
                   3: d['ioc_base'] + ':HUMID'}
    elif dev['device_class'] == 'pcdsdevices.El3174AiCh': 
        terms[dev['ioc_card_num']]['type'] = 'EL3174'
        terms[dev['ioc_card_num']]['channels'] = '4'
        terms[dev['ioc_card_num']][dev['ioc_chan_num']] = dev['ioc_alias']
    else:
        print("Skipping unrecognized device {}.".format(dev['device_class'])

    #TODO: add more data checking
    common = ['ioc_release', 'ioc_base', 'ioc_arch', 'ioc_name']
    for field in common:
        vals = []
        for v in valid:
            vals.append(v[field])
        if len(set(vals)) > 1:
            err = "Multiple values for field {} detected".format(field)
            raise ValueError(err)

    # Data seems valid, make the config
    filename = valid[0]['ioc_name'] + '.cfg'
    print("Writing {}".format(location+'/'+filename))
    conf = template.render(devs=terms)
#    with open(location+'/'+filename, 'w') as f:
#        f.write(conf)
    return 0


def MakeEk9000Configs(devices, location, template):
    """
    Function to make all EK9000 configurations found in the given device
    list. Searches through the data for unique serial numbers, then calls
    MakeSmarActConfig for each unique controller ip number found.
    """
    ips = []
    for device in devices:
        ips.append(device['ioc_ip'])
    for ip in set(ips):
        print("Writing EK9000 configurations to {}".format(location))
        MakeEk9000Config(devices, ip, location, template)
