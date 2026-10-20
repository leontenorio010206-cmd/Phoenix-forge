`timescale 1ns/1ps
// 50 MHz / (2 * 25,000,000) = 1 Hz, 50% duty cycle.
module square_divider #(parameter HALF_CYCLES=25000000)(
    input clk, input reset, output reg square
);
localparam WIDTH = (HALF_CYCLES <= 1) ? 1 : $clog2(HALF_CYCLES);
reg [WIDTH-1:0] count;
always @(posedge clk) begin
    if (reset) begin count <= 0; square <= 0; end
    else if (count == HALF_CYCLES-1) begin count <= 0; square <= ~square; end
    else count <= count+1'b1;
end
endmodule
