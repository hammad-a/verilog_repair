// "dff" is the name of this module 
 
module  dff  (   input   d,       // Inputs to the design should start with "input"
            rstn,
            clk,
        output  q);     // Outputs of the design should start with "output"
 
  reg q;               // Declare a variable to store output values
 
  always @ (posedge clk) begin   // This block is executed at the positive edge of clk 0->1
    if (!rstn)          // At the posedge, if rstn is 0 then q should get 0
      q <= 0;
    else 
      q <= d;         // At the posedge, if rstn is 1 then q should get d
  end
endmodule               // End of module