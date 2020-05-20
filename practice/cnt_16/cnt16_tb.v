//-------------------------------------------------
// File: cnt16_tb.v
// Purpose: Verilog Simulation Example
// Test Bench
//-----------------------------------------------------------
‘timescale 1 ns / 100 ps
module cnt16_tb ();
 //---------------------------------------------------------
 // inputs to the DUT are reg type
 reg clk_50;
 reg rst_l, load_l, enable_l;
 reg [3:0] count_in;
 reg oe_l;
 //--------------------------------------------------------
 // outputs from the DUT are wire type
 wire [3:0] cnt_out;
 wire [3:0] count_tri;
 //---------------------------------------------------------
 // instantiate the Device Under Test (DUT)
 // using named instantiation
 count16 U1 ( .count(cnt_out),
 .count_tri(count_tri),
 .clk(clk_50),
 .rst_l(rst_l),
 .load_l(load_l),
 .cnt_in(count_in),
 .enable_l(enable_l),
 .oe_l(oe_l)
 );
 //----------------------------------------------------------
 // create a 50Mhz clock
 always
 #10 clk_50 = ~clk_50; // every ten nanoseconds invert
 //-----------------------------------------------------------
 // initial blocks are sequential and start at time 0
 initial
 begin
 $display($time, " << Starting the Simulation >>");
 clk_50 = 1’b0;
// at time 0
 rst_l = 0;
// reset is active
 enable_l = 1’b1;
// disabled
 load_l = 1’b1;
// disabled
 count_in = 4’h0;
 oe_l = 4’b0;
// enabled
 #20 rst_l = 1’b1;
// at time 20 release reset
 $display($time, " << Coming out of reset >>");
 @(negedge clk_50); // wait till the negedge of
// clk_50 then continue
 load_count(4’hA);
// call the load_count task
11 A Verilog HDL Test Bench Primer
// and pass 4’hA
 @(negedge clk_50);
 $display($time, " << Turning ON the count enable >>");
 enable_l = 1’b0;
// turn ON enable
// let the simulation run,
// the counter should roll
 wait (cnt_out == 4’b0001); // wait until the count
// equals 1 then continue
 $display($time, " << count = %d - Turning OFF the count enable >>",
cnt_out);
 enable_l = 1’b1;
 #40;
// let the simulation run for 40ns
// the counter shouldn’t count
 $display($time, " << Turning OFF the OE >>");
 oe_l = 1’b1;
// disable OE, the outputs of
// count_tri should go high Z.
 #20;
 $display($time, " << Simulation Complete >>");
 $stop;
// stop the simulation
 end
 //--------------------------------------------------------------
 // This initial block runs concurrently with the other
 // blocks in the design and starts at time 0
 initial begin
 // $monitor will print whenever a signal changes
 // in the design
 $monitor($time, " clk_50=%b, rst_l=%b, enable_l=%b, load_l=%b,
count_in=%h, cnt_out=%h, oe_l=%b, count_tri=%h", clk_50, rst_l,
enable_l, load_l, count_in, cnt_out, oe_l, count_tri);
 end
 //--------------------------------------------------------------
 // The load_count task loads the counter with the value passed
 task load_count;
 input [3:0] load_value;
 begin
@(negedge clk_50);
$display($time, " << Loading the counter with %h >>", load_value);
 load_l = 1’b0;
count_in = load_value;
@(negedge clk_50);
load_l = 1’b1;
 end
 endtask //of load_count
endmodule //of cnt16_tb