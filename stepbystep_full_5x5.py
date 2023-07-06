import larpix
import larpix.io
#from base import utility_base
from base import pacman_base
import time

def tile_to_io_channel(tile):
    io_channel=[]
    for t in tile:
        for i in range(1,5,1):
            io_channel.append( ((t-1)*4)+i )
    return io_channel

def invert_pacman_uart(io, io_group, asic_version, tile):
    #if asic_version!='2b': return
    tile = [tile]
    inversion_registers={1:0x0301c, 2:0x0401c, 3:0x0501c, 4:0x0601c,
                         5:0x0701c, 6:0x0801c, 7:0x0901c, 8:0x0a01c,
                         9:0x0b01c, 10:0x0c01c, 11:0x0d01c, 12:0x0e01c,
                         13:0x0f01c, 14:0x1001c, 15:0x1101c, 16:0x1201c,
                         17:0x1301c, 18:0x1401c, 19:0x1501c, 20:0x1601c,
                         21:0x1701c, 22:0x1801c, 23:0x1901c, 24:0x1a01c,
                         25:0x1b01c, 26:0x1c01c, 27:0x1d01c, 28:0x1e01c,
                         29:0x1f01c, 30:0x2001c, 31:0x2101c, 32:0x2201c}
    io_channel=tile_to_io_channel(tile)
    for ioc in io_channel:
        io.set_reg(inversion_registers[ioc], 0b11, io_group=io_group)
    return





def read(c,key,param):
    c.reads = []
    c.read_configuration(key,param,timeout=0.1)
    message = c.reads[-1]
    for msg in message:
        if not isinstance(msg,larpix.packet.packet_v2.Packet_v2):
            continue
        if msg.packet_type not in [larpix.packet.packet_v2.Packet_v2.CONFIG_READ_PACKET]:
            continue
        print(msg)

def conf_east(c,cm,ck,cadd,iog,iochan):
    HI_TX_DIFF=0
    HTX_SLICE=15
    HR_TERM=2
    HI_RX=8

# add second chip
    #set mother transceivers
    c.add_chip(ck,version='2b')
    c[cm].config.i_rx3=HI_RX
    c.write_configuration(cm, 'i_rx3')
    c[cm].config.r_term3=HR_TERM
    c.write_configuration(cm, 'r_term3')
    c[cm].config.i_tx_diff2=HI_TX_DIFF
    c.write_configuration(cm, 'i_tx_diff2')
    c[cm].config.tx_slices2=HTX_SLICE
    c.write_configuration(cm, 'tx_slices2')
    c[cm].config.enable_piso_upstream[2]=1  #[0,0,1,0]
    m_piso=c[cm].config.enable_piso_upstream
    c[cm].config.enable_piso_upstream=[0,0,1,0] # turn only one upstream port on during config
    c.write_configuration(cm, 'enable_piso_upstream')
    #add new chip to network
    default_key = larpix.key.Key(iog, iochan, 1) # '1-5-1'
    c.add_chip(default_key,version='2b') # TODO, create v2c class
    #  - - rename to chip_id = 12
    c[default_key].config.chip_id = cadd
    c.write_configuration(default_key,'chip_id')
    #  - - remove default chip id from the controller
    c.remove_chip(default_key)
    #  - - and add the new chip id
    print(ck)
    c[ck].config.chip_id=cadd
    c[ck].config.i_rx1=HI_RX
    c.write_configuration(ck, 'i_rx1')
    c[ck].config.r_term1=HR_TERM
    c.write_configuration(ck, 'r_term1')
    c[ck].config.enable_posi=[0,1,0,0]
    c.write_configuration(ck, 'enable_posi')
    c[ck].config.enable_piso_upstream=[0,0,0,0]
    c.write_configuration(ck, 'enable_piso_upstream')
    c[ck].config.i_tx_diff0=HI_TX_DIFF
    c.write_configuration(ck, 'i_tx_diff0')
    c[ck].config.tx_slices0=HTX_SLICE
    c.write_configuration(ck, 'tx_slices0')
    c[ck].config.enable_piso_downstream=[1,1,1,1] # krw adding May 8, 2023
    c.write_configuration(ck, 'enable_piso_downstream')
    time.sleep(0.1)
    c[ck].config.enable_piso_downstream=[1,0,0,0] # only one downstream port
    c.write_configuration(ck, 'enable_piso_downstream')
    time.sleep(0.1)
    #enable mother rx
    c[cm].config.enable_piso_upstream=m_piso
    c.write_configuration(cm, 'enable_piso_upstream') #allow multi-upstream
    c[cm].config.enable_posi[3]= 1  #[0,1,0,1]
    c.write_configuration(cm, 'enable_posi')

