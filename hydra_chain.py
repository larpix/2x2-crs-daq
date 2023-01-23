import sys
import time
import argparse
from base import graphs
import larpix
import larpix.io
import larpix.logger
from base import generate_config
from base import pacman_base
from tqdm import tqdm
import numpy as np
import json
from base import v2a_base
from base.v2a_base import *

def string_to_chips_list(string):
        chiplist = string.split(',')
        return [int(chip) for chip in chiplist]

def convert_voltage_for_pacman(voltage):
        max_voltage, max_scale = 1.8, 46020
        v = voltage
        if v > max_voltage: v=max_voltage
        return int( (v/max_voltage)*max_scale )

arr = graphs.NumberedArrangement()

def get_temp_key(io_group, io_channel):
        return larpix.key.Key(io_group, io_channel, 1)

def get_good_roots(c, io_group, io_channels):
        #root chips with external connections to pacman
        root_chips = [11, 41, 71, 101]
        print('getting good roots...')
        good_tile_channel_indices = []
        for n, io_channel in enumerate(io_channels):

                #writing initial config
                key = larpix.key.Key(io_group, io_channel, 1)
                c.add_chip(key)

                c[key].config.chip_id = root_chips[n]
                c.write_configuration(key, 'chip_id')
                c.remove_chip(key)

                key = larpix.key.Key(io_group, io_channel, root_chips[n])
                c.add_chip(key)
                c[key].config.chip_id = key.chip_id

                c[key].config.enable_miso_downstream = [1,0,0,0]
                c[key].config.enable_miso_differential = [1,1,1,1]
                c.write_configuration(key, 'enable_miso_downstream')

                ###############################################################################


                #resetting clocks

                c[key].config.enable_miso_downstream=[0]*4
                c[key].config.enable_miso_upstream=[0]*4
                c.write_configuration(key, 'enable_miso_downstream')
                c.write_configuration(key, 'enable_miso_upstream')
                c[key].config.clk_ctrl = v2a_base._default_clk_ctrl
                c.write_configuration(key, 'clk_ctrl')
                c.io.set_uart_clock_ratio(io_channel, clk_ctrl_2_clk_ratio_map[v2a_base._default_clk_ctrl], io_group=io_group)
                print("setting uart clock ratio to:",clk_ctrl_2_clk_ratio_map[v2a_base._default_clk_ctrl]) 
         
                ################################################################################

                #rewriting config
                c[key].config.enable_miso_downstream = [1,0,0,0]
                c[key].config.enable_miso_differential = [1,1,1,1]
                c.write_configuration(key, 'enable_miso_differential')
                c.write_configuration(key, 'enable_miso_downstream')

                #enforcing configuration on chip
                ok,diff = c.enforce_registers([(key,122), (key, 125)], timeout=0.1, n=5, n_verify=5)
                if ok:
                        good_tile_channel_indices.append(n)
                        print('verified root chip ' + str(root_chips[n]))
                else:
                        print('unable to verify root chip ' + str(root_chips[n]))

        #checking each connection for every chip
        good_roots = [root_chips[n] for n in good_tile_channel_indices]
        good_channels = [io_channels[n] for n in good_tile_channel_indices]

        print('Found working root chips: ', good_roots)

        return good_roots, good_channels

