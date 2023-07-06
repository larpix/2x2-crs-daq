

#TO DO: FIX ISSUE WITH MULTIPLE IO CHANNEL NETWORKS
#RIGHT NOW SECOND IO_CHANNEL CONTROLLER OVERWRITES FIRST


import larpix
import larpix.io
from base import pacman_base
from base import network_base
from base import utility_base
from base import v2a_base
import hydra_chain
from base import generate_config
import argparse
import json
import time
from time import perf_counter
import shutil
from base import config_loader
from RUNENV import *
from tqdm import tqdm
_default_file_prefix=None
_default_disable_logger=True
_default_verbose=False
_default_ref_current_trim=0
_default_tx_diff=0
_default_tx_slice=15
_default_r_term=2
_default_i_rx=8
_default_recheck=False


def main(file_prefix=_default_file_prefix, \
         disable_logger=_default_disable_logger, \
         verbose=_default_verbose, \
         ref_current_trim=_default_ref_current_trim, \
         tx_diff=_default_tx_diff, \
         tx_slice=_default_tx_slice, \
         r_term=_default_r_term, \
         i_rx=_default_i_rx, \
         controller_config=None,
         asic_config=None,\
         resume=False,
         recheck=_default_recheck,
         **kwargs):
   
    c = larpix.Controller()
    c.io = larpix.io.PACMAN_IO(relaxed=True)
    c.io.reset_larpix(length=4096*4, io_group=1) #2048 
    time.sleep(4096*4*1e-6)
    c.io.reset_larpix(length=4096*4, io_group=1) #2048 
    time.sleep(4096*4*1e-6)


    if controller_config is None:
        now=time.strftime("%Y_%m_%d_%H_%M_%Z")
        config_name='controller-config-'+now+'.json'


    if disable_logger==False:
        now=time.strftime("%Y_%m_%d_%H_%M_%Z")
        if file_prefix!=None: fname=file_prefix+'-network-config-'+now+'.h5'
        else: fname='network-config-'+now+'.h5'
        c.logger = larpix.logger.HDF5Logger(filename=fname)
        print('filename: ', c.logger.filename)
        c.logger.enable()
    
         
    #_io_group_pacman_tile_={1: list(range(1, 9, 1)), 2:list(range(1,9,1))}
    _io_group_pacman_tile_={1:[2]}
    for iog in io_group_pacman_tile_.keys():
       
        iog_ioc_cid=utility_base.iog_tile_to_iog_ioc_cid(io_group_pacman_tile_, io_group_asic_version_[iog])
        