def conf_north(c,cm,ck,cadd,iog,iochan):
    HI_TX_DIFF=0
    HTX_SLICE=15
    HR_TERM=2
    HI_RX=8

# add second chip
    #set mother transceivers
    c.add_chip(ck,version='2b')
    c[cm].config.i_rx0=HI_RX
    c.write_configuration(cm, 'i_rx0')
    c[cm].config.r_term0=HR_TERM
    c.write_configuration(cm, 'r_term0')
    c[cm].config.i_tx_diff3=HI_TX_DIFF
    c.write_configuration(cm, 'i_tx_diff3')
    c[cm].config.tx_slices3=HTX_SLICE
    c.write_configuration(cm, 'tx_slices3')
    c[cm].config.enable_piso_upstream[3]= 1 # add new upstream port  
    m_piso=c[cm].config.enable_piso_upstream # remember upstream ports
    c[cm].config.enable_piso_upstream = [0,0,0,1] # turn only one upstream port on during config
    c.write_configuration(cm, 'enable_piso_upstream')

    #add new chip to network
    default_key = larpix.key.Key(iog, iochan, 1) # '1-5-1'
    c.add_chip(default_key,version='2b') # TODO, create v2c class
    c[default_key].config.chip_id = cadd
    c.write_configuration(default_key,'chip_id')
    c.remove_chip(default_key)
    print("adding " ,ck)
    c[ck].config.chip_id=cadd
    c[ck].config.i_rx2=HI_RX
    c.write_configuration(ck, 'i_rx2')
    c[ck].config.r_term2=HR_TERM
    c.write_configuration(ck, 'r_term2')
    c[ck].config.enable_posi=[0,0,1,0]
    c.write_configuration(ck, 'enable_posi')
    c[ck].config.enable_piso_upstream=[0,0,0,0]
    c.write_configuration(ck, 'enable_piso_upstream')
    c[ck].config.i_tx_diff1=HI_TX_DIFF
    c.write_configuration(ck, 'i_tx_diff1')
    c[ck].config.tx_slices1=HTX_SLICE
    c.write_configuration(ck, 'tx_slices1')
    c[ck].config.enable_piso_downstream=[1,1,1,1] # krw adding May 8, 2023
    c.write_configuration(ck, 'enable_piso_downstream')
    time.sleep(0.1)
    c[ck].config.enable_piso_downstream=[0,1,0,0] 
    c.write_configuration(ck, 'enable_piso_downstream')
    time.sleep(0.1)
    #enable mother rx
    c[cm].config.enable_piso_upstream=m_piso
    c.write_configuration(cm, 'enable_piso_upstream') #allow multi-upstream
    c[cm].config.enable_posi[0]= 1  #[0,1,0,1]
    c.write_configuration(cm, 'enable_posi')

        
def conf_south(c,cm,ck,cadd,iog,iochan):
    HI_TX_DIFF=0
    HTX_SLICE=15
    HR_TERM=2
    HI_RX=8

