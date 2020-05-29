`timescale 1ns / 100ps
/**********************************************************************
 * Date: Aug. 28, 1999
 * File: Test_Mux_16_to_1.v   (440 Examples)
 *
 * Testbench to generate some stimulus and display the results for the
 * Mux 16 to 1 module -- with sixteen 1-bit inputs
 **********************************************************************/
//*********************************************************
  module Test_mux_16to1;
//*********************************************************  
     wire         MuxOut;
     reg   [15:0]  In;
     reg   [3:0]  sel;
     // Instantiate the MUX (named DUT {device under test})
     mux_16to1  DUT(MuxOut, In, sel);
     initial  begin
        $timeformat(-9, 1, " ns", 6);
        $monitor("At t=%t sel=%b In=%b_%b MuxOut=%b",$time,sel,In[15:8],In[7:0],MuxOut);
        In  = 16'b1100_0011_1011_0100;  // time = 0
        sel = 4'b0000; 
        #10;
        sel = 4'b0001;                  // time = 10
        #10;
        sel = 4'b0010;                  // time = 20
        #10;
        sel = 4'b0011;                  // time = 30
        #10;
        In  = 16'b1100_0011_1011_1111;        
        sel = 4'b0100;                  // time = 40
        #10;
        sel = 4'b0101;                  // time = 50
        #10;
        sel = 4'b0110;                  // time = 60
        #10;
        sel = 4'b0111;                  // time = 70
        #10;
        In  = 16'b1100_0011_1111_1111;  // time = 80
        sel = 4'b1000; 
        #10;
        sel = 4'b1001;                  // time = 90
        #10;
        sel = 4'b1010;                  // time = 100
        #10;
        sel = 4'b1011;                  // time = 110
        #10;
        In  = 16'b1100_1111_1111_1111;        
        sel = 4'b1100;                  // time = 120
        #10;
        sel = 4'b1101;                  // time = 130
        #10;
        sel = 4'b1110;                  // time = 140
        #10;
        sel = 4'b1111;                  // time = 150
        #5;
        $finish;
     end
   endmodule
