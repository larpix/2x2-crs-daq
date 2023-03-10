import larpix
import larpix.io
from base import pacman_base
from base import network_base
from base import utility_base
import argparse
import json
import time
from time import perf_counter
import shutil

_default_file_prefix=None
_default_disable_logger=False
_default_verbose=False
_default_ref_current_trim=0
_default_tx_diff=0
_default_tx_slice=15
_default_r_term=2
_default_i_rx=8

_current_dir_='/home/daq/PACMANv1rev4/commission/'
_destination_dir_='/data/LArPix/Module2_Nov2022/TPC12_run2/'
#_io_group_pacman_tile_={9:[1]}
#_io_group_pacman_tile_={2:list(range(1,9,1))}
#_io_group_pacman_tile_={2:list(range(1,9,1))}
_io_group_pacman_tile_={1:list(range(1,9,1)), 2:list(range(1,9,1))}
_vdda_dac_=[47000]*8
_vddd_dac_=[31000]*8
_pacman_version_='v1rev4'
_asic_version_='2b'



def main(file_prefix=_default_file_prefix, \
         disable_logger=_default_disable_logger, \
         verbose=_default_verbose, \
         ref_current_trim=_default_ref_current_trim, \
         tx_diff=_default_tx_diff, \
         tx_slice=_default_tx_slice, \
         r_term=_default_r_term, \
         i_rx=_default_i_rx, \
         **kwargs):
    
    c = larpix.Controller()
    c.io = larpix.io.PACMAN_IO(relaxed=True)
    
    if disable_logger==False:
        now=time.strftime("%Y_%m_%d_%H_%M_%Z")
        if file_prefix!=None: fname=file_prefix+'-network-config-'+now+'.h5'
        else: fname='network-config-'+now+'.h5'
        c.logger = larpix.logger.HDF5Logger(filename=fname)
        print('filename: ', c.logger.filename)
        c.logger.enable()
        
    _io_group_pacman_tile_={1: list(range(1, 9, 1)), 2:list(range(1,9,1))}
    for iog in _io_group_pacman_tile_.keys():
        pacman_base.disable_all_pacman_uart(c.io, iog)
        pacman_base.invert_pacman_uart(c.io, iog, _asic_version_, \
                                       _io_group_pacman_tile_[iog]) 
     #   if iog==1: continue
        pacman_base.power_up(c.io, iog, 'v1rev4', True, 
                             _io_group_pacman_tile_[iog], _vdda_dac_, \
                             _vddd_dac_, reset_length=1000000000, \
                             vdda_step=1000, vddd_step=1000, ramp_wait=0.1,\
                             warm_wait=20)
        
#        pacman_base.power_up(c.io, iog, 'v1rev4', True, 
#                             _io_group_pacman_tile_[iog], _vdda_dac_, \
#                             _vddd_dac_, reset_length=300000000, \
#                             vdda_step=1000, vddd_step=1000, ramp_wait=0.1,\
#                             warm_wait=20)
    for iog in _io_group_pacman_tile_.keys():
    #    if iog==1: continue
        readback=pacman_base.power_readback(c.io, iog, _pacman_version_, \
                                            _io_group_pacman_tile_[iog])

    #_io_group_pacman_tile_={2:[3]}
    iog_ioc_cid=utility_base.iog_tile_to_iog_ioc_cid(_io_group_pacman_tile_, \
                                                     _asic_version_)
        
    for g_c_id in iog_ioc_cid:
        network_base.network_ext_node_from_tuple(c, g_c_id)
    print('setup software controller to root chips')

    root_keys=[]        
    for g_c_id in iog_ioc_cid:
        print(g_c_id)
        candidate_root = network_base.setup_root(c, c.io, g_c_id[0], \
                                                  g_c_id[1],\
                                                  g_c_id[2], verbose, \
                                                  _asic_version_, \
                                                  0, 0, 15, 2, 8)
        if candidate_root!=None: root_keys.append(candidate_root)
    print('ROOT KEYS: ',root_keys)

    iog_tile_to_root_keys=utility_base.partition_chip_keys_by_io_group_tile(root_keys)

    for iog_tile in iog_tile_to_root_keys.keys():
        network_base.initial_network(c, c.io, iog_tile[0], \
                                     iog_tile_to_root_keys[iog_tile], \
                                     verbose, \
                                     _asic_version_, ref_current_trim, \
                                     tx_diff, tx_slice, r_term, i_rx)

    unconfigured=[]
    for iog in _io_group_pacman_tile_.keys():
        for tile in _io_group_pacman_tile_[iog]:
            out_of_network=network_base.iterate_waitlist(c, c.io, iog, \
                                                         utility_base.tile_to_io_channel([tile]),
                                                         verbose, \
                                                         _asic_version_, \
                                                         ref_current_trim,\
                                                         tx_diff, tx_slice, \
                                                         r_term, i_rx)
            unconfigured.extend(out_of_network)

    network_file = network_base.write_network_to_file(c, file_prefix, _io_group_pacman_tile_,\
                                       unconfigured)
    shutil.move(_current_dir_+network_file, _destination_dir_+network_file)
                                

    if disable_logger==False:
        c.logger.flush()
        c.logger.disable()
        c.reads=[]
        shutil.move(_current_dir_+fname, _destination_dir_+fname)
        
    return c, c.io

    

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_prefix', default=_default_file_prefix, \
                        type=str, help='''String prepended to filename''')
    parser.add_argument('--disable_logger', default=_default_disable_logger, \
                        action='store_true', help='''Disable logger''')
    parser.add_argument('--verbose', default=_default_verbose, \
                        action='store_true', help='''Enable verbose mode''')
    parser.add_argument('--ref_current_trim', \
                        default=_default_ref_current_trim, \
                        type=int, \
                        help='''Trim DAC for primary reference current''')
    parser.add_argument('--tx_diff', \
                        default=_default_tx_diff, \
                        type=int, \
                        help='''Differential per-slice loop current DAC''')
    parser.add_argument('--tx_slice', \
                        default=_default_tx_slice, \
                        type=int, \
                        help='''Slices enabled per transmitter DAC''')
    parser.add_argument('--r_term', \
                        default=_default_r_term, \
                        type=int, \
                        help='''Receiver termination DAC''')
    parser.add_argument('--i_rx', \
                        default=_default_i_rx, \
                        type=int, \
                        help='''Receiver bias current DAC''')
    args = parser.parse_args()
    main(**vars(args))

