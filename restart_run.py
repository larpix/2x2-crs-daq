import larpix
from signal import signal, SIGINT
import larpix.io
import argparse
import shutil
import time
import response_trigger
_io_group_pacman_tile_={2:list(range(1,9,1))}

_default_LRS=False #True
_default_file_prefix=None
_default_disable_logger=False
_default_verbose=False
_default_disabled_json=None
_default_pedestal_json=None
_default_target=60 #75
_default_runtime=1200
_default_file_count=1
_default_periodic_reset_cycles=4096
_default_vdda=1650.
_default_vref_dac=223
_default_vcm_dac=68
_default_ref_current_trim=0
_default_tx_diff=0
_default_tx_slice=15
_default_r_term=2
_default_i_rx=8


_default_file_prefix=None
_default_asic_config_dir=None
_default_disable_logger=False
_default_register_name=None
#_default_register_value=None
_default_hydra_config_file=None
_asic_version_='v2b'
_current_dir_='/home/daq/PACMANv1rev4/commission/'
_destination_dir_='/data/LArPix/Module2_Nov2022/commission/Nov16/'
from base import pacman_base
from base import utility_base
from base import network_base

def main(LRS=_default_LRS, \
         file_prefix=_default_file_prefix, \
         disable_logger=_default_disable_logger, \
         verbose=_default_verbose, \
         disabled_json=_default_disabled_json, \
         pedestal_json=_default_disabled_json, \
         target=_default_target, \
         runtime=_default_runtime, \
         file_count=_default_file_count, \
         periodic_reset_cycles=_default_periodic_reset_cycles, \
         vdda=_default_vdda, \
         vref_dac=_default_vref_dac, \
         vcm_dac=_default_vcm_dac, \
         ref_current_trim=_default_ref_current_trim, \
         tx_diff=_default_tx_diff, \
         tx_slice=_default_tx_slice, \
         r_term=_default_r_term, \
         i_rx=_default_i_rx, \
         hydra_config_file=_default_hydra_config_file,\
         **kwargs):

    c = larpix.Controller()
    c.io = larpix.io.PACMAN_IO(relaxed=True)
    

#    if disable_logger==False:
#        now=time.strftime("%Y_%m_%d_%H_%M_%Z")
#        if file_prefix!=None: fname=file_prefix+'-broadcast-config-'+now+'.h5'
#        else: fname=='broadcast-config-'+now+'.h5'
#        c.logger = larpix.logger.HDF5Logger(filename=fname)
#        print('filename: ',c.logger.filename)
#        c.logger.enable()

    # load ASIC config    
    c.load(hydra_config_file)
    
    #    _io_group_pacman_tile_={2:list(range(1,9,1))}
    #for iog in _io_group_pacman_tile_.keys():
    #    pacman_base.disable_all_pacman_uart(c.io, iog)
    #    pacman_base.invert_pacman_uart(c.io, iog, _asic_version_, \
    #                                   _io_group_pacman_tile_[iog]) 

        #pacman_base.power_up(c.io, iog, 'v1rev4', True, 
        #                     _io_group_pacman_tile_[iog], _vdda_dac_, \
        #                     _vddd_dac_, reset_length=1000000000, \
        #                     vdda_step=1000, vddd_step=1000, ramp_wait=0.1,\
        #                     warm_wait=20)
        
#        pacman_base.power_up(c.io, iog, 'v1rev4', True, 
#                             _io_group_pacman_tile_[iog], _vdda_dac_, \
#                             _vddd_dac_, reset_length=300000000, \
#                             vdda_step=1000, vddd_step=1000, ramp_wait=0.1,\
#                             warm_wait=20)
    #for iog in _io_group_pacman_tile_.keys():
    #    readback=pacman_base.power_readback(c.io, iog, _pacman_version_, \
    #                                        _io_group_pacman_tile_[iog])

