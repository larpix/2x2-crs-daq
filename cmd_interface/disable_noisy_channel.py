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
    
    key =  larpix.key.Key(chip_key)
    
    #print('initializing network to correct values...') 
    #ok, diff = c.init_network_and_verify(key.io_group, key.io_channel, modify_mosi=True)
    #print('done')
    #print('initializing network')
    #print('done')
   
#    network=config['network']
#    miso_us_uart_map=network['miso_us_uart_map']
#    miso_ds_uart_map=network['miso_ds_uart_map']
#    mosi_uart_map=network['mosi_uart_map']
#    subnetwork = network[ str(key.io_group) ][ str(key.io_channel) ]
#    nodes = subnetwork['nodes']
#   
#    mosi_disable = []
#    for item in nodes:
#        miso_us=item['miso_us']
#        chip_id = item['chip_id']
#        if chip_id=='ext': continue
#        chipkey='{}-{}-{}'.format(key.io_group, key.io_channel, chip_id)
#        if chipkey==chip_key: break
#        #c.add_chip(chipkey)
#        #print(c[chipkey].config.enable_mosi)
#        #c[chipkey].chip_id=chip_id
#        for idx in range(4):
#            if not miso_us[idx] is None:
#                #print(mosi_uart_map[idx], idx, miso_us_uart_map[idx], miso_ds_uart_map[idx])
#                c[chipkey].config.enable_mosi[idx]=0
#                mosi_disable.append(chipkey)
#                for i in range(100):
#                    c.write_configuration(chipkey, 'enable_mosi') 
#                    c.write_configuration(chipkey, 'enable_mosi')
#                if chip_id in [11,41,71,101]:
#                    ok, diff= c.enforce_registers( [ (chipkey, c[chipkey].config.register_map['enable_mosi'] )] )
#                    print(ok, diff)
#                time.sleep(0.3)
#                #print(c[chipkey].config.enable_mosi) 
#                print('writing mosi disable to chip id', chip_id)
#                continue
    

    
    disabled={}
    with open(disabled_json, 'r') as f: disabled=json.load(f)
    d=disabled[chip_key]
    mask=[1 if i in d else 0 for i in range(64)]
    mask[channel]=1
    chip_reg_pairs=[]
    
    chips_to_write=[chip_key]
    print('Writing Disable...')
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

        for i in range(25):
            c.write_configuration(broadcast, 'test_mode_uart0')
            c.write_configuration(broadcast, 'test_mode_uart1')
            c.write_configuration(broadcast, 'test_mode_uart2')
            c.write_configuration(broadcast, 'test_mode_uart3')
        disabled[chip]+=[channel] 
        setattr(c[chip].config,register,mask)
        chip_reg_pairs.append((chip, c[chip].config.register_map[register]))
        c.write_configuration(chip, register)
        c.write_configuration(chip, register)  
    
#    print('initializing network to correct values...') 
#    for chipkey in mosi_disable:
#        c[chip_key].config.enable_mosi=[1,1,1,1]
#        ok, diff= c.enforce_registers( [ (chipkey, c[chipkey].config.register_map['enable_mosi'] )], timeout=0.2, n=5, n_verify=5, connection_delay=0.02 )
#    #c.load(controller_config)
#    #ok, diff= c.init_network_and_verify(key.io_group, key.io_channel, modify_mosi=True)
#        if ok:
#            print('done', chip_key)
#        else:
#            print(diff)
#
#    #print(chip_reg_pairs)
#    for pair in chip_reg_pairs:
#        print(pair)#, '\t', getattr(c[pair[0]].config, c[pair[0]].config.register_names[pair[1][0]] ))
    
    ok, diff = c.enforce_registers(chip_reg_pairs, timeout=0.2, connection_delay=0.1, n=5, n_verify=5)
    
    with open(disabled_json, 'w') as f: json.dump(disabled, f)
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
    parser.add_argument('--channel', default=_default_value, \
                        type=int, help='''Channel on chip to disable''')

    parser.add_argument('--disabled_json', default=_default_controller_config,\
                        type=str, help='''Path to hydra config JSON ''')


    parser.add_argument('--value', default=_default_value, \
                        type=int, help='''Register value to set''')
    parser.add_argument('--controller_config', default=_default_controller_config,\
                        type=str, help='''Path to hydra config JSON ''')

    

    args=parser.parse_args()
    main(**vars(args))
