`timescale 1ns/1ps
module full_adder(input a, b, cin, output sum, cout);
  assign {cout,sum} = {1'b0,a} + {1'b0,b} + {1'b0,cin};
endmodule
