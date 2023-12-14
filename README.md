# CirFix: Automatically Repairing Defects in Hardware Design Code

This repository contains the artifact for the paper [CirFix: Automatically Repairing Defects in Hardware Design Code](https://dl.acm.org/doi/10.1145/3503222.3507763) accepted at ASPLOS'22.

Please read the individual README files in /prototype and /pyverilog_changes for instructions on how to set up and run CirFix.

Please contact Hammad Ahmad (hammada@umich.edu) if you have any questions or problems running CirFix.

## Dependencies:

* PyVerilog 1.2.1
    * `pip3 install pyverilog==1.2.1`
    * Make sure to replace source files for PyVerilog to support CirFix (see documentation in /pyverilog_changes).

* [Icarus Verilog](https://github.com/steveicarus/iverilog)
    * `sudo yum install iverilog` (for RHEL), or [build from source](https://github.com/steveicarus/iverilog?tab=readme-ov-file#buildinginstalling-icarus-verilog-from-source)

* Synopsys VCS
    * Commercial license; you may use alternative Verilog simulators, but would likely need to modify the scripts to match the API of the simulator.
