import json
import sys

#file1 = 'reference/run2_everything_on/pedestal-disable.json'
#file2 = 'reference/full-disable.json'

def main(file1, file2, tag1=None, tag2=None):
    print('Combining', file1, file2)
    d1 = {}
    d2 = {}
    with open(file1, 'r') as f1:
        d1 = json.load(f1)

    with open(file2, 'r') as f2:
        d2 = json.load(f2)

    ch1 = []
    ch2 = []
    
    for n in range(1, 65):
        cc1 = 0
        for key in d1.keys(): cc1 += d1[key].count(n) 
        ch1.append(cc1)
        
        cc2 = 0
        for key in d2.keys(): cc2 += d2[key].count(n) 
        ch2.append(cc2)
    print(tag1, sum(ch1))
    print(tag2, sum(ch2))
    from matplotlib import pyplot as plt
    fig = plt.figure()
    ax = fig.add_subplot()
    ax.set_title('disabled channels')
    ax.set_xlabel('channel id')
    ax.set_ylabel('count disabled')
    ax.plot(list(range(1, 65)), ch1, drawstyle='steps-mid', label=tag1, alpha=0.5)
    ax.plot(list(range(1, 65)), ch2, drawstyle='steps-mid', label=tag2, alpha=0.5)
    plt.legend()
    plt.show()
    #print(d1, d2)
    fd = {}
    for key in d1.keys():
        fd[key]=d1[key]
    for key in d2.keys():
        if key in fd.keys(): fd[key]= list(set(fd[key] + d2[key]) )
        else: fd[key] = d2[key]

    with open('full-disable.json', 'w') as f:
        json.dump(fd, f, indent=4)
    
if __name__=='__main__':
    if len(sys.argv)==3:
        main(sys.argv[1], sys.argv[2])
    if len(sys.argv)==5:
        main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print('check your arguments')


