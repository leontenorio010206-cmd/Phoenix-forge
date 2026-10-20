`timescale 1ns/1ps
// One source-clock-wide pulse every CYCLES rising edges. Not a square clock.
module pulse_generator #(parameter CYCLES=50000000)(
    input clk, input reset, output reg pulse
);
localparam WIDTH = (CYCLES <= 1) ? 1 : $clog2(CYCLES);
reg [WIDTH-1:0] count;
always @(posedge clk) begin
    if (reset) begin count <= 0; pulse <= 0; end
    else if (count == CYCLES-1) begin count <= 0; pulse <= 1; end
    else begin count <= count+1'b1; pulse <= 0; end
end
endmodule
