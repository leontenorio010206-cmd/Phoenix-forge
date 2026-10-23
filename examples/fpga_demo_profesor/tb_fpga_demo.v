module tb_fpga_demo;
  reg clk = 0;
  reg reset = 1;
  wire [3:0] leds;
  integer i;
  fpga_demo dut(.clk(clk), .reset(reset), .leds(leds));
  initial begin
    $dumpfile("fpga_demo.vcd");
    $dumpvars(0, tb_fpga_demo);
    #5; clk = 1; #1;
    if (leds !== 4'b0000) $fatal(1, "Reset incorrecto");
    #4; clk = 0; reset = 0;
    for (i = 1; i <= 12; i = i + 1) begin
      #5; clk = 1; #1;
      if (leds !== (i & 15)) $fatal(1, "Contador incorrecto en %0d", i);
      #4; clk = 0;
    end
    $display("PASS: 12 FPGA RTL vectors");
    $finish;
  end
endmodule
