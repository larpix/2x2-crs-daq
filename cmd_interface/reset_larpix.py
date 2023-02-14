import larpix
from signal import signal, SIGINT
import larpix.io
import argparse
import shutil
import time


_default_chip_key='All'
_default_register=None
_default_length=2048
_default_controller_config=None

def main(chip_key=_default_chip_key, \
        register=_default_register,\
        length=_default_length,\
        controller_config=_default_controller_config,\
         **kwargs):

    c = larpix.Controller()
    c.io = larpix.io.PACMAN_IO(relaxed=True)
    
    c.load(controller_config)
    mclock = 10e6
    for io_group, io_channels in c.network.items():
        c.io.reset_larpix(length=int(length*mclock), io_group=int(io_group) )
    
    return c, c.io



if __name__=='__main__':
    parser = argparse.ArgumentParser()
    #parser.add_argument('--LRS', default=_default_LRS, \
    #                    action='store_true', help='''True to run LRS''')
    parser.add_argument('--chip_key', default=_default_chip_key, \
                        type=str, help='''Chip key, default All''')
    parser.add_argument('--register', default=_default_register, \
                        type=str, help='''Register to set''')
    parser.add_argument('--length', default=_default_length, \
                        type=int, help='''reset length in seconds''')
    parser.add_argument('--controller_config', default=_default_controller_config,\
                        type=str, help='''Path to hydra config JSON ''')

    

    args=parser.parse_args()
    main(**vars(args))