def get_initial_controller(io_group, io_channels, vdda=0, pacman_version='v1rev3b'):
        #creating controller with pacman io
        c = larpix.Controller()
        c.io = larpix.io.PACMAN_IO(relaxed=True)
        c.io.double_send_packets = True
        print('getting initial controller')
        if pacman_version == 'v1rev3b':
                print('setting power,', vdda)
                vddd_voltage = 1.6
                vddd = convert_voltage_for_pacman(vddd_voltage)
                vdda = convert_voltage_for_pacman(vdda)
                reg_pairs = get_reg_pairs(io_channels)
                for pair in reg_pairs:
                        c.io.set_reg(pair[0], vdda, io_group=io_group)
                        c.io.set_reg(pair[1], vddd, io_group=io_group)
                tiles = get_all_tiles(io_channels)
                bit_string = list('100000000') # prepended '1' to enable the clock
                for tile in tiles: bit_string[-1*tile] = '1'
                c.io.set_reg(0x00000014, 1, io_group=io_group) # enable global larpix power
                print(bit_string)
                print(int("".join(bit_string),2))
                c.io.set_reg(0x00000010, int("".join(bit_string), 2), io_group=io_group) # enable tiles to be powered
                c.io.set_reg(0x101C, 4, io_group=io_group)
                c.io.set_reg(0x18, 0xffffffff, io_group=io_group) # enable uarts (for all tiles?)

                power = power_registers()
                adc_read = 0x00024001
                for i in power.keys():
                        val_vdda = c.io.get_reg(adc_read+power[i][0], io_group=io_group)
                        val_idda = c.io.get_reg(adc_read+power[i][1], io_group=io_group)
                        val_vddd = c.io.get_reg(adc_read+power[i][2], io_group=io_group)
                        val_iddd = c.io.get_reg(adc_read+power[i][3], io_group=io_group)
                        print('TILE',i,
                                  '\tVDDA:',(((val_vdda>>16)>>3)*4),
                                  '\tIDDA:',(((val_idda>>16)-(val_idda>>31)*65535)*500*0.01),
                                  '\tVDDD:',(((val_vddd>>16)>>3)*4),
                                  '\tIDDD:',(((val_iddd>>16)-(val_iddd>>31)*65535)*500*0.01))

        #adding pacman!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        for io_channel in io_channels:
                c.add_network_node(io_group, io_channel, c.network_names, 'ext', root=True)
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        #resetting larpix
        c.io.reset_larpix(length=10240, io_group=io_group)
        for io_channel in io_channels:
                c.io.set_uart_clock_ratio(io_channel, clk_ctrl_2_clk_ratio_map[0], io_group=io_group)
                print("setting uart clock ratio to:",clk_ctrl_2_clk_ratio_map[0]) 
        ###################################################################################
        pacman_base.enable_pacman_uart_from_tile(c.io, io_group, [tile] )
        
        return c

def reset_board_get_controller(c, io_group, io_channels):
        #resetting larpix
        c.io.reset_larpix(length=10240)
        for io_channel in io_channels:
                c.io.set_uart_clock_ratio(io_channel, clk_ctrl_2_clk_ratio_map[0], io_group=io_group)
                print("setting uart clock ratio to:",clk_ctrl_2_clk_ratio_map[0]) 
        c.chips.clear()
        ###################################################################################
        return c

