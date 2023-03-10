#!/usr/bin/env python3

import argparse
from copy import deepcopy

import larpix
import larpix.io
import larpix.logger
import numpy as np
import time
from base import utility_base
from base import pacman_base
from tqdm import tqdm
from base import config_loader
from base import check_power

LARPIX_10X10_SCRIPTS_VERSION='v1.0.3'

_default_controller_config=None
_default_pacman_version='v1rev3'
_default_logger=False
_default_reset=True

##### default network (single chip) if no hydra network provided
_default_chip_id = 2
_default_io_channel = 1
_default_miso_ds = 0
_default_mosi = 0
_default_clk_ctrl = 1

##### default IO 
_uart_phase = 2

#clk_ctrl_2_clk_ratio_map = {
#        0: 2,
#        1: 4,
#        2: 8,
#        3: 16
#        }

clk_ctrl_2_clk_ratio_map = {
        0: 10,
        1: 20,
        2: 40,
        3: 80
        }

v2a_nonrouted_channels=[6,7,8,9,22,23,24,25,38,39,40,54,55,56,57]

vdda_reg = dict()
vdda_reg[1] = 0x00024130
vdda_reg[2] = 0x00024132
vdda_reg[3] = 0x00024134
vdda_reg[4] = 0x00024136
vdda_reg[5] = 0x00024138
vdda_reg[6] = 0x0002413a
vdda_reg[7] = 0x0002413c
vdda_reg[8] = 0x0002413e

vddd_reg = dict()
vddd_reg[1] = 0x00024131
vddd_reg[2] = 0x00024133
vddd_reg[3] = 0x00024135
vddd_reg[4] = 0x00024137
vddd_reg[5] = 0x00024139
vddd_reg[6] = 0x0002413b
vddd_reg[7] = 0x0002413d
vddd_reg[8] = 0x0002413f

def convert_voltage_for_pacman(voltage):
        max_voltage, max_scale = 1.8, 46020
        v = voltage
        if v > max_voltage: v=max_voltage
        return int( (v/max_voltage)*max_scale )


def unique_channel_id(io_group, io_channel, chip_id, channel_id):
    return channel_id + 100*(chip_id + 1000*(io_channel + 1000*(io_group)))