# add second chip
    #set mother transceivers rx2, tx1
    c.add_chip(ck,version='2b')
    c[cm].config.i_rx2=HI_RX
    c.write_configuration(cm, 'i_rx2')
    c[cm].config.r_term2=HR_TERM
    c.write_configuration(cm, 'r_term2')
    c[cm].config.i_tx_diff1=HI_TX_DIFF
    c.write_configuration(cm, 'i_tx_diff1')
    c[cm].config.tx_slices1=HTX_SLICE
    c.write_configuration(cm, 'tx_slices1')
    c[cm].config.enable_piso_upstream[1]= 1  
    m_piso=c[cm].config.enable_piso_upstream
    c[cm].config.enable_piso_upstream=[0,1,0,0] # turn only one upstream port on during config
    c.write_configuration(cm, 'enable_piso_upstream')

    #add new chip to network
    default_key = larpix.key.Key(iog, iochan, 1) # '1-5-1'
    c.add_chip(default_key,version='2b') # TODO, create v2c class
    #  - - rename to chip_id = 12
    c[default_key].config.chip_id = cadd
    c.write_configuration(default_key,'chip_id')
    #  - - remove default chip id from the controller
    c.remove_chip(default_key)
    #  - - and add the new chip id
    print(ck)
    c[ck].config.chip_id=cadd
    c[ck].config.i_rx0=HI_RX  #rx0,tx3
    c.write_configuration(ck, 'i_rx0')
    c[ck].config.r_term0=HR_TERM
    c.write_configuration(ck, 'r_term0')
    c[ck].config.enable_posi=[1,0,0,0]
    c.write_configuration(ck, 'enable_posi')
    c[ck].config.enable_piso_upstream=[0,0,0,0]
    c.write_configuration(ck, 'enable_piso_upstream')
    c[ck].config.i_tx_diff3=HI_TX_DIFF
    c.write_configuration(ck, 'i_tx_diff3')
    c[ck].config.tx_slices3=HTX_SLICE
    c.write_configuration(ck, 'tx_slices3')
    c[ck].config.enable_piso_downstream=[1,1,1,1] # krw adding May 8, 2023
    c.write_configuration(ck, 'enable_piso_downstream')
    time.sleep(0.1)    
    c[ck].config.enable_piso_downstream=[0,0,0,1] 
    c.write_configuration(ck, 'enable_piso_downstream')
    time.sleep(0.1)    
    #enable mother rx
    c[cm].config.enable_piso_upstream=m_piso
    c.write_configuration(cm, 'enable_piso_upstream') #allow multi-upstream
    c[cm].config.enable_posi[2]=1  #[0,1,0,1]
    c.write_configuration(cm, 'enable_posi')
    
        
def conf_root(c,cm,cadd,iog,iochan):
    I_TX_DIFF=0
    TX_SLICE=15
    R_TERM=2
    I_RX=8
    c.add_chip(cm,version='2b')
    #  - - default larpix chip_id is '1'
    default_key = larpix.key.Key(iog, iochan, 1) # '1-5-1'
    c.add_chip(default_key,version='2b') # TODO, create v2c class
    #  - - rename to chip_id = cm
    c[default_key].config.chip_id = cadd
    c.write_configuration(default_key,'chip_id')
    #  - - remove default chip id from the controller
    c.remove_chip(default_key)
    #  - - and add the new chip id
    print(cm)
    c[cm].config.chip_id=cadd
    c[cm].config.i_rx1=I_RX
    c.write_configuration(cm, 'i_rx1')
    c[cm].config.r_term1=R_TERM
    c.write_configuration(cm, 'r_term1')
    c[cm].config.enable_posi=[0,1,0,0]
    c.write_configuration(cm, 'enable_posi')
    c[cm].config.enable_piso_upstream=[0,0,0,0]
    c.write_configuration(cm, 'enable_piso_upstream')
    c[cm].config.i_tx_diff0=I_TX_DIFF
    c.write_configuration(cm, 'i_tx_diff0')
    c[cm].config.tx_slices0=TX_SLICE
    c.write_configuration(cm, 'tx_slices0')
    #c.io.set_reg(0x18, 1, io_group=1)
    c[cm].config.enable_piso_downstream=[1,1,1,1] # krw adding May 8, 2023
    c.write_configuration(cm, 'enable_piso_downstream')
    time.sleep(0.1)
    c[cm].config.enable_piso_downstream=[1,0,0,1] # piso1 ds for probe 
    c.write_configuration(cm, 'enable_piso_downstream')
    time.sleep(0.1)
    # enable pacman uart receiver
    rx_en = c.io.get_reg(0x18, iog)
    ch_set=pow(2,iochan-1)
    print('enable pacman uart receiver', rx_en, ch_set, rx_en|ch_set)
