`timescale 1ns/1ps
module tb_clock;
reg clk=0, reset=1;
wire red,green,yellow,pulse,square;
wire [2:0] count;
integer i, sec, slot;
// Reduced source clock: four edges represent one virtual second.
traffic_light #(.CLOCK_HZ(4),.RED_SECONDS(3),.GREEN_SECONDS(2),.YELLOW_SECONDS(1)) dut(clk,reset,red,green,yellow);
pulse_generator #(.CYCLES(4)) pg(clk,reset,pulse);
square_divider #(.HALF_CYCLES(2)) sq(clk,reset,square);
modulo_counter #(.MODULUS(5)) counter(clk,reset,1'b1,count);
always #5 clk=~clk;
initial begin
    $dumpfile("clock.vcd"); $dumpvars(0,tb_clock);
    @(negedge clk); reset=0;
    for(i=1;i<=72;i=i+1) begin
        @(posedge clk); #1;
        sec=i/4; slot=sec%6;
        if(red !== (slot<3)) $fatal(1,"Red cycle %0d",i);
        if(green !== (slot>=3 && slot<5)) $fatal(1,"Green cycle %0d",i);
        if(yellow !== (slot==5)) $fatal(1,"Yellow cycle %0d",i);
        if(pulse !== (i%4==0)) $fatal(1,"Pulse cycle %0d",i);
        if(square !== ((i/2)%2==1)) $fatal(1,"Square cycle %0d",i);
        if(count !== (i%5)) $fatal(1,"Counter cycle %0d",i);
    end
    $display("PASS: 72 cycles, traffic/pulse/square/counter"); $finish;
end
endmodule
