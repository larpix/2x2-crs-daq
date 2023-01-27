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

def unique_id(io_group, io_channel, chip_id, channel_id):
    return np.add( np.add(np.add(io_group*1000, 4*io_channel_to_tile(io_channel))*1000,  chip_id)*100, channel_id)

def ch_id(unique):
    return np.mod(unique, 100)

def chip_id(unique):
    return (unique//100)%1000

vcm_dac = 50.
vref_dac = 185.

def convert_adc_to_mv(adc, vref_dac, vcm_dac, vdda=1650):
    vcm = vcm_dac/256*vdda
    vref = vref_dac/256*vdda
    return adc*(vref-vcm)/256 + vcm

def convert_mv_to_adc(mv, vref_dac, vcm_dac, vdda=1650):
    vcm = vcm_dac/256*vdda
    vref = vref_dac/256*vdda
    return (mv-vcm)*256/(vref-vcm)

def change_vref_vcm(mv, vref_old, vcm_old, vref_new, vcm_new):
    return convert_adc_to_mv(convert_mv_to_adc(mv, vref_old, vcm_old), vref_new, vcm_new)
    
import json

def get_channel_dict(filename, vref_dac=vref_dac, vcm_dac=vcm_dac, plot=False, tag=''):
    ntrigs = []
    print('Analyzing {}...'.format(filename))
    with h5py.File(filename) as f:
        count = 0
        packets = f['packets']
        ppackets = packets[ packets['channel_id'] < 64 ]
        ppackets = ppackets[ np.logical_and(ppackets['chip_id'] < 111, ppackets['chip_id'] > 10) ]
        #ppackets = ppackets[np.logical_and(ppackets['io_channel'].astype(int) > 20,ppackets['io_channel'].astype(int) < 25) ]
        print('percent valid packets:\t', np.sum( ppackets['valid_parity']==1  )/len(ppackets))
        data = ppackets[ np.logical_and( ppackets['packet_type']==0, ppackets['valid_parity']==1 )   ]
        print('total data packets:\t', len(data) )
        uniques = unique_id(data['io_group'].astype(int), data['io_channel'].astype(int), data['chip_id'].astype(int), data['channel_id'].astype(int))
        luniq = np.array(list(set(uniques)))
        np.random.shuffle(luniq)
        print(len(list(luniq)), 'total channels')
        d = {}
        dw = convert_adc_to_mv(data['dataword'],vref_dac,vcm_dac)
        counter=0
        total_channels = len(luniq)
        fig=plt.figure()
        ax = fig.add_subplot()
        ax.hist(dw, bins=50)
        ax.set_yscale('log')
        ax.set_title('all datawords')
        pbar=tqdm(total=len(list(luniq)))
        for chan in luniq:
            pbar.update(1)
            mask = uniques==chan
            d[int(chan)] = [ np.quantile(dw[mask], 0.05), np.median(dw[mask]), np.std(dw[mask]) ]
            ntr = len(dw[mask])
            if ntr < 1e4: ntrigs.append(ntr)
            if plot: 
                #if len(dw[mask]) < 10: continue
                #if not chan in gt250: continue
                count+=1
                if count > 20: continue
                fig = plt.figure()
                ax = fig.add_subplot()
                ax.set_title('sample channel: '+ str(chan) )
                ax.hist(dw[mask], bins=25, label='packets', range=(min(dw[mask])-100, min(dw[mask])+100))
                ax.axvline(np.quantile(dw[mask], 0.05), label='threshold', color='red', linestyle='--')
                ax.set_xlabel('front end voltage [mV]')
                ax.legend()
                plt.show()
        
            counter+=1
        pbar.close()
        if plot:
            fig = plt.figure()
            ax = fig.add_subplot()
            ax.hist(ntrigs, bins=50)
            ax.set_yscale('log')
            ax.set_title('Number of Triggers')
            plt.show()
        with open('extracted-'+tag+'.json', 'w') as ff: json.dump(d, ff)
        return

def match_channels(list_of_dicts):
    all_channels = dict()
    for key in list_of_dicts[0].keys():
        if not all([key in d.keys() for d in list_of_dicts]): continue
        all_channels[key] = []
        for d in list_of_dicts: all_channels[key].append(d[key][1])
    return all_channels


def line(x, a, b):
    return a*x + b


def fit_offset(global_thresh, threshold_dicts, pedestal, tag='', save=''):
    all_offsets = {}
    print('Fitting channel threshold offsets...')
    nmissing=0 
    pbar=tqdm(total=len(threshold_dicts[0].keys()))
    A=[]
    B=[]
    offset = {}
    slope = {}
    for channel in threshold_dicts[0].keys():
        if (not sum([channel in ddict.keys() for ddict in threshold_dicts])>=3) or (not channel in pedestal.keys()):
            nmissing+=1
            pbar.update(1)
            continue
        data = []
        xvals=[]
        for i in range(len(threshold_dicts)): 
            if not channel in threshold_dicts[i].keys(): continue
            data.append(threshold_dicts[i][channel][0]-pedestal[channel][1])
            xvals.append(global_thresh[i])
        params, pcov = curve_fit(line, xvals, data, p0=[465, 6.])
        pbar.update(1)
        A.append(params[0])
        B.append(params[1])
        slope[channel]=params[0]
        offset[channel]=params[1]
    pbar.close()
    print('missing {} channels'.format(nmissing))
    fig = plt.figure()
    ax = fig.add_subplot()
    ax.hist(A, bins=50, range=(-5,20))
    ax.set_title(tag+' Slope')
    ax.set_xlabel('slope [mV/dac]')

    fig = plt.figure()
    ax = fig.add_subplot()
    ax.hist(B, bins=50, range=(-50, 700))
    ax.set_title(tag+' Offset')
    ax.set_xlabel('offset [mV]')
    plt.show()
    
    with open(save+'-offset.json', 'w') as f: json.dump(offset, f)
    with open(save+'-slope.json', 'w') as f: json.dump(slope, f)
    return slope, offset

def main(datadir, pedfile, rescan=False):
    
    all_files=os.listdir(datadir)
    h5_files=[]
    for file in all_files:
        if file[-3:]=='.h5':
            h5_files.append(file)

    #format='pixel_trim-{}-threshold_global-{}-{}'
    threshold_global = []
    pixel_trim_dac = []
    extracted_name = []
    for file in h5_files:
        sp=file.split('-')
        tg = sp[2]
        ptd = sp[4]
        threshold_global.append(int(tg) )
        pixel_trim_dac.append(int(ptd) )
        name = 'extracted-' + 'tg-{}-ptd-{}.json'.format(tg, ptd)
        extracted_name.append(name)
        if rescan: get_channel_dict(datadir+'/'+file, tag='tg-{}-ptd-{}'.format(tg, ptd))

    if rescan: get_channel_dict(pedfile, tag='pedestal')

    pedestal = {}

    with open('extracted-pedestal.json', 'r') as f: pedestal=json.load(f)
    offset_dicts=[]
    thresh_global=[]

    pt_dicts = []
    pt_val = [] 
    for i in range(len(pixel_trim_dac)):
        if int(pixel_trim_dac[i])==0:
            d={}
            thresh_global.append(threshold_global[i])
            with open(extracted_name[i], 'r') as f: d=json.load(f)
            offset_dicts.append(d)
        
        if int(threshold_global[i])==70:
            d = {}
            pt_val.append(int(pixel_trim_dac[i]))
            with open(extracted_name[i], 'r') as f: d=json.load(f)
            pt_dicts.append(d)

    fit_offset(thresh_global, offset_dicts, pedestal, tag='Global Threshold', save='global_threshold')

    fit_offset(pt_val, pt_dicts, pedestal, tag='Pixel Trim', save='pixel_trim')

if __name__=='__main__':
    if len(sys.argv)==3:
        main(sys.argv[1], sys.argv[2])