#        pacman_base.disable_all_pacman_uart(c.io, iog)
        #VERSION_SPECIFIC
        if io_group_asic_version_[iog]=='2b': 
            print('inverting io group {} tiles {}'.format(iog, io_group_pacman_tile_[iog]))
            pacman_base.invert_pacman_uart(c.io, iog, io_group_asic_version_[iog], \
                                       io_group_pacman_tile_[iog]) 
     #   if iog==1: continue
        #VERSION_SPECIFIC
        _vdda_dac_=[0,46020,0,0,0,0,0,0]
        _vddd_dac_=[0,32000,0,0,0,0,0,0]
        #pacman_base.power_up(c.io, iog, iog_pacman_version_[iog], True, 
        #                     io_group_pacman_tile_[iog], _vdda_dac_, \
        #                      _vddd_dac_, reset_length=1000000) 
        
        
        #replaced the value for _vdda_dac_, \
        #replaced the value for _vddd_dac_

        #pacman_base.power_up(c.io, iog, 'v1revS1', True, 
        #                     io_group_pacman_tile_[iog], _vdda_dac_, 
        #                     _vddd_dac_, reset_length=300000000,
        #                     vdda_step=1000, vddd_step=1000, ramp_wait=0.5,
        #                     warm_wait=20)
        #time.sleep(2)
    for iog in io_group_pacman_tile_.keys():
        readback=pacman_base.power_readback(c.io, iog, iog_pacman_version_[iog], \
                                            io_group_pacman_tile_[iog])

    #_io_group_pacman_tile_={2:[3]}
        
    for g_c_id in iog_ioc_cid:
        network_base.network_ext_node_from_tuple(c, g_c_id)
    
    print('setup software controller to root chips')
    
    for iog in io_group_pacman_tile_.keys():
        print('Configuring IO Group', iog)
        if io_group_asic_version_[iog]=='2b':
            root_keys=[]        
            for g_c_id in iog_ioc_cid:
                print(g_c_id)
                candidate_root = network_base.setup_root(c, c.io, g_c_id[0], \
                                                        g_c_id[1],\
                                                          g_c_id[2], verbose, \
                                                          io_group_asic_version_[iog], \
                                                          0, 0, 15, 2, 8)
                if candidate_root!=None: root_keys.append(candidate_root)
            print('ROOT KEYS: ',root_keys)

            iog_tile_to_root_keys=utility_base.partition_chip_keys_by_io_group_tile(root_keys)

            for iog_tile in iog_tile_to_root_keys.keys():
                network_base.initial_network(c, c.io, iog_tile[0], \
                                             iog_tile_to_root_keys[iog_tile], \
                                             verbose, \
                                             io_group_asic_version_[iog], ref_current_trim, \
                                             tx_diff, tx_slice, r_term, i_rx)

            unconfigured=[]
            for iog in io_group_pacman_tile_.keys():
                for tile in io_group_pacman_tile_[iog]:
                    out_of_network=network_base.iterate_waitlist(c, c.io, iog, \
                                                                 utility_base.tile_to_io_channel([tile]),
                                                                 verbose, \
                                                                 io_group_asic_version_[iog], \
                                                                 ref_current_trim,\
                                                                 tx_diff, tx_slice, \
                                                                 r_term, i_rx)
                    unconfigured.extend(out_of_network)
            network_file = network_base.write_network_to_file(c, file_prefix, io_group_pacman_tile_,\
                                       unconfigured)
            shutil.move(current_dir_+network_file, destination_dir_+network_file)

            if disable_logger==False:
                c.logger.flush()
                c.logger.disable()
                c.reads=[]
                shutil.move(current_dir_+fname, destination_dir_+fname)
            
            
            if not asic_config is None: config_loader.load_config_from_directory(c, asic_config)
            
            print(c.chips.keys())
            last_io_channel = None
            last_io_group = None
            for chip in tqdm(c.chips):
                ioch = chip.io_channel
                iogr = chip.io_group
                if not (last_io_channel==ioch and last_io_group==iogr):
                    last_io_channel = ioch
                    last_io_group = iogr
                    pacman_base.enable_pacman_uart_from_io_channel(c.io, iogr, [ioch] )
        #        print(chip, c[chip].config.channel_mask)
                ok, diff = c.enforce_configuration(chip, n=5, n_verify=3, timeout=0.01)
                if not ok:
                    print(diff)
                    #return
            config_loader.write_config_to_file(c)

            return c, c.io

        elif io_group_asic_version_[iog]==2:  
            print('configuring v2a network...')
            if controller_config is None: 
                config_name = hydra_chain.main(io_group=iog, pacman_tile=_io_group_pacman_tile_[iog], pacman_version=_iog_pacman_version_[iog], config_name=config_name, exclude=_iog_exclude[iog])
                time.sleep(1)
            else: 
                print('starting main')
                c = v2a_base.main(controller_config=controller_config, pacman_version=iog_pacman_version_[iog], asic_config=asic_config, resume=resume, recheck=recheck)
                io = c.io
                return c, c.io

        c = v2a_base.main(controller_config=config_name, pacman_version=_iog_pacman_version_[iog], recheck=recheck)
        io = c.io
        
        return c, io

    

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--asic_config', default=None, \
                        type=str, help='''Directory with JSON files giving ASIC configuration registers''')
    parser.add_argument('--controller_config', default=None, \
                        type=str, help='''Controller config for v2a tiles only''')
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
    parser.add_argument('--recheck', default=_default_recheck, \
                        action='store_true', help='''Flag to re-check all asic configs after initally enforcing them all ''')
    args = parser.parse_args()
    main(**vars(args))

