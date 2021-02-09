#!/usr/bin/env python

import os

from schema import Schema, And, Use
from happi import Client

# Base Schema for IOC generation
# Assumes base pv is given via prefix
base_ioc_schema = Schema({'ioc_engineer': And(str),
                          'ioc_release': And(str),
                          'ioc_location': And(str),
                          'ioc_arch': And(str, lambda s: s in ('linux-x86',
                                                           'linux-x86_64',
                                                           'rhel5-x86_64',
                                                           'rhel7-x86_64')),
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


def make_ell_config(devices, serial=None, location=None):
    """
    Write a Thorlabss Elliptec motor controller configuration file.
    
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
            valid.append(ell_schema.validate(device.metadata))
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
    with open(location+'/'+filename, 'w') as f:
        f.write("RELEASE={}\n".format(valid[0]['ioc_release']))
        f.write("ENGINEER={}\n".format(valid[0]['ioc_engineer']))
        f.write("LOCATION={}\n".format(valid[0]['ioc_location']))
        f.write("IOC_PV=IOC:{}\n".format(valid[0]['ioc_base']))
        f.write("ARCH={}\n".format(valid[0]['ioc_arch']))
        s = 'PORT(BASE="{}",SERIAL="{}",DEBUG=)\n'.format(valid[0]['ioc_base'], 
                                                        serial)
        f.write(s)

        for stage in valid:
            model = stage['ioc_model'].upper()
            f.write("{}(PORT0,ADDRESS={})\n".format(model, stage['ioc_channel']))
            if stage['ioc_alias'] is not None:
                alias_str = 'ALIAS(RECORD="{0}:M{1}",ALIAS="{2}:ELL:M{1}")\n'
                f.write(alias_str.format(stage['ioc_base'],
                                         stage['ioc_channel'],
                                         stage['ioc_alias']))
    return 0


def make_ell_configs(devices, location):
    """
    Function to make all Elliptec configurations found in the given device
    list. Searches through the data for unique serial numbers, then calls
    make_elliptec_config for each unique serial number found.
    """
    serials = []
    for device in devices:
        serials.append(device['ioc_serial'])
    for serial in set(serials):
        print("Writting elliptec configurations to {}".format(location))
        make_ell_config(devices, serial=serial, location=location)


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


def make_qmini_config(device, location=None):
    """
    Write a Broadcom Qseries Spectrometer configuration file.
    
    Arguments
    ---------
    device : happi.SearchResult
        Search result from a Happi database search containing a qmini 
        container.

    location : str
        Directory to write the configuration file to.
    """
    # Compare given metadata against defined schema. Should help guard against
    # empty or mal-formed entries.
    if not qmini_schema.is_valid(device.metadata):
        print("Device config for {} is not valid".format(device['name']))
        return 0

    ## Data seems valid, make the config
    filename = device['ioc_name'] + '.cfg'
    print("Writing {}".format(location+'/'+filename))
    with open(location+'/'+filename, 'w') as f:
        f.write("RELEASE={}\n".format(device['ioc_release']))
        f.write("ARCH={}\n".format(device['ioc_arch']))
        f.write("ENGINEER={}\n".format(device['ioc_engineer']))
        f.write("NAME={}\n".format(device['prefix']))
        f.write("SERIAL={}\n".format(device['ioc_serial']))
        f.write("LOCATION={}\n".format(device['ioc_location']))
        f.write("IOCPVROOT=IOC:{}\n".format(device['prefix']))
        f.write("DEBUG=\n")
        if device['ioc_use_evr'] == 'yes':
            f.write("EVR_PV=EVR:{}\n".format(device['prefix']))
            f.write("EVR_TYPE=SLAC\n")
            f.write("EVR_TRIG={}\n".format(device['ioc_evr_channel']))
            
    return 0

def make_qmini_configs(devices, location):
    """
    Function to make all Qmini configurations found in the given device
    list. 
    """
    for device in devices:
        print("Writting qmini configurations to {}".format(location))
        make_qmini_config(device, location=location)
