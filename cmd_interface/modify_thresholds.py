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
_default_configuration_dir=None
_default_channel=list(range(64))

def main(chip_key=_default_chip_key, \
        register=_default_register,\
        value=_default_value,\
        chip_key='All',\
        channel=None,\
        controller_config=_default_controller_config,\
        configuration_dir=_default_configuration_dir,\
         **kwargs):

    c = larpix.Controller()
    c.io = larpix.io.PACMAN_IO(relaxed=True)
    
    if channel is None: channel=_default_channel
    else: channel=[channel]


    configs={}
    config_files = [file for file os.listdir(configuration_dir) if file[-5:]=='.json']
    for file in config_files:
        d={}
        with open(configuration_dir+'/'+file, 'rw') as f: d=json.load(f)
        for key in d.keys():
            configs[key]=d[key]
            
    
    chips_to_write=[]
    if chip_key=='All':
        chips_to_write=c.chips
    else:
        chips_to_write=[chip_key]   

    chip_reg_pairs=[]
    for chip in chips_to_write:
        if register=='pixel_trim_dac':
            val=configs[chip_key]['pixel_trim_dac']
            for ch in channel:
                val[ch]+=value
            setattr(c[chip].config,register,val)
        else if register=='threshold_global':
            val=configs[chip_key]['threshold_global']
            val+=value
            setattr(c[chip].config,register,val)
            
        chip_reg_pairs.append((chip, c[chip].config.register_map[register]))
        c.write_configuration(chip, register)
        c.write_configuration(chip, register)  
    
    ok, diff = c.enforce_registers(chip_reg_pairs, timeout=0.1, connection_delay=0.1, n=10, n_verify=10)

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
    parser.add_argument('--channel', default=None, \
                        type=int, help='''Channel to change for pixel trim only, defaults to All''')

    parser.add_argument('--value', default=_default_value, \
                        type=int, help='''Register value to set''')
    parser.add_argument('--configuration_dir', default=None,\
                        type=str, help='''Path to directory with threshold configs ''')


    parser.add_argument('--controller_config', default=_default_controller_config,\
                        type=str, help='''Path to hydra config JSON ''')

    

    args=parser.parse_args()
    main(**vars(args))