def from_unique_to_chip_key(unique):
    io_group = (unique // (100*1000*1000)) % 1000
    io_channel = (unique // (100*1000)) % 1000
    chip_id = (unique // 100) % 1000
    return larpix.Key(io_group, io_channel, chip_id)

def from_unique_to_channel_id(unique):
    return int(unique) % 100

def from_unique_to_chip_id(unique):
    return int(unique//100) % 1000

def chip_key_to_string(chip_key):
    return '-'.join([str(int(chip_key.io_group)),str(int(chip_key.io_channel)),str(int(chip_key.chip_id))])

def get_tile_from_io_channel(io_channel):
    return np.floor( (io_channel-1-((io_channel-1)%4))/4+1)

def get_all_tiles(io_channel_list):
    tiles = set()
    for io_channel in io_channel_list:
        tiles.add(int(get_tile_from_io_channel(io_channel)) )
    return list(tiles)

def get_reg_pairs(io_channels):
    tiles = get_all_tiles(io_channels)
    reg_pairs = []
    for tile in tiles:
        reg_pairs.append( (vdda_reg[tile], vddd_reg[tile]) )
    return reg_pairs


#print('ENABLE PRC!!!!!FIX ME REPLACING TILE 1 VDDD FOR SINGLE BRINGUP--PUT BACK TO 37520 ON IO GROUP 1')
vddd_bytile_byio = [[37500, 38500, 38500, 38500, 38500, 39000, 39000, 39000],\
                [37520, 38000, 38500, 38000, 38500, 39000, 39000, 39000]]



def set_pacman_power(c, vdda=46020, vddd=37520):
    return
    for _io_group, io_channels in c.network.items():
        active_io_channels = []
        for io_channel in range(1,33): #io_channels:
            active_io_channels.append(io_channel)
        reg_pairs = get_reg_pairs(active_io_channels)
        print(active_io_channels)
        #reg_pairs=get_reg_pairs([25,26, 27,28])
        #for ip, pair in enumerate(reg_pairs):
        #    c.io.set_reg(pair[0], vdda, io_group=_io_group)
        #    c.io.set_reg(pair[1], vddd_bytile_byio[_io_group-1][ip], io_group=_io_group)
        #tiles = get_all_tiles(active_io_channels)
        #bit_string = list('1000000000')
        #for tile in tiles: bit_string[-1*tile] = '1'
        c.io.set_reg(0x00000014, 1, io_group=_io_group) # enable global larpix power
        #c.io.set_reg(0x00000010, int("".join(bit_string), 2), io_group=_io_group) # enable tiles to be powered
        c.io.set_reg(0x101C, 4, io_group=_io_group)
        c.io.set_reg(0x18, 0xffffffff, io_group=_io_group) # enable uarts (for all tiles?)
    time.sleep(0.1)


def power_registers():
    adcs=['VDDA', 'IDDA', 'VDDD', 'IDDD']
    data = {}
    for i in range(1,9,1):
        l = []
        offset = 0
        for adc in adcs:
            if adc=='VDDD': offset = (i-1)*32+17
            if adc=='IDDD': offset = (i-1)*32+16
            if adc=='VDDA': offset = (i-1)*32+1
            if adc=='IDDA': offset = (i-1)*32
            l.append( offset )
        data[i] = l
    return data


def flush_data(controller, runtime=0.1, rate_limit=0., max_iterations=10):
    ###### continues to read data until data rate is less than rate_limit
    for _ in range(max_iterations):
        controller.run(runtime, 'flush_data')
        if len(controller.reads[-1])/runtime <= rate_limit:
            break

def reset(c, config=None, enforce=False, verbose=False, modify_power=False, vdda=46020):
    if modify_power:
        c.io.set_reg(0x00000010, 0, io_group=io_group)
        time.sleep(0.1)
        set_pacman_power(c, vdda=vdda)
    ##### issue hard reset (resets state machines and configuration memory)
    if not config is None:
        new_controller = main(controller_config=config, modify_power=modify_power, verbose=verbose, enforce=enforce)
        return new_controller

    c.io.reset_larpix(length=10240)
    # resets uart speeds on fpga
    for io_group, io_channels in c.network.items():
        for io_channel in io_channels:
            c.io.set_uart_clock_ratio(io_channel, clk_ctrl_2_clk_ratio_map[0], io_group=io_group)

                
    ##### re-initialize network
    c.io.group_packets_by_io_group = False # throttle the data rate to insure no FIFO collisions
    for io_group, io_channels in c.network.items():
        for io_channel in io_channels:
            c.init_network(io_group, io_channel, modify_mosi=True)
            #c.init_network(io_group, io_channel, modify_mosi=True)

            
    ###### set uart speed (v2a at 2.5 MHz transmit clock, v2b fine at 5 MHz transmit clock)
    for io_group, io_channels in c.network.items():
        for io_channel in io_channels:
            chip_keys = c.get_network_keys(io_group,io_channel,root_first_traversal=False)
            for chip_key in chip_keys:
                c[chip_key].config.clk_ctrl = _default_clk_ctrl
                c.write_configuration(chip_key, 'clk_ctrl')

    for io_group, io_channels in c.network.items():
        for io_channel in io_channels:
            c.io.set_uart_clock_ratio(io_channel, clk_ctrl_2_clk_ratio_map[_default_clk_ctrl], io_group=io_group)
            #print('io_channel:',io_channel,'factor:',c.io.set_uart_clock_ratio(io_channel, clk_ctrl_2_clk_ratio_map[_default_clk_ctrl], io_group=io_group))

    ##### issue soft reset (resets state machines, configuration memory untouched)
    c.io.reset_larpix(length=24)

    ##### setup low-level registers to enable loopback
    chip_config_pairs=[]
    for chip_key, chip in reversed(c.chips.items()):
        initial_config = deepcopy(chip.config)
        c[chip_key].config.vref_dac = 185 # register 82
        c[chip_key].config.vcm_dac = 41 # register 83
        c[chip_key].config.adc_hold_delay = 15 # register 129
        c[chip_key].config.enable_miso_differential = [1,1,1,1] # register 125
        chip_config_pairs.append((chip_key,initial_config))
    c.io.double_send_packets = True
    c.io.group_packets_by_io_group = True
    chip_register_pairs = c.differential_write_configuration(chip_config_pairs, write_read=0, connection_delay=0.01)
    chip_register_pairs = c.differential_write_configuration(chip_config_pairs, write_read=0, connection_delay=0.01)
    flush_data(c)

    #for chip_key in c.chips:
    #    chip_registers = [(chip_key, i) for i in [82,83,125,129]]
    #    ok,diff = c.enforce_registers(chip_registers, timeout=0.01, n=10, n_verify=10)
    #    if not ok:
    #        raise RuntimeError(diff,'\nconfig error on chips',list(diff.keys()))
    c.io.double_send_packets = False
    c.io.group_packets_by_io_group = False
    
    if hasattr(c,'logger') and c.logger: c.logger.record_configs(list(c.chips.values()))
    return c
        
def main(controller_config=_default_controller_config, pacman_version=_default_pacman_version, logger=_default_logger, vdda=46020, vddd=40605, asic_config=None, reset=_default_reset, enforce=True, no_enforce=False, verbose=True, modify_power=True, return_bad_keys=False, retry=0, resume=False, **kwargs):
    if verbose: print('[START BASE]')
    ###### create controller with pacman io
    print(pacman_version) 
    c = larpix.Controller()
    c.io = larpix.io.PACMAN_IO(relaxed=True)
    if no_enforce: enforce = False

     ##### setup hydra network configuration
    if controller_config is None:
        print('no controller config!')
        c.add_chip(larpix.Key(1, _default_io_channel, _default_chip_id))
        c.add_network_node(1, _default_io_channel, c.network_names, 'ext', root=True)
        c.add_network_link(1, _default_io_channel, 'miso_us', ('ext',_default_chip_id), 0)
        c.add_network_link(1, _default_io_channel, 'miso_ds', (_default_chip_id,'ext'), _default_miso_ds)
        c.add_network_link(1, _default_io_channel, 'mosi', ('ext', _default_chip_id), _default_mosi)
    else:
        c.load(controller_config)

    for io_group in c.network.keys():
        io_channels = np.array(list(c.network[io_group].keys())).astype(int)
        tiles= utility_base.io_channel_list_to_tile(io_channels)
        #pacman_base.power_up(c.io, io_group, pacman_version, tile=tiles, vdda_dac=[vdda]*len(tiles), vddd_dac=[vddd]*len(tiles), ramp=False)         
        set_pacman_power(c, io_group)
    if logger:
        if verbose: print('logger enabled')
        if 'filename' in kwargs: c.logger = larpix.logger.HDF5Logger(filename=kwargs['filename'])
        else: c.logger = larpix.logger.HDF5Logger()
        print('filename:',c.logger.filename)
        c.logger.record_configs(list(c.chips.values()))


    ##### issue hard reset (resets state machines and configuration memory)
    if reset and not resume:
        c.io.reset_larpix(length=10240)
        time.sleep(10240*(1/(10e6)))
        c.io.reset_larpix(length=10240)
        time.sleep(10240*(1/(10e6)))
        # resets uart speeds on fpga
        for io_group, io_channels in c.network.items():
            for io_channel in io_channels:
                c.io.set_uart_clock_ratio(io_channel, clk_ctrl_2_clk_ratio_map[0], io_group=io_group)

    #c.io.set_reg(0x10014, 0x04, io_group=2)            
    ##### initialize network
    c.io.group_packets_by_io_group = False # throttle the data rate to insure no FIFO collisions
    for io_group, io_channels in c.network.items():
        for io_channel in io_channels:
            #c.init_network(io_group, io_channel, modify_mosi=False)
            c.init_network(io_group, io_channel, modify_mosi=False)
            
    ###### set uart speed (v2a at 2.5 MHz transmit clock, v2b fine at 5 MHz transmit clock)
    for io_group, io_channels in c.network.items():
        for io_channel in io_channels:
            chip_keys = c.get_network_keys(io_group,io_channel,root_first_traversal=False)
            for chip_key in chip_keys:
                c[chip_key].config.clk_ctrl = _default_clk_ctrl
                if not resume: c.write_configuration(chip_key, 'clk_ctrl')

    for io_group, io_channels in c.network.items():
        for io_channel in io_channels:
            if not resume: c.io.set_uart_clock_ratio(io_channel, clk_ctrl_2_clk_ratio_map[_default_clk_ctrl], io_group=io_group)
            #print('io_channel:',io_channel,'factor:',c.io.set_uart_clock_ratio(io_channel, clk_ctrl_2_clk_ratio_map[_default_clk_ctrl], io_group=io_group))


    ##### issue soft reset (resets state machines, configuration memory untouched)
    c.io.reset_larpix(length=24)

    if not (asic_config is None):
        config_loader.load_config_from_directory(c, asic_config)

    ##### setup low-level registers to enable loopback
    if verbose: print('setting base configuration')
    chip_config_pairs=[]
    for chip_key, chip in reversed(c.chips.items()):
        initial_config = deepcopy(chip.config)
        c[chip_key].config.vref_dac = 223 # register 82
        c[chip_key].config.vcm_dac = 68 # register 83
        c[chip_key].config.adc_hold_delay = 15 # register 129
        c[chip_key].config.enable_miso_differential = [1,1,1,1] # register 125
        chip_config_pairs.append((chip_key,initial_config))
    c.io.double_send_packets = True
    c.io.group_packets_by_io_group = True
    if not resume:
        chip_register_pairs = c.differential_write_configuration(chip_config_pairs, write_read=0, connection_delay=0.01)
        chip_register_pairs = c.differential_write_configuration(chip_config_pairs, write_read=0, connection_delay=0.01)
        flush_data(c)

    if not enforce: 
        print('enforcing:', enforce)
        if hasattr(c,'logger') and c.logger: c.logger.record_configs(list(c.chips.values()))
        if verbose: print('[FINISH BASE]')
        return c

    if resume:
        return c

    current=[[0]*33, [0]*33, [0]*33]
    for io_group, __ in c.network.items():
        pacman_base.disable_all_pacman_uart(c.io,io_group)
    print('enforcing configuration:', enforce)
    #for chip_key in c.chips:
    for chip_key in tqdm(c.chips,desc='configuring chips...',ncols=80,smoothing=0):
        ioch = int(chip_key.io_channel)
        iog = int(chip_key.io_group)
        if current[iog][ioch]==0: 
            current[iog]=[0]*33
            current[iog][ioch]=1
            pacman_base.enable_pacman_uart_from_io_channel(c.io, iog, [ioch])
        #chip_registers = [(chip_key, i) for i in [82,83,125,129]]
        chip_registers = [(chip_key, i) for i in range(c[chip_key].config.num_registers)]
        ok,diff = c.enforce_registers(chip_registers, timeout=0.1, n=10, n_verify=10)
        if not ok:
            print(diff,'\nconfig error on chips',list(diff.keys())) 
            #print('retrying...')
            #if retry < 5:
            #    retry = retry+1
            #    print('Retry attempt # ',retry)
            #    return main(controller_config=controller_config, pacman_version=pacman_version, logger=logger, vdda=vdda, reset=reset, enforce=True, no_enforce=False, verbose=verbose, modify_power=modify_power, retry=retry)
            #else: raise RuntimeError(diff,'\nconfig error on chips',list(diff.keys()))
            raise RuntimeError(diff,'\nconfig error on chips',list(diff.keys()))
    c.io.double_send_packets = False
    c.io.group_packets_by_io_group = False
    if verbose: print('base configuration successfully enforced')
  
    recheck=True
    if recheck:
        for chip_key in tqdm(c.chips,desc='re-checking chip configs...',ncols=80,smoothing=0):
            ioch = int(chip_key.io_channel)
            iog = int(chip_key.io_group)
            if current[iog][ioch]==0: 
                current[iog]=[0]*33
                current[iog][ioch]=1
                pacman_base.enable_pacman_uart_from_io_channel(c.io, iog, [ioch])
        #chip_registers = [(chip_key, i) for i in [82,83,125,129]]
            chip_registers = [(chip_key, i) for i in range(c[chip_key].config.num_registers)]
            ok,diff = c.verify_registers(chip_registers, timeout=0.1, n=5)
            if not ok:
                print(diff,'\nconfig error on chips',list(diff.keys())) 
     


    if hasattr(c,'logger') and c.logger: c.logger.record_configs(list(c.chips.values()))
    if verbose: print('[FINISH BASE]')
    if return_bad_keys: return c, []
    return c


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--controller_config', default=_default_controller_config, type=str, help='''Hydra network configuration file''')
    parser.add_argument('--pacman_version', default=_default_pacman_version, type=str, help='''Pacman version in use''')
    parser.add_argument('--logger', default=_default_logger, action='store_true', help='''Flag to create an HDF5Logger object to track data''')
    parser.add_argument('--no_enforce', action='store_true', default=False, help='''Flag whether to enforce config''')
    parser.add_argument('--no_reset', default=_default_reset, action='store_false', help='''Flag that if present, chips will NOT be reset, otherwise chips will be reset during initialization''')
    parser.add_argument('--vdda', default=46020, type=int, help='''VDDA setting during bringup''')
    args = parser.parse_args()
    c = main(**vars(args))


