import json
import os

workdir = '.'



full_config={}

for file in sorted(os.listdir(workdir)):
    print(file[:-5])
    d={}
    if file[-5:]=='.json':
        with open(file, 'r') as f: d= json.load(f)

    for key in d.keys():
        if not key in full_config.keys(): full_config[key] = {}
        if not key=='network':
            full_config[key]=d[key]
        else:
            for kkey in d[key]: #io group
                if not kkey in full_config['network'].keys(): full_config['network'][kkey] = {}
                for kkkey in d[key][kkey]:
                    full_config['network'][kkey][kkkey]=d[key][kkey][kkkey]




with open('combined_module3_config.json', 'w') as f: json.dump(full_config, f, indent=4)



    