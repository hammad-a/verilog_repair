#!/bin/bash

source /etc/profile.d/modules.sh
module load vcs/2017.12-SP2-1

rm tests.log
rm output.txt

for i in `cat testcases.txt`; do
    # echo $i
    # echo ${i##*/}
    timeout 10 vcs +vc -Mupdate -line -full64 tb.v eth_registers.v a23_core.v system.v eth_test.v tb_uart.v dumpvcd.v a23_fetch.v a23_decode.v a23_execute.v a23_coprocessor.v clocks_resets.v eth_top.v generic_iobuf.v boot_mem32.v uart.v test_module.v timer_module.v interrupt_controller.v main_mem.v wishbone_arbiter.v ethmac_wb.v eth_crc.v a23_cache.v a23_wishbone.v a23_decompile.v a23_barrel_shift.v a23_alu.v a23_multiply.v a23_register_bank.v eth_miim.v eth_maccontrol.v eth_txethmac.v eth_rxethmac.v eth_wishbone.v eth_macstatus.v generic_sram_byte_en.v generic_sram_line_en.v eth_spram_256x32.v eth_clockgen.v eth_shiftreg.v eth_outputcontrol.v eth_register.v eth_receivecontrol.v eth_transmitcontrol.v eth_txcounters.v eth_txstatem.v eth_random.v eth_rxstatem.v eth_rxcounters.v eth_rxaddrcheck.v eth_fifo.v +define+BOOT_MEM_FILE=\"$i\" \+ +define+AMBER_TEST_NAME=\"${i##*/}\" \+ -o simv -R
    if [ $? -eq 124 ]; then 
        echo "Fail" >> output.txt
    fi

done


