import argparse
from base import config_loader
import json
def main(*files, register, value, **kwargs):
        if register is None or value is None:
            return

        for file in files:
                config={}
                with open(file, 'r') as f: config=json.load(f)
                
                config[register]=value

                with open(file, 'w') as f: json.dump(config, f, indent=4)

                
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('input_files', nargs='+', help='''files to modify''')
    parser.add_argument('--register', type=str, default=None, help='''Register to modify''')
    parser.add_argument('--value', type=int, default=None, help='''value to set''')
    args = parser.parse_args()
    
    main(
        *args.input_files,
        value=args.value,
        register=args.register
    )
