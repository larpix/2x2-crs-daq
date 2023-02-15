import json
import larpix
from signal import signal, SIGINT
import larpix.io
import argparse
import shutil
import time
from copy import copy

register='channel_mask'
_default_controller_config=None

def main(controller_config=_default_controller_config,\
         **kwargs):

    c = larpix.Controller()
    c.io = larpix.io.PACMAN_IO(relaxed=True)
    config={}
    
    with open(controller_config, 'r') as f:
        config = json.load(f)

    print('loading controller:')
    c.load(controller_config)
    print('done')
    
    chips_to_write=copy(list(c.chips.keys()) )
    chip_reg_pairs=[]
    
    for chip in chips_to_write:
        
        key = larpix.key.Key(chip)
        iog = key.io_group
        ioch = key.io_channel
        broadcast=larpix.key.Key(iog, ioch, 255)
        c.add_chip(broadcast)
        c[broadcast].config.test_mode_uart0=0
        c[broadcast].config.test_mode_uart1=0
        c[broadcast].config.test_mode_uart2=0
        c[broadcast].config.test_mode_uart3=0
        c[broadcast].config.channel_mask=[1]*64
        c[broadcast].config.csa_enable=[0]*64

        for i in range(5):
            c.write_configuration(broadcast, 'channel_mask')
            c.write_configuration(broadcast, 'csa_enable')
            c.write_configuration(broadcast, 'test_mode_uart0')
            c.write_configuration(broadcast, 'test_mode_uart1')
            c.write_configuration(broadcast, 'test_mode_uart2')
            c.write_configuration(broadcast, 'test_mode_uart3')
        
        c.remove_chip(broadcast)

        chip_reg_pairs.append((chip, c[chip].config.register_map[register]))
    
    ok, diff = c.enforce_registers(chip_reg_pairs, timeout=0.2, connection_delay=0.1, n=5, n_verify=5)
    
    print(ok, diff)

    return c, c.io



if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--controller_config', default=_default_controller_config,\
                        type=str, help='''Path to hydra config JSON ''')

    

    args=parser.parse_args()
    main(**vars(args))
