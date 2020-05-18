module tb;
 
  // 1. Declare input/output variables to drive to the design
  reg   tb_clk;
  reg   tb_d;
  reg   tb_rstn;
  wire   tb_q;
 
  // 2. Create an instance of the design
  // This is called design instantiation
  dff   dff0 (   .clk   (tb_clk),     // Connect clock input with TB signal
          .d     (tb_d),     // Connect data input with TB signal
          .rstn   (tb_rstn),     // Connect reset input with TB signal
          .q     (tb_q));     // Connect output q with TB signal
 
  // 3. The following is an example of a stimulus
  // Here we drive the signals tb_* with certain values
  // Since these tb_* signals are connected to the design inputs,
  // the design will be driven with the values in tb_*
  initial begin
    tb_rsnt   <=   1'b0;
    tb_clk     <=   1'b0;
    tb_d     <=  1'b0;
  end
endmodule