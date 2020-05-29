//Module Written By: Josh Smith

module pa2_fsm(
  input               clock,
  input               reset,
  input               valid,
  input         [3:0] num,
  input         [3:0] seq,
  output STATE        state,
  output STATE        n_state,
  output logic  [3:0] cnt,
  output logic  [3:0] n_cnt,
  output logic        hit
  
  );

  logic       cnt_inc, cnt_dec;

  // Control/output logic
  assign cnt_inc = (state == WATCH) && (seq==num);
  assign cnt_dec = (state == ASSERT);
  assign n_cnt   = cnt_inc ? cnt + 4'h1 :
                   cnt_dec ? cnt - 4'h1 : cnt;

  assign hit = (state == ASSERT);

  // Next-state logic
  always_comb begin 
    case(state)
      WAIT:
        if (valid) n_state = WATCH;
        else       n_state = WAIT;

      WATCH:
        if (!valid) n_state = (n_cnt==0) ? WAIT : ASSERT;
        else        n_state = WATCH;

      ASSERT:
        // check >1, because if we decrement to 0 we'll assert
        // hit one time too many
        if (cnt>4'h1) n_state = ASSERT;
        else          n_state = WAIT;
    
      default: n_state = WAIT;
    endcase
  end

  always_ff @(posedge clock) begin
    if (reset) begin
      state <= #1 WAIT;
      cnt   <= #1 4'h0;
    end else begin
      state <= #1 n_state;
      cnt   <= #1 n_cnt;
    end
  end

endmodule
