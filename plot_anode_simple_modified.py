import time
import h5py
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
import json
import glob
import argparse

max_index=10000000

###_default_datalog_file='/home/russell/DUNE/2x2/Module1/datalog_2022_02_03_20_14_20_CET.h5'
###_default_geometry_file='/home/russell/DUNE/2x2/Module1/multi_tile_layout-2.2.16-dict.json'

_default_datalog_file='/data/LArPix/Module3_Feb2023/commission/calibration_packets/use_me/packet_module3-threshold-calibration-threshold_global-80-trim_dac-0--binary-2023_01_28_23_41_CET.h5'
#_default_datalog_file='/data/LArPix/SingleModule_Jan2022/TPC12/dataRuns/Cooldown/raw_2022_02_06_11_06_37_CET.h5'
#_default_geometry_file='/home/daq/PACMANv1rev3/larpix-10x10-scripts/module1/multi_tile_layout-2.1.16-dict.json'
#_default_geometry_file='/home/daq/PACMANv1rev3/larpix-geometry/larpixgeometry/layouts/bern-module1-warm-test-tile-replacement-dict.json'
#_default_geometry_file='/home/daq/PACMANv1rev3/larpix-10x10-scripts/module1/Warm_test_after_tile_replacement/full_anode/Mod1_april_swapped_bottom_v3-dict.json'
#_default_geometry_file='/home/daq/PACMANv1rev4/larpix-geometry/larpixgeometry/layouts/multi_tile_layout-2.5.16.yaml'
_default_geometry_file='/home/daq/PACMANv1rev3b/larpix-monitor/multi_tile_layout-module3-dict.json'

nonrouted_channels=[]
routed_channels=[i for i in range(64) if i not in nonrouted_channels]


def unique_channel_id(d): return ((d['io_group'].astype(int)*256+d['io_channel'].astype(int))*256 + d['chip_id'].astype(int))*64 + d['channel_id'].astype(int)

def unique_2_channel_id(unique): return unique % 64

