#!/usr/bin/env python

import sys
import os
from jinja2 import Environment, PackageLoader
from happi.containers import registry
from happi import Client
from utils import (make_Makefile, MakeElliptecConfigs, MakeQminiConfigs,
                   MakeBaslerConfigs, MakeThorlabsWfsConfigs,
                   MakeSmarActConfigs)
from pcdsdevices.happi.containers import (Elliptec, Qmini, SmarActMotor,
                                          SmarActTipTiltMotor, ThorlabsWfs,
                                          ThorlabsPM101PowerMeter,
                                          EnvironmentalMonitor, LasBasler)

# Map ioc_types to templates and evaluation functions
dev_map = {'Elliptec': {'template': 'elliptec_template.cfg',
                        'function': MakeElliptecConfigs},
           'Qmini': {'template': 'qmini_template.cfg',
                     'function': MakeQminiConfigs},
           'BaslerGigE': {'template': 'basler_template.cfg',
                         'function': MakeBaslerConfigs},
           'ThorlabsWfs40': {'template': 'wfs40_template.cfg',
                             'function': MakeThorlabsWfsConfigs},
           'SmarAct': {'template': 'smaract_template.cfg',
                       'function': MakeSmarActConfigs}}

def make_tile_configs(tile, directory, dbpath):
    """
    Write TILE IOC configs based on database entries.
    """
    # Hack in our test device types
    registry._registry['pcdsdevices.Elliptec'] = Elliptec
    registry._reverse_registry[Elliptec] = 'pcdsdevices.Elliptec'
    registry._registry['pcdsdevices.Qmini'] = Qmini 
    registry._reverse_registry[Qmini] = 'pcdsdevices.Qmini'
    registry._registry['pcdsdevices.SmarActMotor'] = SmarActMotor
    registry._reverse_registry[SmarActMotor] = 'pcdsdevices.SmarActMotor'
    registry._registry['pcdsdevices.SmarActTipTilt'] = SmarActTipTiltMotor
    registry._reverse_registry[SmarActTipTiltMotor] = \
        'pcdsdevices.SmarActTipTilt'
    registry._registry['pcdsdevices.LasBasler'] = LasBasler
    registry._reverse_registry[LasBasler] = 'pcdsdevices.LasBasler'
    registry._registry['pcdsdevices.ThorlabsWfs40'] = ThorlabsWfs
    registry._reverse_registry[ThorlabsWfs] = 'pcdsdevices.ThorlabsWfs40'
    registry._registry['pcdsdevices.ThorlabsPM101PowerMeter'] = \
        ThorlabsPM101PowerMeter
    registry._reverse_registry[ThorlabsPM101PowerMeter] = \
        'pcdsdevices.ThorlabsPM101PowerMeter'
    registry._registry['pcdsdevices.EnvironmentalMontior'] = \
        EnvironmentalMonitor 
    registry._reverse_registry[EnvironmentalMonitor] = \
        'pcdsdevices.EnvironmentalMonitor'

    # Just use our test devices for now
    if tile not in ['lm1k4_com']:
        raise ValueError("Unrecognized TILE {}".format(tile))

    client = Client(path=dbpath)
    results = client.search(location_group=tile)
    env = Environment(loader=PackageLoader('mods_deploy', 'templates'))
    for dev in dev_map.keys():  # Aggregate devices based on ioc_type
        devs = [result for result in results if dev == result['ioc_type']]
        print("Found {} devices of type {}".format(len(devs), dev))
        if len(devs) > 0:
            template = env.get_template(dev_map[dev]['template'])
            dev_map[dev]['function'](devs, directory, template)
        else:
            print("Skipping device type {}".format(dev))


if __name__ == '__main__':
    # For testing
    db_path = '/cds/home/t/tjohnson/trunk/hutch-python/forks/device_config/db.json'
    tile = sys.argv[1]
    workdir = os.getcwd()+'/test'
    make_Makefile(workdir)
    make_tile_configs(tile, workdir, db_path)