#    c.io.set_reg(0x18, rx_en|ch_set, iog)

    
def main():

    ###########################################
    IO_GROUP = 1
    PACMAN_TILE = 2
    #IO_CHAN = (1+(PACMAN_TILE-1)*4)
    IO_CHAN = 5
    VDDA_DAC = 54000# 44500 # ~1.8 V
    VDDD_DAC =  28500 # ~1.1 V
    RESET_CYCLES = 300000 #5000000


    REF_CURRENT_TRIM=0
    ###########################################

    # create a larpix controller
    c = larpix.Controller()
    c.io = larpix.io.PACMAN_IO(relaxed=True)
    io_group=IO_GROUP
    pacman_version='v1rev4'
    pacman_tile=[PACMAN_TILE]
    chip=11    
    cadd=12
        #disable pacman rx uarts
    bitstring = list('00000000000000000000000011110000')
    c.io.set_reg(0x18, int("".join(bitstring),2), io_group)
    if True :
        print('enable pacman power')
        # disable tile power, LARPIX clock
        c.io.set_reg(0x00000010, 0, io_group)
        c.io.set_reg(0x00000014, 0, io_group)
        # set up mclk in pacman
        c.io.set_reg(0x101c, 0x4, io_group)
        time.sleep(1)
    
        # enable pacman power
        c.io.set_reg(0x00000014, 1, io_group)
        #set voltage dacs to 0V  
        c.io.set_reg(0x24010+(PACMAN_TILE-1), 0, io_group)
        c.io.set_reg(0x24020+(PACMAN_TILE-1), 0, io_group)
        time.sleep(0.1)
        #set voltage dacs  VDDD first 
        c.io.set_reg(0x24020+(PACMAN_TILE-1), VDDD_DAC, io_group)
        c.io.set_reg(0x24010+(PACMAN_TILE-1), VDDA_DAC, io_group)
  
        print('reset the larpix for n cycles',RESET_CYCLES)
        #   - set reset cycles
        c.io.set_reg(0x1014,RESET_CYCLES,io_group=IO_GROUP)
        #   - toggle reset bit
        clk_ctrl = c.io.get_reg(0x1010, io_group=IO_GROUP)
        c.io.set_reg(0x1010, clk_ctrl|4, io_group=IO_GROUP)
        c.io.set_reg(0x1010, clk_ctrl, io_group=IO_GROUP)
    
        #enable tile power
        tile_enable_val=pow(2,PACMAN_TILE-1)+0x0200  #enable one tile at a time    
        c.io.set_reg(0x00000010,tile_enable_val,io_group)
        time.sleep(0.03)
        print('enable tilereg 0x10 , ', tile_enable_val)
        readback=pacman_base.power_readback(c.io, io_group, pacman_version,pacman_tile)
    
    if True :
        #   - toggle reset bit
        RESET_CYCLES = 50000
        c.io.set_reg(0x1014,RESET_CYCLES,io_group=IO_GROUP)
        clk_ctrl = c.io.get_reg(0x1010, io_group=IO_GROUP)
        c.io.set_reg(0x1010, clk_ctrl|4, io_group=IO_GROUP)
        c.io.set_reg(0x1010, clk_ctrl, io_group=IO_GROUP)
        time.sleep(0.01)

    #c.io.set_reg(0x24010+(PACMAN_TILE-1), 44500, io_group)
    
    invert_pacman_uart(c.io, IO_GROUP, 'v2b', PACMAN_TILE)

    chip11_key=larpix.key.Key(IO_GROUP,IO_CHAN,11)
    conf_root(c,chip11_key,11,IO_GROUP,IO_CHAN)    
# add second chip
    chip12_key=larpix.key.Key(IO_GROUP,IO_CHAN,12)
#    conf_east(c,chip11_key,chip12_key,12,IO_GROUP,IO_CHAN)
# add third chip
    chip13_key=larpix.key.Key(IO_GROUP,IO_CHAN,13)
#    conf_east(c,chip12_key,chip13_key,13,IO_GROUP,IO_CHAN)
# add fourth chip
    chip14_key=larpix.key.Key(IO_GROUP,IO_CHAN,14)
