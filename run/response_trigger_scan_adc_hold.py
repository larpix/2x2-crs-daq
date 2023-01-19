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

_default_LRS=True
_default_file_prefix='selftrigger'
_default_disable_logger=False
_default_verbose=False
_default_disabled_json=None
_default_pedestal_json=None
_default_target=75
_default_runtime=1200
_default_file_count=3
_default_periodic_reset_cycles=6400
_default_vdda=1650.
_default_vref_dac=223
_default_vcm_dac=68
_default_ref_current_trim=0
_default_tx_diff=0
_default_tx_slice=15
_default_r_term=2
_default_i_rx=8

_current_dir_='/home/daq/PACMANv1rev4/commission/'
_destination_dir_='/data/LArPix/Module2_Nov2022/TPC12/'
#_io_group_pacman_tile_={1:list(range(1,9,1))}
#_io_group_pacman_tile_={2:list(range(1,9,1))}
_io_group_pacman_tile_={1:list(range(1,9,1)), 2:list(range(1,9,1))}
#_io_group_pacman_tile_={2:[8]}
_pacman_version_='v1rev4'
_asic_version_='2b'

global oldfilename

def ctrlc_handler(signal_received, frame):
    subprocess.call(["echo 0 > ~/.adc_watchdog_file"],shell=True)
    if oldfilename!=None: shutil.move(_current_dir+oldfilename, _destination_dir+oldfilename)
    print('SIGINT or CTRL-C detected. Exiting gracefully')
    exit(0)

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
         **kwargs):
    if pedestal_json==None:
        print('Input pedestal JSON file required by commandline argument. \n EXITING.')
        return
        
    c, io = network.main(file_prefix=file_prefix, \
                         disable_logger=disable_logger, \
                         verbose=verbose, ref_current_trim=ref_current_trim,\
                         tx_diff=tx_diff, tx_slice=tx_slice, r_term=r_term,\
                         i_rx=i_rx)

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
        ok, diff=asic_base.enable_response_trigger_config_by_io_channel(c, io,\
                                                                        iog_ioc[g_c],
                                                                        vref_dac, vcm_dac, vdda, periodic_reset_cycles, pedestal, disabled, target)

        if not ok:
            for key in diff.keys():
                print('MISCONFIGURED ASIC: ',key)
            print('*****WARNING: Response-based triggering config error(s).*****\n')
        print('Reponse-based triggering config setup on IO group ', g_c[0],\
              ' and IO channel ',g_c[1])

    iog_list=[]
    for key in iog_ioc.keys():
        if key[0] not in iog_list: iog_list.append(key[0])

    #adc_hold_delay=[4, 8, 15, 30, 60, 120]
    adc_hold_delay=[120] #, 15, 30, 60, 120]
    for ahd in adc_hold_delay:
        c.logger.enable()
        for g_c in iog_ioc.keys():
            io.set_reg(0x18, 2**(g_c[1]-1), \
                       io_group=g_c[0])
            chip_config_pairs=[]
            for chip_key in iog_ioc[g_c]:
                c[chip_key].config.adc_hold_delay=ahd
                c.write_configuration(chip_key,'adc_hold_delay')
                c.write_configuration(chip_key,'adc_hold_delay')
                ok, diff = utility_base.reconcile_configuration(c, chip_key,\
                                                                False)
                if not ok:
                    print(chip_key,' ADC hold delay ',ahd,' NOT configured')
            io.set_reg(0x18, 0, io_group=g_c[0])

        for iog in iog_list:
            ok, diff=asic_base.enable_self_triggering(c, io, iog, disabled)
            if not ok:
                for key in diff.keys():
                    print('MISCONFIGURED ASIC: ',key)
                    print('\n\n*****WARNING: Response-based self triggering error(s).*****')
            print('Response-based self triggering setup on IO group ',g_c[0])


        for iog in _io_group_pacman_tile_.keys():
            pacman_base.enable_pacman_uart_from_tile(io, iog, \
                                                     _io_group_pacman_tile_[iog])

        if disable_logger==False:
            c.logger.record_configs(list(c.chips.values())) 
            c.logger.flush()
            c.logger.disable()
            c.reads=[]
            shutil.move(_current_dir_+c.logger.filename, _destination_dir_+c.logger.filename)    
        
        ctr=0
        while ctr<file_count:
            filename = utility_base.data(c, runtime, False, \
                                         file_prefix+'-adc-hold-delay-'+str(ahd)+'-', LRS)
            shutil.move(_current_dir_+filename, _destination_dir_+filename)
            ctr+=1
        for iog in _io_group_pacman_tile_.keys():
            io.set_reg(0x18, 0, io_group=iog)

        for g_c in iog_ioc.keys():
            ok, diff = asic_base.debug_disable_response_trigger_config_by_io_channel(c, io, iog_ioc[g_c])
            if not ok:
                for key in diff.keys():
                    print('MISCONFIGURED ASIC: ',key)
                    print('*****WARNING: Response-based triggering NOT turned off.*****\n')
            print('Reponse-based triggering masked on IO group ', g_c[0],\
                  ' and IO channel ',g_c[1])


    return c



if __name__=='__main__':
    signal(SIGINT, ctrlc_handler)
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
                        default=_default_i_rx, \
                        type=int, \
                        help='''Receiver bias current DAC''')
    args=parser.parse_args()
    c = main(**vars(args))
