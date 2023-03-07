import numpy as np
from matplotlib import pyplot as plt
import h5py
import os
import json
import argparse

_default_input_file=None
_default_file_prefix=None


ped_mean_cut = 45.
ped_std_cut = 2.
ped_rate_cut = 50 #Hz

_runtime=120

datadir='/data/LArPix/Module2_Nov2022/commission/Nov16/debug1/'

#datadir = '/data/LArPix/Module2_Nov2022/commission/'

datadict = {}

def get_list_of_h5_files(file_or_dir_name):
	if os.path.isfile(file_or_dir_name):
		return [file_or_dir_name]
	else:
		base = file_or_dir_name
		return sorted([base + "/" + name for name in os.listdir(base) if (name[-3:] == ".h5")])

def partition_by_channel(packets, datadict):
    packets=packets[packets['valid_parity']==1]
#    packets=packets[packets['packet_type']==0]
    io_groups = set(packets['io_group'])
    for iog in io_groups:
        #print('io_group:', iog)
        _packets = packets[packets['io_group']==iog]
        io_channels = set(_packets['io_channel'])
        for ioch in io_channels:
            #print('io_channel', ioch)
            __packets =_packets [_packets['io_channel']==ioch]
            chip_keys = set(__packets['chip_id'])
            for chkey in chip_keys:
                #print('chip_key', chkey)
                ___packets = __packets[__packets['chip_id']==chkey]
                channels = set(___packets['channel_id'])
                for chan in channels:
                    data = ___packets[___packets['channel_id']==chan]
                    key = '{}-{}-{}-{}'.format(iog, ioch, chkey, chan)
                    if not key in datadict: datadict[key]={'n':0,'sum':0, 'sum2':0}
                   # print(data['dataword'].astype(float))
                   # print(np.square( data['dataword'].astype(float) ) )
                    datadict[key]['n']+=len(data)
                    datadict[key]['sum']+=np.sum(data['dataword'].astype(float))
                    datadict[key]['sum2']+=np.sum(np.square(data['dataword'].astype(float)))
                   # print( (datadict[key]['sum']/datadict[key]['n'])**2,datadict[key]['sum2']/datadict[key]['n']) 
                    #print( np.sqrt(-1*(datadict[key]['sum']/datadict[key]['n'])**2+datadict[key]['sum2']/datadict[key]['n']) )

                   # print( (datadict[key]['sum'])**2-datadict[key]['sum2']) 
                    #print( (print( (datadict[key]['sum'])**2-datadict[key]['sum2']) )


                    #print(datadict[key]['sum'], datadict[key]['sum2'])
 #   for key in datadict.keys():
 #       print(datadict[key]['n'])
    return


