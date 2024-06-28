# MIT License

# Copyright (c) 2024 B. Arar

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
from string import Template
import os

# default paramters, feel free to change

input_modifier = "_i"
output_modifier = "_o"
inout_modifier = "_io"

modifiers_enabled = True

m_i_skew = "1step"
m_o_skew = "1ns"
s_i_skew = "1step"
s_o_skew = "1ns"

sync_m = "master_sp"      # Name of synchronous master modport
clk_m = "mcb"       # Name of master clocking block:
sync_s = "slave_sp"      # Name of synchronous slave modport
clk_s = "scb"       # Name of master clocking block
async_m = "master"  # Name of asynchronous master modport
async_s = "slave"   # Name of asynchronous slave modport


# Template class to group generator templates without placing in a separate file
class templates:
    port_expression = Template(".${identifier}(${expression})")

    # Main block: Interface
    interface_template = Template(
"""\
interface $interface_name ($port_list);
$interface_items\
$interface_clocking_blocks\
${interface_modports}\
endinterface : $interface_name
"""
    )

    # Clocking block templates:
    clocking_block = Template(
"""
\tclocking $clocking_identifier @(posedge ${clk_name});
\t\tdefault input #${input_skew} output #${output_skew};
${items}\
\tendclocking : $clocking_identifier\n
"""
    )

    # Port templates

    input_direct = Template("input\t${dtype}\t${size}\t${identifier}${modifier}")
    output_direct = Template("output\t${dtype}\t${size}\t${identifier}${modifier}")
    inout_direct = Template("inout\t\t${size}\t${identifier}${modifier}")

    input_expression = Template("input\t.${expression}${modifier}(${identifier})")
    output_expression = Template("output\t.${expression}${modifier}(${identifier})")
    inout_expression = Template("inout\t.${expression}${modifier}(${identifier})")

    item = Template("$dtype\t$size\t$identifier;")

    # Modport templates:

    """
    modport_identifier: name of modport
    list_of_ports: comma-separated list of the port expressions that make up the modport
    """
    modport = Template("\tmodport $modport_identifier ($list_of_ports);\n")


# Port class, encompasses data and common functions for a given interface item
class Port:
    direction = ""
    dtype = ""
    size = ""
    identifier = ""
    expression = None
    main_port = False # determines whether port will be a port for the whole interface
    def __init__(self, direction, dtype, size, identifier, expression=None, main_port=False):
        self.direction = direction
        self.dtype = dtype
        self.size = "\t" if size == "" else size
        self.identifier = identifier
        self.expression = expression
        self.main_port = main_port
    
    def copy(self, **kwargs):
        cpy = Port(self.direction, self.dtype, self.size, self.identifier, self.expression, self.main_port)
        if "direction" in kwargs:
            cpy.direction = kwargs["direction"]
            
        if "dtype" in kwargs:
            cpy.dtype = kwargs["dtype"]

        if "size" in kwargs:
            cpy.size = kwargs["size"]

        if "identifier" in kwargs:
            cpy.identifier = kwargs["identifier"]

        if "expression" in kwargs:
            cpy.expression = kwargs["expression"]

        if "main_port" in kwargs:
            cpy.main_port = kwargs["main_port"]

        return cpy

    def inverted(self):
        if self.direction == "input":
            return self.copy(direction="output")
        elif self.direction == "output":
            return self.copy(direction="input")
        else:
            return self
    
    def generate(self, modifier_en=False):
        template = None
        modifier = ""
        match(self.direction, self.expression):
            case ("input", None):
                template = templates.input_direct
                modifier = input_modifier
            case ("input", _):
                template = templates.input_expression
                modifier = input_modifier
            case ("output", None):
                template = templates.output_direct
                modifier = output_modifier
            case ("output", _):
                template = templates.output_expression
                modifier = output_modifier
            case ("inout", None):
                template = templates.inout_direct
                modifier = inout_modifier
            case ("inout", _):
                template = templates.inout_expression
                modifier = inout_modifier
        if modifier_en == False: modifier = ""
        return template.safe_substitute(dtype=self.dtype, identifier=self.identifier, modifier=modifier, size=self.size, expression=self.expression)

    def identifier_modifier(self):
        if modifiers_enabled == False: return self.identifier
        modifier = ""
        match(self.direction):
            case "inout":
                modifier = inout_modifier
            case "input":
                modifier = input_modifier
            case "output":
                modifier = output_modifier
        return self.identifier + modifier



# 1 - Read the file given in command line
file = None

try:
    ind = sys.argv.index('-i')
    if ind == -1 or ind == (len(sys.argv) - 1):
        raise Exception("No input file specified.")
    file = open(sys.argv[ind + 1],"r")
except:
    print("Error: Failed to open file.")
    exit(1)

content = file.read()

item_strings = content.split('\n')

# 2 - Parse items from file, ignores comments, extra white spaces, and empty lines

items = []

""" Returns direction string and main_port boolean in a tuple from direction input string"""
def parse_direction(str):
    direction = ""
    match(str):
        case "i" | "i!":
            direction = "input"
        case "o" | "o!":
            direction = "output"
        case "io" | "io!":
            direction = "inout"
    if str[-1] == "!":
        main_port = True
    else:
        main_port = False
    return (direction, main_port)


