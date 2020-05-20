//-------------------------------------------------
// File: count16.v
// Purpose: Verilog Simulation Example
//-------------------------------------------------
‘timescale 1 ns / 100 ps
module count16 (count, count_tri, clk, rst_l, load_l, enable_l, cnt_in,
oe_l);
 output [3:0] count;
 output [3:0] count_tri;
 input clk;
 input rst_l;
 input load_l;
 input enable_l;
 input [3:0] cnt_in;
 input oe_l;
 reg [3:0] count;
 // tri-state buffers
 assign count_tri = (!oe_l) ? count : 4’bZZZZ;
 // synchronous 4 bit counter
 always @ (posedge clk or negedge rst_l)
 begin
 if (!rst_l) begin
 count <= #1 4’b0000;
end
 else if (!load_l) begin
 count <= #1 cnt_in;
end
 else if (!enable_l) begin
 count <= #1 count + 1;
 end
 end
endmodule //of count16
