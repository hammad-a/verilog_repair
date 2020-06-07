// Self-checking testbench for first_counter.v
// DUT is instantiated in tb, tb will contain a clock generator, reset
// generator, enable logic generator, compare logic.


// step1: create a dummy template that declares inputs to DUT as reg,
// declare outputs of DUT as wire. Note there is no port list for test
// bench.
module first_counter_tb;
reg clk, reset, enable;
wire[3:0] counter_out;



first_counter U0(
    .clk (clk),
    .reset (reset),
    .enable (enable),
    .counter_out (counter_out)
);

// step2: add clock generator logic. Before this we need to drive all
// inputs of DUT to some known state.
initial begin // initial block only executes once 
    clk = 0;
    reset = 0;
    enable = 0;
end

always
    #5 clk = !clk;

integer f;
initial begin
    f = $fopen("output.txt");
    $display("\t\ttime,\tclk,\treset,\tenable,\tcount_out");
    $fwrite(f, "time,counter_out[3],counter_out[2],counter_out[1],counter_out[0]\n");
    $monitor("%d, \t%b, \t%b, \t%b, \t%d", $time, clk, reset, enable, counter_out);
    forever begin 
	@(posedge clk);
	$fwrite(f, "%g,%b,%b,%b,%b\n", $time, counter_out[3], counter_out[2], counter_out[1], counter_out[0]);
    end
end

event reset_trigger;
event reset_done_trigger;
event terminate_sim;


initial begin
    #5
    forever begin
        @(reset_trigger);
        @(negedge clk);
        reset = 1;
        @(negedge clk);
        reset = 0;
        -> reset_done_trigger;
    end
end

initial begin
    @(terminate_sim);
    #5
    $fclose(f);
    $finish;
end

initial begin: TEST_CASE_2
    #10 -> reset_trigger;
    
    @(reset_done_trigger);
    @(negedge clk);
    enable = 1;
    repeat (10) begin
        @(negedge clk);
    end
    enable = 0;
    #5 -> terminate_sim;
end

initial begin
    #103
    
     -> terminate_sim; // terminate simulation after 100 time units.

end

endmodule
