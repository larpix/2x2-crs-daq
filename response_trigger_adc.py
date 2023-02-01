import larpix
import larpix.io
import network
from base import pacman_base
from base import asic_base
from base import ana_base
from base import utility_base
import argparse
import time
import json
import shutil
import subprocess
from signal import signal, SIGINT

_default_LRS=False #True
_default_file_prefix='self_trigger_NAME_ME'
_default_disable_logger=False
_default_verbose=False
_default_disabled_json=None
_default_pedestal_json=None
_default_target=60 #75
_default_runtime=1200
_default_file_count=1
_default_periodic_reset_cycles=64
_default_vdda=1650.
_default_vref_dac=223
_default_vcm_dac=68
_default_ref_current_trim=0
_default_tx_diff=0
_default_tx_slice=15
_default_r_term=2
_default_i_rx=8
_current_dir_='/home/daq/PACMANv1rev3b/commission/take2/2x2-crs-daq/'
_destination_dir_='/data/LArPix/Module3_Feb2023/ramp_up/'

#_io_group_pacman_tile_={1:list(range(1,9,1))}
#_io_group_pacman_tile_={2:list(range(1,9,1))}
_io_group_pacman_tile_={1:list(range(1,9,1)), 2:list(range(1,9,1))}
#_io_group_pacman_tile_={2:[3]}
_pacman_version_='v1rev4'
_asic_version_='2b'

global oldfilename

def ctrlc_handler(signal_received, frame):
    subprocess.call(["echo 0 > ~/.adc_watchdog_file"],shell=True)
    if oldfilename!=None: shutil.move(_current_dir+oldfilename, _destination_dir+oldfilename)
    print('SIGINT or CTRL-C detected. Exiting gracefully')
    exit(0)

def main(LRS=_default_LRS, \
         resume=False,\
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
         pixel_trim_dict=None,\
         controller_config=None,\
         ref_adc_json=None, \
         global_ref=None, \
         trim_ref=None,\
         trim_scale_json=None,\
         global_scale_json=None,\
         c=None,\
         **kwargs):
    if pedestal_json==None:
        print('Input pedestal JSON file required by commandline argument. \n EXITING.')
        return
    io = None
    global_scale_dict={}
    trim_scale_dict={}
    ref_adc={}

    with open(trim_scale_json, 'r') as f: trim_scale_dict = json.load(f)
    with open(global_scale_json, 'r') as f: global_scale_dict = json.load(f)
    with open(ref_adc_json, 'r') as f: ref_adc = json.load(f)

    if c is None:
        c, io = network.main(file_prefix=file_prefix, \
                             disable_logger=disable_logger, \
                             verbose=verbose, ref_current_trim=ref_current_trim,\
                             tx_diff=_default_tx_diff, tx_slice=_default_tx_slice, r_term=r_term,\
                             i_rx=i_rx, resume=resume, controller_config=controller_config)
    else:
        io = c.io
    
    print('****', 16*100-len(c.chips), ' missing chips') 


    if disable_logger==False:
        now=time.strftime("%Y_%m_%d_%H_%M_%Z")
        if file_prefix!=None: fname=file_prefix+'-response-trigger-config-'+now+'.h5'
        else: fname='response-trigger-config-'+now+'.h5'
        c.logger = larpix.logger.HDF5Logger(filename=fname)
        print('filename: ', c.logger.filename)
        c.logger.enable()

    iog_ioc={}
    for chip_key in c.chips:
        pair = (chip_key.io_group, chip_key.io_channel)
        if pair not in iog_ioc: iog_ioc[pair]=[]
        iog_ioc[pair].append(chip_key)

    disabled=dict()
    if disabled_json!=None:
        with open(disabled_json,'r') as f: disabled=json.load(f)

    pedestal=dict()
    if pedestal_json!=None:
        with open(pedestal_json,'r') as f: pedestal=json.load(f)
        
    for g_c in iog_ioc.keys():
        ok, diff = asic_base.enable_response_trigger_adc_config_by_io_channel(c, io, iog_ioc[g_c], vref_dac=vref_dac, \
                                                 vcm_dac=vcm_dac, vdda=vdda,\
                                                 periodic_reset_cycles=periodic_reset_cycles, \
                                                 pedestal=pedestal,\
                                                 disabled=disabled,\
                                                 target=target,\
                                                 ref_adc=ref_adc, global_ref=global_ref, trim_ref=trim_ref, \
                                                 trim_scale_dict=trim_scale_dict, global_scale_dict=global_scale_dict)

        if not ok:
            for key in diff.keys():
                print('MISCONFIGURED ASIC: ',key, diff[key])
            print('*****WARNING: Response-based triggering config error(s).*****\n')
        print('Reponse-based triggering config setup on IO group ', g_c[0],\
              ' and IO channel ',g_c[1])

    iog_list=[]
    for key in iog_ioc.keys():
        if key[0] not in iog_list: iog_list.append(key[0])

    for iog in iog_list:
        ok, diff=asic_base.enable_self_triggering(c, io, iog, disabled, set_rate=0.1)
        if not ok:
            for key in diff.keys():
                print('MISCONFIGURED ASIC: ', key, diff[key])
            print('\n\n*****WARNING: Response-based self triggering error(s).*****')
        print('Response-based self triggering setup on IO group ',g_c[0])

    if disable_logger==False:
        c.logger.record_configs(list(c.chips.values())) 
        c.logger.flush()
        c.logger.disable()
        c.reads=[]
        shutil.move(_current_dir_+c.logger.filename, _destination_dir_+c.logger.filename)
    
    for iog in _io_group_pacman_tile_.keys():
            all_io_channels = list(utility_base.all_io_channels(c, iog))
            print('enabling uarts on io_group', iog, 'io_channels:', all_io_channels)
            pacman_base.enable_pacman_uart_from_io_channel(c.io, iog, all_io_channels)
        
    ctr=0
    while ctr<file_count:
        filename = utility_base.data(c, runtime, False, file_prefix, LRS)
        shutil.move(_current_dir_+filename, _destination_dir_+filename)
        ctr+=1
    for iog in _io_group_pacman_tile_.keys():
        io.set_reg(0x18, 0, io_group=iog)
    
    return c



if __name__=='__main__':
    signal(SIGINT, ctrlc_handler)
    parser = argparse.ArgumentParser()
    parser.add_argument('--trim_scale_json', default=None, \
                        type=str, help='''Pixel Trim dict''')
    parser.add_argument('--global_scale_json', default=None, \
                        type=str, help='''Pixel Trim dict''')

    parser.add_argument('--controller_config', default=None, \
                        type=str, help='''Controller config for v2a tiles only''')
    
    parser.add_argument('--resume', default=False, \
                        action='store_true', help='''No reset, leave asic configuration intact ''')

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
                        default=_default_i_rx, \
                        type=int, \
                        help='''Receiver bias current DAC''')
    parser.add_argument('--ref_adc_json', \
                        default=None, \
                        type=str, \
                        help='''JSON file with ADC threshold at reference settings''')
    parser.add_argument('--global_ref', \
                        default=None, \
                        type=int, \
                        help='''Global threshold of reference calibration run''')
    parser.add_argument('--trim_ref', \
                        default=None, \
                        type=int, \
                        help='''trim_dac of reference calibration run''')

    args=parser.parse_args()
    c = main(**vars(args))