#    _io_group_pacman_tile_={2:[3]}
    #iog_ioc_cid=utility_base.iog_tile_to_iog_ioc_cid(_io_group_pacman_tile_, \
    #                                                 _asic_version_)
        
    #for g_c_id in iog_ioc_cid:
    #    network_base.network_ext_node_from_tuple(c, g_c_id)
    #print('setup software controller to root chips')

    #io.set_reg(0x101c, 4, io_group=io_group)
    # broadcast write
    for ii in range(1):
        iog_ioc_set = set()
        for chip in c.chips:
            iog = chip.io_group
            ioc = chip.io_channel
            if (iog, ioc) in iog_ioc_set: continue
            iog_ioc_set.add((iog, ioc))
            print(iog, ioc)
            for __chip in c.get_network_keys(iog, ioc, root_first_traversal=True):
                c[__chip].config.channel_mask = [1]*64
                c[__chip].config.csa_enable = [0]*64
                print('disabling chip', __chip)
                for __ in range(5):
                    #c.write_configuration(__chip, 'csa_enable')
                    c.write_configuration(__chip, 'csa_enable')
                    c.write_configuration(__chip, 'channel_mask')
    for iog_ioc_pair in iog_ioc_set:
        c.init_network(iog_ioc_pair[0], iog_ioc_pair[1])
    
    c = response_trigger.main(LRS, \
         file_prefix, \
         disable_logger, \
         verbose, \
         disabled_json, \
         pedestal_json, \
         target, \
         runtime, \
         file_count, \
         periodic_reset_cycles, \
         vdda, \
         vref_dac, \
         vcm_dac, \
         ref_current_trim, \
         tx_diff, \
         tx_slice, \
         r_term, \
         i_rx,\
         c=c)
    

    return c, c.io



if __name__=='__main__':
    signal(SIGINT, response_trigger.ctrlc_handler)
    parser = argparse.ArgumentParser()
    parser.add_argument('--LRS', default=_default_LRS, \
                        action='store_true', help='''True to run LRS''')
    parser.add_argument('--file_prefix', default=_default_file_prefix, \
                        type=str,  help='''String prepended to file''')
    parser.add_argument('--disable_logger', default=_default_disable_logger, \
                        action='store_true', help='''Disable logger''')
    parser.add_argument('--verbose', default=_default_verbose, \
                        action='store_true', help='''Enable verbose mode''')
    parser.add_argument('--disabled_json', default=_default_disabled_json, \
                        type=str, help='''JSON-formatted dict of disabled \
                        chip_key:[channel]''')
    parser.add_argument('--pedestal_json', default=_default_pedestal_json, \
                        type=str, help='''JSON-formatted dict of channel \
                        pedestal; chip_key: [(mean, std)]''')
    parser.add_argument('--target', default=_default_target, \
                        type=float, help='''Target value above pedestal to \
                        set threshold [mV]''')
    parser.add_argument('--runtime', default=_default_runtime, \
                        type=int, help='''Runtime duration''')
    parser.add_argument('--file_count', default=_default_file_count, \
                        type=int, help='''Number of output files to create''')
    parser.add_argument('--periodic_reset_cycles', \
                        default=_default_periodic_reset_cycles, type=int, \
                        help='''Periodic reset cycles [MCLK]''')
    parser.add_argument('--vdda', default=_default_vdda, type=float, \
                        help='''VDDA''')
    parser.add_argument('--vref_dac', default=_default_vref_dac, type=int, \
                        help='''Vref DAC''')
    parser.add_argument('--vcm_dac', default=_default_vcm_dac, type=int, \
                        help='''Vcm DAC''')
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
                        default=_default_i_rx)
#    parser.add_argument('--asic_config_dir', default=_default_asic_config_dir,\
#                        type=str, help='''Path to ASIC config JSON \
#                        file directory''')
    parser.add_argument('--hydra_config_file', default=_default_hydra_config_file,\
                        type=str, help='''Path to hydra config JSON ''')    
#    parser.add_argument('--file_prefix', default=_default_file_prefix, \
#                        type=str, help='''String prepended to filename''')
#    parser.add_argument('--disable_logger', default=_default_disable_logger, \
#                        action='store_true', help='''Disable logger''')
#    parser.add_argument('--register_name', default=_default_register_name, \
#                        type=str, help='''ASIC config register name''')
#    parser.add_argument('--register_value', default=_default_register_value, \
#                        type=int, help='''ASIC config register value; \
#                        WARNING: not applicable to list spaces''')
    args=parser.parse_args()
    main(**vars(args))