def unique_2_chip_id(unique): return (unique//64) % 256

def unique_2_io_channel(unique): return(unique//(64*256)) % 256

def unique_2_io_group(unique): return(unique // (64*256*256)) % 256

def unique_2_chip_key_string(unique): return str(unique_2_io_group(int(unique)))+'-'+str(unique_2_io_channel(int(unique)))+'-'+str(unique_2_chip_id(int(unique)))

def convert_unique_2_network_agnostic(unique):
    channel_id = unique_2_channel_id(unique)
    chip_id = unique_2_chip_id(unique)
    io_channel = unique_2_io_channel(unique)
    io_group = unique_2_io_group(unique)

    io_channel = ((io_channel-1) // 4) * 4 + 1
    return ((io_group*256 + io_channel)*256 + chip_id)*64 + channel_id

def find_mean_std_rate(datalog_file, geometry_dict):
    d = dict()
    f = h5py.File(datalog_file,'r')
    #f = datalog_file

    print (f)
    print (f.keys())
    unixtime = f['packets']['timestamp'][f['packets']['packet_type']==4]
    livetime = np.max(unixtime) - np.min(unixtime)
    print(len(f['packets']),' packets')
    data_mask=f['packets'][:]['packet_type'][0:max_index]==0
    valid_parity_mask=f['packets'][:]['valid_parity'][0:max_index]==1
    mask = np.logical_and(data_mask, valid_parity_mask)
    adc = f['packets']['dataword'][0:max_index][mask]
    unique_id = unique_channel_id(f['packets'][0:max_index][mask])
    unique_id = convert_unique_2_network_agnostic(unique_id)
    unique_id_set = np.unique(unique_id)
    for i in unique_id_set:
        if str(i) not in geometry_dict: continue
        id_mask = unique_id == i
        masked_adc = adc[id_mask]
        d[i] = dict(
            mean = np.mean(masked_adc),
            std = np.std(masked_adc),
            x = geometry_dict[str(i)][0],
            y = geometry_dict[str(i)][1],
            rate = len(masked_adc) / (livetime + 1e-9),
            n = len(masked_adc)
        )
    return d



### to extract single channel (X,Y) position: X == d[str(unique_channel_id)][0]; Y == d[str(unique_channel_id)][1]
def load_geometry(g):
    geom_dict = None
    with open(g,'r') as f: geom_dict = json.load(f)
    return geom_dict



def plot_xy(metric_dict, metric, unit):
    fig, ax = plt.subplots(1, 2, num=metric, figsize=(20,15))
    c0 = fig.colorbar(ax[0].scatter([metric_dict[key]['x'] for key in metric_dict.keys() if unique_2_io_group(int(key))==1],
                                    [metric_dict[key]['y'] for key in metric_dict.keys() if unique_2_io_group(int(key))==1],
                                    c=[metric_dict[key][metric] for key in metric_dict.keys() if unique_2_io_group(int(key))==1],
                                    marker='s',s=1.5), ax = ax[0])
    c1 = fig.colorbar(ax[1].scatter([metric_dict[key]['x'] for key in metric_dict.keys() if unique_2_io_group(int(key))==2],
                                    [metric_dict[key]['y'] for key in metric_dict.keys() if unique_2_io_group(int(key))==2],
                                    c=[metric_dict[key][metric] for key in metric_dict.keys() if unique_2_io_group(int(key))==2],
                                    marker='s',s=1.5), ax = ax[1])

    for i in range(2):
        ax[i].set_xlabel('X [mm]')
        ax[i].set_ylabel('Y [mm]')
        ax[i].set_title('TPC '+str(i+1))
    c0.set_label(unit); c1.set_label(unit)
    plt.tight_layout()
    plt.show()
    plt.savefig(metric+'.png')
    return fig


    
def main(datalog_file=_default_datalog_file, geometry_file=_default_geometry_file):    
    if geometry_file==None: print('Geometry file absent. Exiting early'); return
    if datalog_file==None: print('Datalog file absent. Exiting early'); return
    geometry_dict = load_geometry(geometry_file)
    c=0
    print('test0')
    for key in geometry_dict.keys():
        c+=1
    print(c,' keys in geometry dict')
    print(datalog_file)
    d = find_mean_std_rate(datalog_file, geometry_dict)
    plot_xy(d, 'mean', 'ADC')
    plot_xy(d, 'std', 'ADC')
    plot_xy(d, 'rate', 'Hz')
    print('done plotting.')

def AnodeSimpleTemplate(name, units):
    class AnodeSimple(object):
        name = 'mean'
        units = 'ADC'
        
        def __init__(self):
            self.geometry_dict = load_geometry(_default_geometry_file)
            self._cached_data = dict()
            self._update_time = dict()

        def update_cache(self, filename, d):
            now = time.time()

            self._update_time[filename] = now
            if filename in self._cached_data:
                for key in d:
                    prev_n = self._cached_data[filename].get(key, dict()).get('n',0)
                    new_n = d[key]['n']
                    prev_val = self._cached_data[filename].get(key, dict()).get(self.name,0)
                    new_val = d[key][self.name]
                    n = prev_n + new_n
                    val = prev_val * prev_n + new_val * new_n
                    val /= n
                    if key in self._cached_data[filename]:
                        self._cached_data[filename][key]['n'] = n
                        self._cached_data[filename][key][self.name] = val
                    else:
                        self._cached_data[filename][key] = d[key]
            else:
                self._cached_data[filename] = d

            for key in list(self._cached_data.keys()):
                last = self._update_time.get(key, None)
                if last is not None and last + 300 < now:
                    del self._update_time[key]
                    del self._cached_data[key]

        def __call__(self, filename, fh, fig=None):
            if fig is not None:
                plt.figure(fig.number)
                plt.close()
                fig = None
            print('test')
            d = find_mean_std_rate(fh, self.geometry_dict)

            self.update_cache(filename, d)
            
            fig = plot_xy(self._cached_data[filename], self.name, self.units)

            return fig

    AnodeSimple.name = name
    AnodeSimple.units = units
    return AnodeSimple

AnodeSimpleMean = AnodeSimpleTemplate('mean', 'ADC')
AnodeSimpleStd = AnodeSimpleTemplate('std', 'ADC')
AnodeSimpleRate = AnodeSimpleTemplate('rate', 'Hz')
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # input file paths
    parser.add_argument('--datalog_file', default=_default_datalog_file, type=str, help='''Path to datalog file''')
    parser.add_argument('--geometry_file', default=_default_geometry_file, type=str, help='''Path to geometry file''')
    
    args = parser.parse_args()
    main(**vars(args))