#    conf_east(c,chip13_key,chip14_key,14,IO_GROUP,IO_CHAN)
# add fifth chip
    chip15_key=larpix.key.Key(IO_GROUP,IO_CHAN,15)
#    conf_east(c,chip14_key,chip15_key,15,IO_GROUP,IO_CHAN)

#add second root chain
    IO_CHAN = IO_CHAN + 1
    chip21_key=larpix.key.Key(IO_GROUP,IO_CHAN,21)
    conf_root(c,chip21_key,21,IO_GROUP,IO_CHAN) 
# add second chip
    chip22_key=larpix.key.Key(IO_GROUP,IO_CHAN,22)
#    conf_east(c,chip21_key,chip22_key,22,IO_GROUP,IO_CHAN)
# add third chip
    chip23_key=larpix.key.Key(IO_GROUP,IO_CHAN,23)
#    conf_east(c,chip22_key,chip23_key,23,IO_GROUP,IO_CHAN)
# add fourth chip
    chip24_key=larpix.key.Key(IO_GROUP,IO_CHAN,24)
#    conf_east(c,chip23_key,chip24_key,24,IO_GROUP,IO_CHAN)
# add fifth chip
    chip25_key=larpix.key.Key(IO_GROUP,IO_CHAN,25)
#    conf_east(c,chip24_key,chip25_key,25,IO_GROUP,IO_CHAN)
#add third root chain
    IO_CHAN = IO_CHAN + 1
    chip31_key=larpix.key.Key(IO_GROUP,IO_CHAN,31)
    conf_root(c,chip31_key,31,IO_GROUP,IO_CHAN) 
# add second chip
    chip32_key=larpix.key.Key(IO_GROUP,IO_CHAN,32)
#    conf_east(c,chip31_key,chip32_key,32,IO_GROUP,IO_CHAN)
# add third chip
    chip33_key=larpix.key.Key(IO_GROUP,IO_CHAN,33)
#    conf_east(c,chip32_key,chip33_key,33,IO_GROUP,IO_CHAN)
# add fourth chip
    chip34_key=larpix.key.Key(IO_GROUP,IO_CHAN,34)
#    conf_east(c,chip33_key,chip34_key,34,IO_GROUP,IO_CHAN)
# add fifth chip
    chip35_key=larpix.key.Key(IO_GROUP,IO_CHAN,35)
#    conf_east(c,chip34_key,chip35_key,35,IO_GROUP,IO_CHAN)
#add 44 south
    chip44_key=larpix.key.Key(IO_GROUP,IO_CHAN,44)
#    conf_south(c,chip34_key,chip44_key,44,IO_GROUP,IO_CHAN)
#add 54 south
    chip54_key=larpix.key.Key(IO_GROUP,IO_CHAN,54)
#    conf_south(c,chip44_key,chip54_key,54,IO_GROUP,IO_CHAN)
#add 45 south
    chip45_key=larpix.key.Key(IO_GROUP,IO_CHAN,45)
#    conf_south(c,chip35_key,chip45_key,45,IO_GROUP,IO_CHAN)
#add 55 south
    chip55_key=larpix.key.Key(IO_GROUP,IO_CHAN,55)
#    conf_south(c,chip45_key,chip55_key,55,IO_GROUP,IO_CHAN)

#add fourth root chain
    IO_CHAN = IO_CHAN + 1
    chip41_key=larpix.key.Key(IO_GROUP,IO_CHAN,41)
    conf_root(c,chip41_key,41,IO_GROUP,IO_CHAN) 
#add south row 5
    chip51_key=larpix.key.Key(IO_GROUP,IO_CHAN,51)
#    conf_south(c,chip41_key,chip51_key,51,IO_GROUP,IO_CHAN)
#add east row 5
    chip52_key=larpix.key.Key(IO_GROUP,IO_CHAN,52)
#    conf_east(c,chip51_key,chip52_key,52,IO_GROUP,IO_CHAN)
# add second chip
#    chip42_key=larpix.key.Key(IO_GROUP,IO_CHAN,42)
#    conf_(c,chip41_key,chip42_key,42,IO_GROUP,IO_CHAN)

