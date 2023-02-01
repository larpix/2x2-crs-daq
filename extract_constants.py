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

def fit_offset(global_thresh, threshold_dicts, tag='', save=''):
    all_offsets = {}
    print('Fitting channel threshold offsets...')
    nmissing=0 
    pbar=tqdm(total=len(threshold_dicts[0].keys()))
    A=[]
    B=[]
    offset = {}
    slope = {}
    plotcount=0
    for channel in threshold_dicts[0].keys():
        if (not sum([channel in ddict.keys() for ddict in threshold_dicts])>=3):# (not channel in pedestal.keys()):
            nmissing+=1
            pbar.update(1)
            continue
        data = []
        xvals=[]
        for i in range(len(threshold_dicts)): 
            if not channel in threshold_dicts[i].keys(): continue
            if threshold_dicts[i][channel][2]>10: continue 
            data.append( convert_mv_to_adc( threshold_dicts[i][channel][0] ) )
            xvals.append(global_thresh[i])
        
        if len(xvals)<4:
            continue
            pbar.update(1)
        params, pcov = curve_fit(line, xvals, data, p0=[25, 6.])
        pbar.update(1)
        
        if plotcount<15:
            xs=np.linspace(min(xvals), max(xvals), 100)
            plotcount+=1
            fig=plt.figure()
            ax=fig.add_subplot()
            ax.set_xlabel('dac value')
            ax.set_ylabel('adc')
            ax.scatter(xvals, data)
            ax.plot(xs, line(xs, params[0], params[1]))
            ax.set_title(tag)

        A.append(params[0])
        B.append(params[1])
        key, chan = chip_key_from_unique(int(channel) )
        if not key in slope.keys(): slope[key]=[-1]*64
        if not key in offset.keys(): offset[key]=[-1]*64
        slope[key][chan]=params[0]
        offset[key][chan]=params[1]
    pbar.close()
    print('missing {} channels'.format(nmissing))
    fig = plt.figure()
    ax = fig.add_subplot()
    ax.hist(A, bins=50, range=(0,10))
    ax.set_title(tag+' Slope')
    ax.set_xlabel('slope [adc/dac]')

    fig = plt.figure()
    ax = fig.add_subplot()
    ax.hist(B, bins=50, range=(-50, 700))
    ax.set_title(tag+' Offset')
    ax.set_xlabel('offset [adc]')
    plt.show()
    
    with open(save+'-offset.json', 'w') as f: json.dump(offset, f)
    with open(save+'-slope.json', 'w') as f: json.dump(slope, f)
    return slope, offset



def main(datadir, pedfile=None, rescan=False):
  
    print('TEST')
    
    if not rescan:

        offset_dicts=[]
        thresh_global=[]

        pt_dicts = []
        pt_val = [] 

        json_files=[]
        all_files=os.listdir(datadir)
        path=datadir
        for file in all_files:
            if file[-5:]=='.json':
                json_files.append(file)
                
        #get tg and ptd from file name
        for file in json_files:
            print(file)
            sp = file.split('-')
            tg=int(sp[2])
            ptd=int(sp[-1].split('.')[0])
            
            if ptd==0:
                d={}
                with open(datadir+'/'+file, 'r') as f: 
                    offset_dicts.append(json.load(f))
                thresh_global.append(tg)

            if tg==100:
                d={}
                with open(datadir+'/'+file, 'r') as f:
                    pt_dicts.append(json.load(f))
                pt_val.append(ptd)


        
        fit_offset(thresh_global, offset_dicts, tag='Global Threshold', save='global_threshold')

        fit_offset(pt_val, pt_dicts, tag='Pixel Trim', save='pixel_trim')

if __name__=='__main__':
    print('TEST')
    if len(sys.argv)==2:
        main(sys.argv[1])
    if len(sys.argv)==3:
        main(sys.argv[1], sys.argv[2])

