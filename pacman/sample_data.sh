./data_transmit_off.sh
./power_vdda.sh
sleep 5
./data_transmit_on.sh
sleep $1
./data_transmit_off.sh
./power_down_vdda.sh