def main(input_file=_default_input_file, \
         file_prefix=_default_file_prefix,\
         **kwargs):
    if input_file==None:
        print('Provide an input HDF5 packet file. Exiting.')
        return
    if file_prefix==None:
        print('Provide a filename for ouptut file. Exiting.')
        return
    #tag_dict = {}

    #for file in get_list_of_h5_files(datadir):
    #ss = file.split('pedestal')
    #print('found file:', file)
    #tag_dict[file]=0

    #for file in list(tag_dict.keys()):
    f = h5py.File(input_file)
    print('analyzing file:', input_file)
    partition_by_channel(f['packets'], datadict)
    
    datawords = []
    stds = []
    for key in datadict.keys():
        datawords.append(datadict[key]['sum']/datadict[key]['n'])
        datadict[key]['mean']=datadict[key]['sum']/datadict[key]['n']
        datadict[key]['std']=np.sqrt(-1*(datadict[key]['mean'])**2+datadict[key]['sum2']/datadict[key]['n'])
        stds.append(datadict[key]['std'])
        #print( (datadict[key]['sum'])**2, datadict[key]['sum2']) )
       # print(datadict[key]['n'], datawords[-1], stds[-1])

    print('\nplotting...\n')

    fign = plt.figure(figsize=(12,5))
    fign.suptitle('N Triggers')
    axn = fign.add_subplot()
    axn.hist([datadict[key]['n'] for key in datadict.keys()], bins=100, alpha=0.7);
    axn.set_xlabel('N Triggers')
    axn.set_yscale('log')
    
    fignn = plt.figure(figsize=(12,5))
    fignn.suptitle('N Triggers')
    axnn = fignn.add_subplot()
    axnn.hist([datadict[key]['n'] for key in datadict.keys()], bins=100, alpha=0.7, range=(0, 1e4));
    axnn.set_xlabel('N Triggers')
    axnn.set_yscale('log')



    fig = plt.figure(figsize=(12,5))
    fig.suptitle('Module2 Pedestal Mean')
    ax = fig.add_subplot()
    ax.hist(datawords, bins=100, alpha=0.7);
    ax.set_xlabel('dataword [adc]')
    #ax.set_yscale('log')
    #plt.legend()

    fig2 = plt.figure(figsize=(12,5))
    fig2.suptitle('Module2 Pedestal Std. Deviation')
    ax2 = fig2.add_subplot()
    #ax2 = fig.add_subplot()
    ax2.hist(stds, bins=100, range=(0, 10), alpha=0.7);
    ax2.set_xlabel('adc')
    ax2.set_yscale('log')
    ax2.set_xlim(0, 10)
    fig3 = plt.figure(figsize=(12,5))
    fig3.suptitle('Module2 Pedestal Mean vs. Pedestal Std. Deviation')
    ax3 = fig3.add_subplot()
    #ax2 = fig.add_subplot()
    ax3.scatter(datawords, stds)
    ax3.set_xlabel('mean')
    ax3.set_ylabel('std. dev.')
    #ax2.set_yscale('log')
    fig4 = plt.figure(figsize=(12,5))
    fig4.suptitle('Module2 Pedestal Std. Deviation')
    ax4 = fig4.add_subplot()
    #ax2 = fig.add_subplot()
    ax4.hist(stds, bins=100, alpha=0.7);
    ax4.set_xlabel('adc')
    ax4.set_yscale('log')
    #ax4.set_xlim(0, 10)
 
    fig.savefig(file_prefix+'-ped_mean.png')
    fig2.savefig(file_prefix+'-ped_std.png')
    fig3.savefig(file_prefix+'-ped_mean_vs_std.png')
    plt.show() 
    #import json

    disable={}
    data = {}

    for key in datadict.keys():
        #add to disabled list
        ids = key.split('-')
        newkey = '{}-{}-{}'.format(ids[0], ids[1], ids[2])
        if not (newkey in data.keys()):
            print('added key', newkey)
            data[newkey] = [(-1, -1) for i in range(64)]
        data[newkey][int(ids[-1])]=(datadict[key]['mean'], datadict[key]['std'])
        if datadict[key]['mean']>ped_mean_cut:
            if not newkey in disable.keys(): disable[newkey]=[]
            disable[newkey].append(int(ids[-1]) )
        if datadict[key]['n']/_runtime>ped_rate_cut:
            if not newkey in disable.keys(): disable[newkey]=[]
            disable[newkey].append(int(ids[-1]) )
        if datadict[key]['std']>ped_std_cut:
            if not newkey in disable.keys(): disable[newkey]=[]
            disable[newkey].append(int(ids[-1]) )
    
    #import json
    with open(file_prefix+'-pedestal-disable.json', 'w') as ff:
        json.dump(disable, ff, indent=4)

    with open(file_prefix+'-pedestal-mean-std.json', 'w') as ff:
        json.dump(data, ff, indent=4)


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', default=_default_input_file, \
                        type=str, help='''Input HDF5 pakcet file''')
    parser.add_argument('--file_prefix', default=_default_file_prefix, \
                        type=str, help='''String prepended to file''')
    args = parser.parse_args()
    main(**vars(args))
