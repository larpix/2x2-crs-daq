##
##
## Specify detector and run dependent constants here
##
##

## Parameters for automatic file transfer to data drive
_current_dir_='/home/daq/PACMANv1rev3b/run3/2x2-crs-daq/'
_destination_dir_='/data/LArPix/Module3_Feb2023/run3/commission'
##

## Mappings of io_group-->pacman version and io_group/tile-->ASIC version
_io_group_pacman_tile_={1:list(range(1,9,1)), 2:list(range(1,9,1))}
__pacman_version_='v1rev3b'
_asic_version_='2'
_io_group_asic_version_={1:2, 2:2}
_iog_pacman_version_={1: 'v1rev3b', 2 : 'v1rev3b'}
##

## Chips to exclude by io_group, tile from new networks being created.
## For example, {1: {}, 2:{ 1 : [11, 12], 4: [55] }} excludes on io_group 2 chips 11,12 on tile 1, and chip 55 on tile 4 
_iog_exclude={1:{}, 2:{} }
##