def init_initial_network(c, io_group, io_channels, paths):
        root_chips = [path[0] for path in paths]

        still_stepping = [True for root in root_chips]
        ordered_chips_by_channel = [ [] for io_channel in io_channels  ]

        for ipath, path in enumerate(paths):

                step = 0

                while step < len(path)-1:
                        step += 1
                        next_key = larpix.key.Key(io_group, io_channels[ipath], path[step])
                        prev_key = larpix.key.Key(io_group, io_channels[ipath], path[step-1])

                        if prev_key.chip_id in root_chips:
                                #this is the first step. need to re-add root chip
                                temp_key = get_temp_key(io_group, io_channels[ipath])
                                c.add_chip(temp_key)
                                c[temp_key].config.chip_id = prev_key.chip_id
                                c.write_configuration(temp_key, 'chip_id')
                                c.remove_chip(temp_key)
                                c.add_chip(prev_key)
                                c[prev_key].config.chip_id = prev_key.chip_id
                                c[prev_key].config.enable_miso_downstream = arr.get_uart_enable_list(prev_key.chip_id)
                                c[prev_key].config.enable_miso_differential = [1,1,1,1]
                                c.write_configuration(prev_key, 'enable_miso_downstream')
                                c.write_configuration(prev_key, 'enable_miso_differential')
                                ordered_chips_by_channel[ipath].append(prev_key.chip_id)
                        
                        c[prev_key].config.enable_miso_upstream = arr.get_uart_enable_list(prev_key.chip_id, next_key.chip_id)
                        c.write_configuration(prev_key, 'enable_miso_upstream')

                        temp_key = get_temp_key(io_group, io_channels[ipath])
                        c.add_chip(temp_key)
                        c[temp_key].config.chip_id = next_key.chip_id
                        c.write_configuration(temp_key, 'chip_id')
                        c.remove_chip(temp_key)

                        c.add_chip(next_key)
                        c[next_key].config.chip_id = next_key.chip_id
                        c[next_key].config.enable_miso_downstream = arr.get_uart_enable_list(next_key.chip_id, prev_key.chip_id)
                        c[next_key].config.enable_miso_differential =[1,1,1,1]
                        c.write_configuration(next_key, 'enable_miso_downstream')
                        ordered_chips_by_channel[ipath].append(next_key.chip_id)
                        
                for chip_ids in ordered_chips_by_channel[ipath][::-1]:
                        key = larpix.key.Key(io_group, io_channels[ipath], chip_ids)
                        c[key].config.enable_miso_downstream=[0]*4
                        c[key].config.enable_miso_upstream=[0]*4
                        c.write_configuration(key, 'enable_miso_downstream')
                        c.write_configuration(key, 'enable_miso_upstream')
                        c[key].config.clk_ctrl = v2a_base._default_clk_ctrl
                        c.write_configuration(key, 'clk_ctrl')
                c.io.set_uart_clock_ratio(io_channels[ipath], clk_ctrl_2_clk_ratio_map[v2a_base._default_clk_ctrl], io_group=io_group)
                print("setting uart clock ratio to:",clk_ctrl_2_clk_ratio_map[v2a_base._default_clk_ctrl]) 

        return True

def test_network(c, io_group, io_channels, paths):
        print('Testing io-group {} io_channels'.format(io_group), io_channels)
        root_chips = [path[0] for path in paths]
        step = 0
        still_stepping = [True for path in paths]
        valid = [True for path in paths]
        pbar=tqdm(total=np.sum([len(p) for p in paths]))
        while any(still_stepping):
                step += 1 
#tqdm(c.chips,desc='configuring chips...',ncols=80,smoothing=0)
                for ipath, path in enumerate(paths):
                         
                        if not still_stepping[ipath] or not valid[ipath]:
                                continue

                        if step > len(path)-1:
                                still_stepping[ipath] = False
                                continue
                        next_key = larpix.key.Key(io_group, io_channels[ipath], path[step])
                        prev_key = larpix.key.Key(io_group, io_channels[ipath], path[step-1])
                        if prev_key.chip_id in root_chips:
                                c[prev_key].config.chip_id = prev_key.chip_id
                                c[prev_key].config.enable_miso_downstream = arr.get_uart_enable_list(prev_key.chip_id)
                                c[prev_key].config.enable_miso_differential = [1,1,1,1]
                                c.write_configuration(prev_key, 'enable_miso_downstream')

                        c[prev_key].config.enable_miso_upstream = arr.get_uart_enable_list(prev_key.chip_id, next_key.chip_id)
                        c.write_configuration(prev_key, 'enable_miso_upstream')

                        c[next_key].config.chip_id = next_key.chip_id
                        c[next_key].config.enable_miso_downstream = arr.get_uart_enable_list(next_key.chip_id, prev_key.chip_id)
                        c[next_key].config.enable_miso_differential =[1,1,1,1]
                        c.write_configuration(next_key, 'enable_miso_downstream')

                        #if (path[step-1], path[step]) in arr.good_connections:
                        #        #already verified links
                        #        print(next_key, 'already verified')
                        #        continue

                        ok, diff = c.enforce_registers([(next_key, 122)], timeout=0.5, n=3)
                        pbar.update(1)
                        if ok:
                                arr.add_good_connection((path[step-1], path[step])) 
                                continue

                        else:
                                #planned path to traverse has been interrupted... restart with adding excluded link
                                arr.add_onesided_excluded_link((prev_key.chip_id, next_key.chip_id))
                                still_stepping[ipath] = False
                                valid[ipath] = False
        pbar.close()
        return all(valid)

