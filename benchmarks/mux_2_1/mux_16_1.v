/**********************************************************************
* Date: Aug. 
16
, 
2006
* File: Mux_16_to_1.v (440 Examples)
*
* Structural of a 16 to 1 MUX (Sixteen 1-bit inputs) that is built
* using two 8-to-1 muxes that feed a 2-to-1 mux.
*
* Note the use of a continuous assignment statement for implementing
* the combinational logic, avoiding the necessity of a "register"
* data type for output Y.
**********************************************************************/
//*********************************************************
module mux_16to1(Y, In, sel);
//*********************************************************
  output       Y;
  input [15:0] In;
  input [3:0]  sel;
  wire         lo8, hi8, out1;
  // Instantiate the 8-to-1 muxes and the 2-to-1 mux
     mux_8to1 mux_lo (lo8, In[7:0], sel[2:0]);
     mux_8to1 mux_hi (hi8, In[15:8], sel[2:0]);
     mux_2to1 mux_out (out1, lo8, hi8, sel[3]);
  // equate the wire out of the 2-to-1 with 
  // the actual output (Y) of the 16-to-1 mux
     assign Y = out1;
endmodule