"""Reads item type, size, and identifier and returns as string tuple"""
def parse_item(item = ""):
    item = item.replace("[ ", "[").replace(" ]", "]").replace(" :", ":").replace(": ", ":")
    arr = item.split()
    i = 1
    if arr[-i][-1] == ';':
        direction_mod = ""
        identifier = arr[-i][0:-1]
        i = i + 1
    else:
        direction_mod = arr[-i]
        identifier = arr[-i - 1][0:-1]
        i = i + 2
    
    if arr[-i][0] == '[':
        size = arr[-i]
        i = i + 1
    else:
        size = ""
    if direction_mod != "":
        (direction, main_port) = parse_direction(direction_mod)
    else:
        (direction, main_port) = ("",False)
    
    dtype = " ".join(arr[0:-i + 1])
    return (direction, dtype, size, identifier, main_port)



for item in item_strings:
    no_ws = "".join(item.split())
    if no_ws == "" or no_ws[0:2] == "//" : continue
    parsed = parse_item(item)
    items.append(Port(parsed[0], parsed[1], parsed[2], parsed[3], None, parsed[4]))

# 3 - Prompt user for item directions not specified in source file

print("""For each interface item without a specified direction in the source file, enter the \
direction for the master blocks:\n
    'i' \tfor input
    'o' \tfor output
    'io'\tfor inout
Add ! (e.g. 'i!') to force the same direction for both sets of ports, this will add the \
item to the interface port list..\n""")

for item in items:
    while item.direction == "":
        dir = input(item.identifier + "\t:\t")
        (item.direction, item.main_port) = parse_direction(dir)


# 4 - Prompt user for clock port (used for clocking blocks)

clock_port = None

print("\n\n================ SIGNALS =================")

for item in items:
    print(item.generate(False),)

while clock_port == None:
    name = input("Clock signal name: ")
    for item in items:
        if item.identifier == name:
            clock_port = item
            break


# 5 - Prompt user for interface name and (optionally) other parameters

if_name = input("\nInterface name: ")

if input("Use default block names? (y/_): ") not in ["Y","y"]:
    sync_m = input("Name of synchronous master modport (empty to skip): ")
    if sync_m != "": clk_m = input("Name of master clocking block: ")
    sync_s = input("Name of synchronous slave modport (empty to skip): ")
    if sync_s != "": clk_s = input("Name of master clocking block: ")
    async_m = input("Enter name of asynchronous master modport (empty to skip):\n")
    async_s = input("Enter name of asynchronous slave modport (empty to skip):\n")

if input("Use default skews? (y/_): ") not in ["Y", "y"]:
    m_i_skew = input("Master block input skew: ")
    m_o_skew = input("Master block output skew: ")
    s_i_skew = input("Slave block input skew: ")
    s_o_skew = input("Slave block output skew: ")

# 6 - Block generator functions and logic

def generate_clocking(items, identifier, clock_port, i_skew, o_skew, inverted=False):
    ports_str = ""
    for item in items:
        if item == clock_port: continue
        if item.main_port:
            ports_str += "\t\t" + item.direction + "\t" + item.identifier_modifier() + ";\n"
            continue
        if inverted:
            item = item.inverted()
        ports_str += "\t\t" + item.direction + "\t" + item.identifier + ";\n"
    return templates.clocking_block.safe_substitute(
        clocking_identifier=identifier,
        clk_name=clock_port.identifier_modifier(),
        input_skew=i_skew,
        output_skew=o_skew,
        items=ports_str
    )

def generate_if_portlist(items):
    port_str = "\n"
    for item in items:
        if item.main_port:
            port_str += "\t" + item.generate(modifiers_enabled) + ",\n"
    return port_str.removesuffix(",\n") + "\n"

def generate_if_items(items):
    item_str = ""
    for item in items:
        if not item.main_port:
            item_str += "\t" + templates.item.safe_substitute(dtype=item.dtype, size=item.size, identifier=item.identifier) + "\n"
    return item_str

def generate_async_modport(identifier, items, inverted=False):
    port_str = "\n"
    for item in items:
        if inverted and not item.main_port: item = item.inverted()
        generated = ""
        if item.main_port or not modifiers_enabled:
            generated = item.direction + "\t" + item.identifier_modifier()
        else:
            generated = item.direction + "\t" + templates.port_expression.safe_substitute(identifier=item.identifier_modifier(), expression=item.identifier)
        port_str += "\t\t" + generated + ",\n"
    port_str = port_str.removesuffix(",\n") + "\n\t" 
    return templates.modport.safe_substitute(
        modport_identifier=identifier,
        list_of_ports=port_str
    )

def generate_sync_modport(identifier, clkng_identifier):
    return templates.modport.safe_substitute(
        modport_identifier=identifier,
        list_of_ports="clocking " + clkng_identifier
    )

def generate_interface(identifier, ports, items, clkng1, clkng2, smp1, smp2, amp1, amp2):
    return templates.interface_template.safe_substitute(
        interface_name=identifier,
        port_list=ports,
        interface_items=items,
        interface_clocking_blocks=clkng1 + clkng2,
        interface_modports = smp1 + "\n" + smp2 + "\n" + amp1 + "\n" + amp2
    )


dif = generate_interface(
    if_name,
    generate_if_portlist(items),
    generate_if_items(items),
    generate_clocking(items, clk_m, clock_port, m_i_skew, m_o_skew) if sync_m else "",
    generate_clocking(items, clk_s, clock_port, s_i_skew, s_o_skew, True) if sync_s else "",
    generate_sync_modport(sync_m, clk_m) if sync_m else "",
    generate_sync_modport(sync_s, clk_s) if sync_s else "",
    generate_async_modport(async_m, items, False) if async_m else "",
    generate_async_modport(async_s, items, True) if async_s else ""
)

# 7 - Write out results, find unused file name to avoid overwrites

filename = if_name + ".sv"
num = 1

while os.path.isfile(filename):
    filename = if_name + "_" + str(num) + ".sv"
    num += 1

with open(filename, "w") as file:
    file.write(dif)
    print("Output written to " + filename)