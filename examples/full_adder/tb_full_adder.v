`timescale 1ns/1ps
module tb_full_adder;
reg a,b,cin;
wire sum,cout;
integer i;
full_adder dut(a,b,cin,sum,cout);
initial begin
  $dumpfile("full_adder.vcd"); $dumpvars(0,tb_full_adder);
  for (i=0;i<8;i=i+1) begin
    {a,b,cin}=i; #10;
    if ({cout,sum} !== ({1'b0,a}+{1'b0,b}+{1'b0,cin})) $fatal(1,"Adder mismatch");
  end
  $display("PASS: 8 full-adder vectors"); $finish;
end
endmodule
