# CirFix: Automatically Repairing Defects in Hardware Design Code

This repository contains the artifact for the paper CirFix: Automatically Repairing Defects in Hardware Design Code accepted at ASPLOS'22.

Please read the individual readme files in /prototype and /pyverilog_changes for instructions on how to set up and run CirFix.

Please contact Hammad Ahmad (hammada@umich.edu) if you have any questions or problems running CirFix.

# Dependencies:

PyVerilog 1.2.1 <br/>
&nbsp;&nbsp;&nbsp;&nbsp;pip3 install pyverilog==1.2.1 <br/>
&nbsp;&nbsp;&nbsp;&nbsp;Make sure to replace source files for PyVerilog to support CirFix (see documentaiton in /pyverilog_changes).

Icarus Verilog <br/>
&nbsp;&nbsp;&nbsp;&nbsp;sudo yum install iverilog (for RHEL)

Synopsys VCS <br/>
&nbsp;&nbsp;&nbsp;&nbsp;(Commercial license; you may use alternative Verilog simulators, but would likely need to modify the scripts to match the API of the simulator.)

# Note:

If you do not have a Synopsys VCS license, check out the iverilog branch that removes that dependency and provides minor usability improvements. Note that I have had a chance to only partially replicate the ASPLOS'22 results using just iverilog. If you happen to be able to fully verify those results, let me know and I can update this. :) 
