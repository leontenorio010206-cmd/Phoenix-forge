`timescale 1ns/1ps
module modulo_counter #(parameter MODULUS=5208,
    parameter WIDTH=(MODULUS <= 1 ? 1 : $clog2(MODULUS)))(
    input clk, input reset, input enable, output reg [WIDTH-1:0] count
);
always @(posedge clk) begin
    if (reset) count <= 0;
    else if (enable) begin
        if (count == MODULUS-1) count <= 0;
        else count <= count+1'b1;
    end
end
endmodule
