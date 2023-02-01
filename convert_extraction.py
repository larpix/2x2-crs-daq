import sys
import numpy as np
import h5py
from matplotlib import pyplot as plt
import os
import json
from tqdm import tqdm
from scipy.optimize import curve_fit

def io_channel_to_tile(io_channel):
    return np.floor((io_channel.astype(int)-1-((io_channel.astype(int)-1)%4))/4+1).astype(int)

def io_channel_to_tile_scalar(io_channel):
    return np.floor((io_channel-1-((io_channel-1)%4))/4+1)

def unique_id(io_group, io_channel, chip_id, channel_id):
    return np.add( np.add(np.add(io_group*1000, 4*io_channel_to_tile(io_channel))*1000,  chip_id)*100, channel_id)

def chip_key_from_unique(unique):
    form='{}-{}-{}'
    
    io_group = iog(unique)
    io_channel = int(4*( io_channel_to_tile_scalar( ioch(unique) )   ))
    chipid=chip_id(unique)

    channel=ch_id(unique)

    return form.format(io_group, io_channel, chipid), channel

def ch_id(unique):
    return np.mod(unique, 100)

def chip_id(unique):
    return (unique//100)%1000

def ioch(unique):
    return ((unique//100)//1000)%1000

def iog(unique):
    return (((unique//100)//1000)//1000)%1000

vcm_dac = 68.
vref_dac = 223.

def convert_adc_to_mv(adc, vref_dac, vcm_dac, vdda=1650):
    vcm = vcm_dac/256*vdda
    vref = vref_dac/256*vdda
    return adc*(vref-vcm)/256 + vcm

def convert_mv_to_adc(mv, vref_dac=vref_dac, vcm_dac=vcm_dac, vdda=1650):
    vcm = vcm_dac/256*vdda
    vref = vref_dac/256*vdda
    return (mv-vcm)*256/(vref-vcm)

def change_vref_vcm(mv, vref_old, vcm_old, vref_new, vcm_new):
    return convert_adc_to_mv(convert_mv_to_adc(mv, vref_old, vcm_old), vref_new, vcm_new)
    
import json

def line(x, a, b):
    return a*x+b

def fit_offset(threshold_dicts, tag='', save=''):
    all_offsets = {}
    nmissing=0 
    pbar=tqdm(total=len(threshold_dicts.keys()))
    slope = {}
    for channel in threshold_dicts.keys():
        data=convert_mv_to_adc( threshold_dicts[channel][0])
        
        key, chan = chip_key_from_unique(int(channel) )
        if not key in slope.keys(): slope[key]=[-1]*64
        slope[key][chan]=data
   
    with open(save+'-converted.json', 'w') as f: json.dump(slope, f)
    return slope



def main(datadir, pedfile=None, rescan=False):
  
    
    if not rescan:
        d={}
        with open(datadir, 'r') as f: d = json.load(f)
        fit_offset(d, tag='tg-100-ptd-0', save='global_threshold')


if __name__=='__main__':
    print('TEST')
    if len(sys.argv)==2:
        main(sys.argv[1])
    if len(sys.argv)==3:
        main(sys.argv[1], sys.argv[2])

