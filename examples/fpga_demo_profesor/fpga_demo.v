module fpga_demo(input clk, input reset, output reg [3:0] leds);
  always @(posedge clk) begin
    if (reset) leds <= 4'b0000;
    else leds <= leds + 4'b0001;
  end
endmodule