# add second chip
    chip42_key=larpix.key.Key(IO_GROUP,IO_CHAN,42)
#    conf_north(c,chip52_key,chip42_key,42,IO_GROUP,IO_CHAN)
# add third chip
    chip43_key=larpix.key.Key(IO_GROUP,IO_CHAN,43)
#    conf_east(c,chip42_key,chip43_key,43,IO_GROUP,IO_CHAN)
# add fourth chip
#ex    chip44_key=larpix.key.Key(IO_GROUP,IO_CHAN,44)
#    conf_east(c,chip43_key,chip44_key,44,IO_GROUP,IO_CHAN)
# add fifth chip
#ex    chip45_key=larpix.key.Key(IO_GROUP,IO_CHAN,45)
#    conf_east(c,chip44_key,chip45_key,45,IO_GROUP,IO_CHAN)

#add south row 5
    chip53_key=larpix.key.Key(IO_GROUP,IO_CHAN,53)
#    conf_east(c,chip52_key,chip53_key,53,IO_GROUP,IO_CHAN)
#add east row 5
#ex    chip54_key=larpix.key.Key(IO_GROUP,IO_CHAN,54)
#    conf_east(c,chip53_key,chip54_key,54,IO_GROUP,IO_CHAN)
#add east row 5
#ex    chip55_key=larpix.key.Key(IO_GROUP,IO_CHAN,55)
#    conf_east(c,chip54_key,chip55_key,55,IO_GROUP,IO_CHAN)

    read(c,chip11_key,'enable_piso_downstream')
#    read(c,chip12_key,'enable_piso_downstream')
#    read(c,chip13_key,'enable_piso_downstream')
#    read(c,chip14_key,'enable_piso_downstream')
#    read(c,chip15_key,'enable_piso_downstream')

    read(c,chip21_key,'enable_piso_downstream')
#    read(c,chip22_key,'enable_piso_downstream')
#    read(c,chip23_key,'enable_piso_downstream')
#    read(c,chip24_key,'enable_piso_downstream')
#    read(c,chip25_key,'enable_piso_downstream')

    read(c,chip31_key,'enable_piso_downstream')
#    read(c,chip32_key,'enable_piso_downstream')
#    read(c,chip33_key,'enable_piso_downstream')
#    read(c,chip34_key,'enable_piso_downstream')
#    read(c,chip35_key,'enable_piso_downstream')

    read(c,chip41_key,'enable_piso_downstream')    
#    read(c,chip42_key,'enable_piso_downstream')
#    read(c,chip43_key,'enable_piso_downstream')    
#    read(c,chip44_key,'enable_piso_downstream')
#    read(c,chip45_key,'enable_piso_downstream')

#    read(c,chip51_key,'enable_piso_downstream')
#    read(c,chip52_key,'enable_piso_downstream')
#    read(c,chip53_key,'enable_piso_downstream')
#    read(c,chip54_key,'enable_piso_downstream')
#    read(c,chip55_key,'enable_piso_downstream')
 
    c.io.set_reg(0x18, int("".join(bitstring),2), io_group)
    
    #ok, diff = utility_base.reconcile_configuration(c, chip11_key, verbose=True,n=5,n_verify=5)
    # optinally, take a look at the
    #message = c.reads[-1]
    #for msg in message:
    #    if not isinstance(msg,larpix.packet.packet_v2.Packet_v2):
    #        continue
    #    if msg.packet_type not in [larpix.packet.packet_v2.Packet_v2.CONFIG_WRITE_PACKET]:
    #        continue
    #    print(msg)

    # every second, read the chip ID on chip11 and print to screen
    while True:
        print('loop')
        read(c,chip11_key,'chip_id')        
 #       read(c,chip15_key,'chip_id')
        read(c,chip21_key,'chip_id')
#        read(c,chip25_key,'chip_id')
        read(c,chip31_key,'chip_id')
        read(c,chip41_key,'chip_id')
        readback=pacman_base.power_readback(c.io, io_group, pacman_version,pacman_tile)
        time.sleep(1)
    return c, c.io


if __name__=='__main__':
    main()

