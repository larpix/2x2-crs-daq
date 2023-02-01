import json
import larpix
from signal import signal, SIGINT
import larpix.io
import argparse
import shutil
import time


_default_chip_key='All'
_default_register='channel_mask'
_default_value=None
_default_controller_config=None
def main(chip_key=_default_chip_key, \
        register=_default_register,\
        value=_default_value,\
        controller_config=_default_controller_config,\
        disabled_json=None,\
        old_disabled_json=None,\
        channel=None,
         **kwargs):

    c = larpix.Controller()
    c.io = larpix.io.PACMAN_IO(relaxed=True)
    config={}
    
    with open(controller_config, 'r') as f:
        config = json.load(f)

    chips_to_write=[]
    print('loading controller:')
    c.load(controller_config)
    print('done')
        
    disabled={}
    with open(disabled_json, 'r') as f: disabled=json.load(f)
    
    disabled_old={}
    with open(old_disabled_json, 'r') as f: disabled_old=json.load(f)

    #mask[channel]=1
    chip_reg_pairs=[]
    
    print('Writing Disable...')
    chip_reg_pairs=[]
    for chip in disabled.keys():
        if not chip in c.chips: continue#c.add_chip(chip)
        d=disabled[chip]
        d_old=[]
        if chip in disabled_old.keys():
            d_old=disabled_old[chip]
        print('disabling channels, ', d+d_old )
        mask=[1 if i in (d_old+d) else 0 for i in range(64)]
        setattr(c[chip].config,register,mask)
        chip_reg_pairs.append((chip, c[chip].config.register_map[register]))
        c.write_configuration(chip, register)
        c.write_configuration(chip, register)  
    
    ok, diff = c.enforce_registers(chip_reg_pairs, timeout=0.2, n=5, n_verify=5)

    if not ok:
        print('Error enforcing configuration:', diff)
    else:
        print('Done')


    return c, c.io



if __name__=='__main__':
    parser = argparse.ArgumentParser()
    #parser.add_argument('--LRS', default=_default_LRS, \
    #                    action='store_true', help='''True to run LRS''')
    parser.add_argument('--register', default=_default_register, \
                        type=str, help='''Register to set''')
    parser.add_argument('--disabled_json', default=_default_controller_config,\
                        type=str, help='''Path to hydra config JSON ''')
    parser.add_argument('--old_disabled_json', default=_default_controller_config,\
                        type=str, help='''Path to hydra config JSON ''')



    parser.add_argument('--value', default=_default_value, \
                        type=int, help='''Register value to set''')
    parser.add_argument('--controller_config', default=_default_controller_config,\
                        type=str, help='''Path to hydra config JSON ''')

    

    args=parser.parse_args()
    main(**vars(args))
