./pacman_util.py --write 0x00024131 38500
./pacman_util.py --write 0x00024133 38500
./pacman_util.py --write 0x00024135 39500
./pacman_util.py --write 0x00024137 39500
./pacman_util.py --write 0x00024139 38500
./pacman_util.py --write 0x0002413b 39000
./pacman_util.py --write 0x0002413d 39000
./pacman_util.py --write 0x0002413f 39000
./pacman_util.py --write 0x00000014 1
./pacman_util.py --write 0x101C 4
sleep 1
./pacman_util.py --write 0x00000010 0b1000000001
sleep 1
./pacman_util.py --write 0x00000010 0b1000000011
sleep 1
./pacman_util.py --write 0x00000010 0b1000000111
sleep 1
./pacman_util.py --write 0x00000010 0b1000001111
sleep 1
./pacman_util.py --write 0x00000010 0b1000011111
sleep 1
./pacman_util.py --write 0x00000010 0b1000111111
sleep 1
./pacman_util.py --write 0x00000010 0b1001111111
sleep 1
./pacman_util.py --write 0x00000010 0b1011111111
sleep 1
./pacman_util.py --write 0x02014 0xffffffff
./pacman_util.py --write 0x00000018 0xffffffff