def main(pacman_tile, io_group, pacman_version, vdda=0, exclude=None):
    d = {'_config_type' : 'controller', '_include':[]}
    if isinstance(pacman_tile, list):
        if exclude is None: exclude = {t : None for t in pacman_tile}
        for tile in pacman_tile:
            d['_include'].append(hydra_chain(io_group, tile, pacman_version, vdda, exclude[tile]))
    if isinstance(pacman_tile, int):
        d['_include'].append(hydra_chain(io_group, pacman_tile, pacman_version, vdda, exclude))
    
    config_name = 'config-{}.json'.format(time.strftime("%Y_%m_%d_%H_%M_%Z"))
    with open(config_name, 'w') as f: json.dump(d, f)

    c = larpix.Controller()
    c.io = larpix.io.PACMAN_IO(relaxed=True)
    if isinstance(pacman_tile, list): pacman_base.enable_pacman_uart_from_tile(c.io, io_group, pacman_tile )
    else: pacman_base.enable_pacman_uart_from_tile(c.io, io_group, [pacman_tile] )

    c = v2a_base.main(controller_config=config_name, enforce=True)
    c = v2a_base.reset(c, config_name, enforce=True)


    c.io.set_reg(0x00000010, 0, io_group=io_group)
    return c, c.io   

def hydra_chain(io_group, pacman_tile, pacman_version, vdda, exclude): 
        
        io_channels = [ 1 + 4*(pacman_tile - 1) + n for n in range(4)]
        print("--------------------------------------------")
        print("get_initial_controller(",io_group,",",io_channels,",",vdda,",",pacman_version,")")
        c = get_initial_controller(io_group, io_channels, vdda, pacman_version)

        root_chips, io_channels = get_good_roots(c, io_group, io_channels)
        print('found root chips:', root_chips)
        c = reset_board_get_controller(c, io_group, io_channels)

        #need to init whole network first and write clock frequency, then we can step through and test

        existing_paths = [ [chip] for chip in root_chips  ]

        #initial network
        paths = arr.get_path(existing_paths)
        print('path including', sum(  [len(path) for path in paths] ), 'chips' )

        #bring up initial network and set clock frequency
        init_initial_network(c, io_group, io_channels, paths)
        #test network to make sure all chips were brought up correctly
        ok = test_network(c, io_group, io_channels, paths)

        while not ok:
                c = reset_board_get_controller(c, io_group, io_channels)

                existing_paths = [ [chip] for chip in root_chips  ]

                #initial network
                paths = arr.get_path(existing_paths)
                print('path inlcuding', sum(  [len(path) for path in paths] ), 'chips' )

                #bring up initial network and set clock frequency
                init_initial_network(c, io_group, io_channels, paths)

                #test network to make sure all chips were brought up correctly
                ok = test_network(c, io_group, io_channels, paths)

        #existing network is full initialized, start tests
        ######
        ##generating config file
        _name = "pacman-tile-"+str(pacman_tile)+"-hydra-network.json"

        if True:
                print('writing configuration', _name + ', including', sum(  [len(path) for path in paths] ), 'chips'  )
                generate_config.write_existing_path(_name, io_group, root_chips, io_channels, paths, ['no test performed'], arr.excluded_chips, asic_version=2, script_version=v2a_base.LARPIX_10X10_SCRIPTS_VERSION)
        return _name 

if __name__ == '__main__':
        parser = argparse.ArgumentParser()
        parser.add_argument('--pacman_tile', default=1, type=int, help='''Pacman software tile number; 1-8  for Pacman v1rev3; 1 for Pacman v1rev2''')
        parser.add_argument('--pacman_version', default='v1rev3b', type=str, help='''Pacman version; v1rev2 for SingleCube; otherwise, v1rev3''')
        parser.add_argument('--vdda', default=0, type=float, help='''VDDA setting during test''')
        parser.add_argument('--io_group', default=1, type=int, help='''IO group to perform test on''')
        parser.add_argument('--exclude', default=None, type=str, help='''Chips to exclude chip from test and networks, formatted chip_id_1,chip_id_2,...''')
        args = parser.parse_args()
        c = main(**vars(args))
        ###### disable tile power


