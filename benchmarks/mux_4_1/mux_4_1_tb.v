module tb_4to1_mux;

   reg [3:0] a;
   reg [3:0] b;
   reg [3:0] c;
   reg [3:0] d;
   wire [3:0] out;
   reg [1:0] sel;

   reg clk;

   integer i;
   
   always #1 clk = !clk;

   mux_4to1_case  mux0 (   .a (a),
                           .b (b),
                           .c (c),
                           .d (d),
                           .sel (sel),
                           .out (out));


   integer f;

   initial begin
       f = $fopen("output_mux_4_1_tb.txt");
       $fwrite(f, "time,out[3],out[2],out[1],out[0]\n");
       forever begin
           @(posedge clk);
           $fwrite(f, "%g,%b,%b,%b,%b\n", $time,out[3],out[2],out[1],out[0]);
       end
   end
   initial begin
      $monitor ("[%0t] sel=0x%0h a=0x%0h b=0x%0h c=0x%0h d=0x%0h out=0x%0h", $time, sel, a, b, c, d, out);

   	  clk = 0;
      sel <= 0;
      a <= $random;
      b <= $random;
      c <= $random;
      d <= $random;

      for (i = 1; i < 4; i=i+1) begin
         #5 sel <= i;
      end

      #6 $finish;
      #10 $fclose(f);
   end
endmodule