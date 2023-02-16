import larpix
import larpix.io
import argparse
import time
import json
import os

def datetime_now():
	''' Return string with year, month, day, hour, minute '''
	return time.strftime("%Y_%m_%d_%H_%M_%Z")

def write_config_to_file(c, directory='.', chip_key=None):
    
    path='{}/asic_configs_{}'.format(directory, datetime_now())
    os.mkdir(path)

    chips = []

    if chip_key is None: 
        chips=c.chips
    else:
        chips.append(chip_key)

    for chip in chips:
        with open('config_{}.json'.format(str(chip)), 'w') as f:
            chip_dict = c[chip].config.to_dict()
            chip_dict['CHIP_KEY']=str(chip)
            json.dump( chip_dict , f, indent=4)

    return path

def parse_disabled_dict(disabled_dict):
    channel_masks = {}
    for key in disabled_dict:
        channel_masks[key] = [1 if channel in disabled_dict[key] else 0 for channel in range(64)]
    
    return channel_masks

def parse_disabled_json(disabled_json):

    if not os.path.isfile(disabled_json):
        raise RuntimeError('Disabled list does not exist')

    disabled_list = {}
    with open(disabled_list, 'r') as f: disabled_list=json.load(f)

    channel_masks = {}
    for key in disabled_list:
        channel_masks[key] = [1 if channel in disabled_list[key] else 0 for channel in range(64)]
    
    return channel_masks

def load_config_from_directory(c, directory):
    ''' Load into controller memory all ASIC configuration JSON Files from directory'''
    for file in os.listdir(directory):
        if file[-5:]=='.json':
            load_config_from_file(c, directory+'/'+file)
   
    return c

def load_config_from_file(c, config):
    ''' Load into controller memory an ASIC configuration from JSON File'''

    asic_config={}
    with open(config, 'r') as f: asic_config=json.load(f)

    chip_key = asic_config['CHIP_KEY']

    for key in asic_config.keys():
        if key=='CHIP_KEY': continue
        setattr(c[chip_key].config, key, asic_config[key])

    return c

