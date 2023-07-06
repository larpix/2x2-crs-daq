##
##
## Specify detector and run dependent constants here
##
##

## Parameters for automatic file transfer to data drive 
## SHOULD END with /
current_dir_='/home/stephen/larpix/develop_2x2/2x2-crs-daq/'
destination_dir_='/home/stephen/larpix/develop_2x2/2x2-crs-daq/'
##

## Mappings of io_group-->pacman version and io_group/tile-->ASIC version
io_group_pacman_tile_={1:[2]}
pacman_version_='v1rev4'
asic_version_='2b'
io_group_asic_version_={1:'2b'}
iog_pacman_version_={1: 'v1rev4'}
##

## Chips to exclude by io_group, tile from new networks being created.
## For example, {1: {}, 2:{ 1 : [11, 12], 4: [55] }} excludes on io_group 2 chips 11,12 on tile 1, and chip 55 on tile 4 
iog_exclude={1:{} }
##

asic_config_dir='asic_configs'




