`timescale 1ns/1ps
// Added design: synchronous active-high reset, red -> green -> yellow.
// The academic source specifies neither durations nor state order.
module traffic_light #(parameter CLOCK_HZ=50000000,
    parameter RED_SECONDS=5, GREEN_SECONDS=5, YELLOW_SECONDS=2)(
    input clk, input reset, output red, output green, output yellow
);
localparam WIDTH=(CLOCK_HZ<=1) ? 1 : $clog2(CLOCK_HZ);
localparam RED=0, GREEN=1, YELLOW=2;
reg [WIDTH-1:0] divider_count;
reg [1:0] state;
integer seconds;
assign red=(state==RED);
assign green=(state==GREEN);
assign yellow=(state==YELLOW);
always @(posedge clk) begin
    if (reset) begin divider_count<=0; seconds<=0; state<=RED; end
    else if (divider_count==CLOCK_HZ-1) begin
        divider_count<=0;
        case (state)
            RED: if (seconds==RED_SECONDS-1) begin seconds<=0; state<=GREEN; end
                 else seconds<=seconds+1;
            GREEN: if (seconds==GREEN_SECONDS-1) begin seconds<=0; state<=YELLOW; end
                   else seconds<=seconds+1;
            YELLOW: if (seconds==YELLOW_SECONDS-1) begin seconds<=0; state<=RED; end
                    else seconds<=seconds+1;
            default: begin state<=RED; seconds<=0; end
        endcase
    end else divider_count<=divider_count+1'b1;
end
endmodule
