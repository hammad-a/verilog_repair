# CirFix: Automatically Repairing Defects in Hardware Design Code

Please read the individual readme files in /prototype and /pyverilog_changes for instructions on how to set up and run CirFix.

Please contact Hammad Ahmad (hammada@umich.edu) if you have any questions or problems running CirFix.

# Dependencies:

PyVerilog 1.2.1
    pip3 install pyverilog==1.2.1
    -> replace source files for PyVerilog to support CirFix (see documentaiton in /pyverilog_changes)

Icarus Verilog
    sudo yum install iverilog (for RHEL)

Synopsys VCS
    (commercial license; you may use alternative Verilog simulators, but would likely need to modify the scripts to match the API of the simulator)
