//-----------------------------------------
//Design name: first_counter
//File Name: first_counter.v
//Function: This is a 4-bit up-counter with
//Synchronous active high reset and 
//with active high enable signal
//------------------------------------------
module first_counter(
    clk,
    reset,
    enable,
    counter_out
);// End of port list
//----------------Input Ports---------------
input clk;
input reset;
input enable;
//----------------Output Ports--------------
output[3:0] counter_out;
//----------------Input ports Data Type-----
//By rule all the input ports should be wires
wire clk;
wire reset;
wire enable;
//----------------Output ports data type----
//Output port can be a storage element(reg) or a wire
reg[3:0] counter_out;

//---------------Code starts here-----------
always@(posedge clk)
begin: COUNTER //block name
    //At every rising edge of clock we check if reset is active
    //If active, we load the counter output with 4'b0000
    if(clk==1'b1) begin
        counter_out <= #1 4'b0000;
    end
    //If enable is active, we increment the counter
    else if(enable == 1'b1) begin
        counter_out <= #1 counter_out + 1;
    end
end // End of block COUNTER

endmodule // End of module counter

