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


def tile_to_io_channel(tile):
    io_channel=[]
    for i in range(1,5,1):
        io_channel.append( ((tile-1)*4)+i )
    return io_channel

def unique_to_possible_io_channels(unique):
    io_channel=ch_id(int(unique))
    tile=io_channel_to_tile(io_channel)
    return tile_to_io_channel(tile)
    
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

def convert_adc_to_mv(adc, vref_dac=223, vcm_dac=68, vdda=1650):
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

def get_channel_dict(filename, vref_dac=vref_dac, vcm_dac=vcm_dac, plot=True, tag=''):
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
            if count >15: return
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

def get_key_channel(channel):
    chkey='{}-{}-{}'.format(iog(int(channel)), ioch(int(channel)), chip_id(int(channel)))
    chan = ch_id(int(channel))
    return chkey, chan


def main(thresholdfile, pedfile):
    
    all_thresholds={}
    allthr=[]
    pedestal = {}
    with open(pedfile, 'r') as f: pedestal=json.load(f)

    thresh = {}
    with open(thresholdfile, 'r') as f: thresh=json.load(f)

    for channel in thresh.keys():
        chkey, chan = get_key_channel(channel)
    
        all_ios = unique_to_possible_io_channels(channel)
        lookup_key=''
        for io in all_ios:
            look=chkey='{}-{}-{}'.format(iog(int(channel)), io, chip_id(int(channel)))
            if look in pedestal.keys():
                lookup_key=look
                break

        if lookup_key=='': continue
            
        for cch in range(0, 64):
            if not pedestal[lookup_key][cch][0]>0: continue
            
            if not chkey in all_thresholds.keys():
                all_thresholds[chkey]=[-1]*64
                all_thresholds[chkey][cch]=thresh[channel][0]-convert_adc_to_mv(pedestal[lookup_key][cch][0])
                allthr.append(thresh[channel][0]-convert_adc_to_mv(pedestal[lookup_key][cch][0]))


    fig=plt.figure()
    ax=fig.add_subplot()
    ax.set_title('Extracted Thresholds: Calo0 Run')
    ax.set_xlabel('channel threshold [mV]')

    ax.hist(allthr, bins=100)#, range=(100, 300))


    with open('threshold-log.json', 'w') as f: json.dump(all_thresholds, f, indent=4)
    plt.show()


if __name__=='__main__':
    if len(sys.argv)==3:
        main(sys.argv[1], sys.argv[2])



