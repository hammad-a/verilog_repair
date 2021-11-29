# verilog_repair
Automated Repair of Verilog Hardware Descriptions

Dependencies:

PyVerilog 1.2.1
    pip3 install pyverilog==1.2.1
    -> replace source files for PyVerilog to support CirFix (see documentaiton in /pyverilog_changes)

Troubleshooting:

1.  If you get a file not found exception immediately after the first simulation:
        FileNotFoundError: [Errno 2] No such file or directory: 'output_lshift_reg_tb_t1.txt'
    This often means that the command to run the simulation timed out (due to long compilation times). This is often easily resolved by re-running
    the repair.py script. 

2.  If the machine seems super slow and unresponsive, run the top command to see if there are any zombie "simv" processes. This may happen due to a
    bug in VCS. If you see several zombie simv processes (that often use 100% CPU on one thread), please run the following command:
        nohup bash ~/clean_simv.sh& 