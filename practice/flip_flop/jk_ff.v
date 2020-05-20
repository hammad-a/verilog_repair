module tb_jk;
   reg j;
   reg k;
   reg clk;
 
   always #5 clk = ~clk;
 
   jk_ff    jk0 ( .j(j),
                  .k(k),
                  .clk(clk),
                  .q(q));
 
   initial begin
      j <= 0;
      k <= 0;
 
      #5 j <= 0;
         k <= 1;
      #20 j <= 1;
          k <= 0;
      #20 j <= 1;
          k <= 1;
      #20 $finish;
   end
 
   initial
      $monitor ("j=%0d k=%0d q=%0d", j, k, q);
endmodule 