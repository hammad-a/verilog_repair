always @ (posedge clk)
  if (~rst_n)
    begin
    state <= INIT_NOP1;
    command <= CMD_NOP;
    state_cnt <= 4'hf;
    haddr_r <= {HADDR_WIDTH{1'b0}};
    state_cnt_next <= 4'd0;
    rd_data_r <= IDLE;
    busy <= 1'b0;
    end
  else
 
