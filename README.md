# SV-interface-gen
This script, written in Python, automatically generates SystemVerilog interface files from a list of signals provided as an input file. By default, the script generates a synchronous master port (w/ clocking), a synchronous slave port (w/ clocking), an asynchronous master port and an asynchronous slave port. You can opt to change this (along with the names of the blocks) when the script prompts you on whether to use defaults. The default skews can also be changed while the script is running. Other parameters like signal name directional modifiers can be changed by editing the script directly. This was done to make the script as simple and quick to run as possible as you make adjustments to the signal list.

You may choose to provide direction indicators (i/o/io) in the input file to avoid inputting them as the script runs. Additionally, appending `!` to the direction indicators marks the signal to be added to the port list of the interface itself (as opposed to an item within it).

## Script parameters
The following parameters and default values can be changed in the body of the script. The user is not prompted for some of these every time to save time.

#### gen-if.py [27-45]:
```py
# Default paramters, feel free to change

input_modifier = "_i"   # Modifier for input signal names
output_modifier = "_o"  # Modifier for output signal names
inout_modifier = "_io"  # Modifier for inout signal names

# Determines whether modifiers will be added 
# to signal names (and thus port expressions in modports)
modifiers_enabled = True 

# Default master input/output and slave input/output skews respectively
m_i_skew = "1step"
m_o_skew = "1ns"
s_i_skew = "1step"
s_o_skew = "1ns"

sync_m = "master_sp"        # Name of synchronous master modport
clk_m = "mcb"               # Name of master clocking block:
sync_s = "slave_sp"         # Name of synchronous slave modport
clk_s = "scb"               # Name of master clocking block
async_m = "master"          # Name of asynchronous master modport
async_s = "slave"           # Name of asynchronous slave modport
```

## Example input file
In the included example, the direction indicators are provided directly in the input file.

All extra whitespaces, comments, and empty lines are ignored by default, so feel free to style the list however you would like.

#### example.txt:
```sv
// Clock and reset
logic			clk; i!
logic			resetn; i!

// Data, address, and write strobe signals
logic	[31:0]	data; o
logic	[31:0]	addr; o
logic	[ 3:0]	wstrb; o

// Handshaking signals
logic			valid; o
logic			ready; i
```
## Example usage
In this example I opted to use default block names and skews, you can change these by typing in anything other than `y` or `Y` when prompted.
```
$ python3 gen_if.py -i example.txt
For each interface item without a specified direction in the source file, enter the direction for the master blocks:

    'i' 	for input
    'o' 	for output
    'io'	for inout
Add ! (e.g. 'i!') to force the same direction for both sets of ports, this will add the item to the interface port list..



================ SIGNALS =================
input	logic			clk
input	logic			resetn
output	logic	[31:0]	data
output	logic	[31:0]	addr
output	logic	[3:0]	wstrb
output	logic			valid
input	logic			ready
Clock signal name: clk

Interface name: example
Use default block names? (y/_): y
Use default skews? (y/_): y
Output written to example.sv

```

## Example output
```sv
interface example (
	input	logic			clk_i,
	input	logic			resetn_i
);
	logic	[31:0]	data;
	logic	[31:0]	addr;
	logic	[3:0]	wstrb;
	logic			valid;
	logic			ready;

	clocking mcb @(posedge clk_i);
		default input #1step output #1ns;
		input	resetn_i;
		output	data;
		output	addr;
		output	wstrb;
		output	valid;
		input	ready;
	endclocking : mcb


	clocking scb @(posedge clk_i);
		default input #1step output #1ns;
		input	resetn_i;
		input	data;
		input	addr;
		input	wstrb;
		input	valid;
		output	ready;
	endclocking : scb

	modport master_sp (clocking mcb);

	modport slave_sp (clocking scb);

	modport master (
		input	clk_i,
		input	resetn_i,
		output	.data_o(data),
		output	.addr_o(addr),
		output	.wstrb_o(wstrb),
		output	.valid_o(valid),
		input	.ready_i(ready)
	);

	modport slave (
		input	clk_i,
		input	resetn_i,
		input	.data_i(data),
		input	.addr_i(addr),
		input	.wstrb_i(wstrb),
		input	.valid_i(valid),
		output	.ready_o(ready)
	);
endinterface : example
```
