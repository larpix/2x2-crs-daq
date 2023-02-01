import larpix
from signal import signal, SIGINT
import larpix.io
import argparse
import shutil
import time


_default_chip_key='All'
_default_register=None
_default_value=None
_default_controller_config=None
_default_channel=None

disabled=[38,6,8,9,7,39,40,55,54,23,22,24,56,25,57]
existing_value=[1 if i in disabled else 0 for i in range(64)]

def main(chip_key=_default_chip_key, \
        register=_default_register,\
        value=_default_value,\
        channel=_default_channel,\
        controller_config=_default_controller_config,\
         **kwargs):

    c = larpix.Controller()
    c.io = larpix.io.PACMAN_IO(relaxed=True)
    
    chips_to_write=[]
    c.load(controller_config)
    if chip_key=='All': 
        chips_to_write=list(c.chips)

    else:
        chips_to_write=[chip_key]
        #else:
        #    raise RuntimeError('Invalid Chip Key')

    chip_reg_pairs=[]
    for chip in chips_to_write: 
        chip_reg_pairs.append((chip, c[chip].config.register_map[register]))
    
    for chip in chips_to_write:
        new_register_value = existing_value#getattr(c[chip_key], register)
        new_register_value[channel]=value
        setattr(c[chip_key].config, register, new_register_value)

    print(chip_reg_pairs)
    print(getattr(c[chip].config, register) )
    ok, diff = c.enforce_registers(chip_reg_pairs, timeout=0.1, connection_delay=0.1, n=10, n_verify=10)
    #ok=False
    if not ok:
        print('Error enforcing configuration:', diff)
    else:
        print('Done')


    return c, c.io



if __name__=='__main__':
    parser = argparse.ArgumentParser()
    #parser.add_argument('--LRS', default=_default_LRS, \
    #                    action='store_true', help='''True to run LRS''')
    parser.add_argument('--chip_key', default=_default_chip_key, \
                        type=str, help='''Chip key, default All''')
    parser.add_argument('--register', default=_default_register, \
                        type=str, help='''Register to set''')
    parser.add_argument('--channel', default=_default_channel, \
                        type=int, help='''Channel to modify''')

    parser.add_argument('--value', default=_default_value, \
                        type=int, help='''Register value to set''')
    parser.add_argument('--controller_config', default=_default_controller_config,\
                        type=str, help='''Path to hydra config JSON ''')

    

    args=parser.parse_args()
    main(**vars(args))
