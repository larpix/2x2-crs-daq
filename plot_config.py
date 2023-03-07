import numpy as np
from matplotlib import pyplot as plt
import argparse
from base import config_loader
import json
def main(*files, register, **kwargs):
        if register is None:
            return
        vals=[]
        for file in files:
                config={}
                with open(file, 'r') as f: config=json.load(f)
                
                value=config[register]
                value=list( np.array(value)[config['csa_enable']] )
                vals+=value

        fig=plt.figure()
        ax=fig.add_subplot()
        ax.hist(vals, bins=32, range=(0,31), label=register)
        ax.grid()
        ax.legend()
        ax.set_title('Module3 Run 2 ASIC Configs')
        ax.set_xlabel('register value')
        ax.set_ylabel('channel count')
        fig.savefig('config_hist.png')

                
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('input_files', nargs='+', help='''files to modify''')
    parser.add_argument('--register', type=str, default=None, help='''Register to modify''')
    args = parser.parse_args()
    
    main(
        *args.input_files,
        register=args.register
    )
