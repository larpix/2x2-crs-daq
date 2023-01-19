import json
io_groups = [1, 2]
io_channels = list(range(1, 32, 1))
chip_ids = list(range(11, 112, 1))
channels = [24]


d = {}

for iog in io_groups:
    for ioch in io_channels:
        for chip in chip_ids:
            key = '{}-{}-{}'.format(iog, ioch, chip)
            d[key]=channels


with open('disable-24.json', 'w') as f: json.dump(d, f)
