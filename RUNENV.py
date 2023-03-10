##
##
## Specify detector and run dependent constants here
##
##

## Parameters for automatic file transfer to data drive 
## SHOULD END with /
current_dir_='/home/stephen/larpix/testing/run3_testing/develop/2x2-crs-daq/'
destination_dir_='/home/stephen/larpix/testing/run3_testing/data'
##

## Mappings of io_group-->pacman version and io_group/tile-->ASIC version
io_group_pacman_tile_={1:list(range(1,9,1)), 2:list(range(1,9,1))}
pacman_version_='v1rev3b'
asic_version_='2'
io_group_asic_version_={1:2, 2:2}
iog_pacman_version_={1: 'v1rev3b', 2 : 'v1rev3b'}
##

## Chips to exclude by io_group, tile from new networks being created.
## For example, {1: {}, 2:{ 1 : [11, 12], 4: [55] }} excludes on io_group 2 chips 11,12 on tile 1, and chip 55 on tile 4 
iog_exclude={1:{}, 2:{} }
##






