#!/usr/bin/env python

import sys
import os
from happi.containers import registry
from happi import Client
from utils import make_Makefile, make_ell_configs, make_qmini_configs
from pcdsdevices.happi.containers import Elliptec, Qmini

# dev_map map devices to functions 
dev_map = {'pcdsdevices.Elliptec': make_ell_configs,
           'pcdsdevices.Qmini': make_qmini_configs}

def make_tile_configs(tile, directory, dbpath):
    """
    Write TILE IOC configs based on database entries.
    """
    # Hack in our test device types
    registry._registry['pcdsdevices.Elliptec'] = Elliptec
    registry._reverse_registry[Elliptec] = 'pcdsdevices.Elliptec'
    registry._registry['pcdsdevices.Qmini'] = Qmini 
    registry._reverse_registry[Qmini] = 'pcdsdevices.Qmini'

    # Just use our test devices for now
    if tile not in ['lm1k4_com']:
        raise ValueError("Unrecognized TILE {}".format(tile))

    client = Client(path=dbpath)
    results = client.search(location_group=tile)
    for dev in dev_map.keys():  # Aggregate devices based on container type
        devs = [result for result in results if result['type'] == dev]
        print("Found {} devices of type {}".format(len(devs), dev))
        func = dev_map[devs[0]['type']]
        func(devs, directory)


if __name__ == '__main__':
    # For testing
    db_path = '/cds/home/t/tjohnson/trunk/hutch-python/forks/device_config/db.json'
    # Gather information
    tile = sys.argv[1]
    workdir = os.getcwd()+'/test'
    make_Makefile(workdir)
    make_tile_configs(tile, workdir, db_path)
