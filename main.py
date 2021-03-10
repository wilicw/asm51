#!/usr/bin/python3
import re
import os

ROM = [0x00] * (2**16)
PTR = 0
label_dict = {}

SFRs = {
    "A": 0xE0,
    "B": 0xF0,
    "PSW": 0xD0,
    "IP": 0xB8,
    "P3": 0xB0,
    "IE": 0xA2,
    "P2": 0xA0,
    "SBUF": 0x99,
    "SCON": 0x98,
    "P1": 0x90,
    "TH1": 0x8D,
    "TH0": 0x8C,
    "TL1": 0x8B,
    "TL0": 0x8A,
    "TMOD": 0x89,
    "TCON": 0x88,
    "PCON": 0x87,
    "DPH": 0x83,
    "DPL": 0x82,
    "SP": 0x81,
    "P0": 0x80,
}


class syntax_match():
    def __init__(self) -> None:
        self.label = lambda x: re.match(r"^(\w*?):", x)  # MAIN:
        self.normal_word = lambda x: re.match(r"^(\w*?)$", x)  # LABEL
        self.hex = lambda x: re.match(r"^(\d*?)H", x)  # EFH
        self.dec = lambda x: re.match(r"^(\d*?)", x)  # 255
        self.imm_hex = lambda x: re.match(r"^#(\d*?)H", x)  # hashtag EEH
        self.imm_dec = lambda x: re.match(r"^#(\d*?)", x)  # hashtag 255
        self.internal_R_ram = lambda x: re.match(r"^@R(\d?)", x)  # @R0
        self.general_reg = lambda x: re.match(r"^R(\d?)", x)  # R7

    def sfr(self, x):
        for name in SFRs.keys():
            if x == name:
                return x
        return None


sym = syntax_match()


def sfr_hex(name):
    return SFRs[name]


def help():
    print("usage: asm51 [--] filename")
    exit(1)


def err(msg):
    print(f"asm51: error: {msg}")
    exit(1)


def err_line(msg, line):
    err(f"{msg} in line: {line}.")


def ins_err(ins, line):
    err_line(f"{ins} instruction error", line)


def search_label(label, bit):
    if label not in label_dict.keys():
        err(f"label: {label} not found.")
    addr = ("{:0" + str(bit) + "b}").format(label_dict[label])
    return addr


def mark_label(label):
    if label in label_dict.keys():
        err(f"label: {label} already been used.")
    label_dict[label] = PTR


def write_rom(opcodes):
    global PTR
    global ROM
    for o in opcodes:
        ROM[PTR] = o
        PTR += 1


def check_args(ins, args, num, f_line):
    if len(args) not in num:
        ins_err(ins, f_line)


def print_ROM():
    print(" ".join([hex(i) for i in ROM[:100]]))


def remove_space_comment(asm_code):
    clean_asm = []
    for f_line, ll in enumerate(asm_code.split("\n")):
        f_line += 1
        ll = ll.lstrip()
        ll = re.sub(';(.*)', "", ll)
        if len(ll) == 0:
            continue
        clean_asm.append((f_line, ll))
    return clean_asm


def create_label(asm_code):
    global PTR
    for f_line, ll in asm_code:
        # label
        label = re.match(r"^(\w*?):", ll)
        if label != None:
            label = label[1]
            mark_label(label)
            continue
        # instructions
        instruction = ll.split()
        ins, args = instruction[0], "".join(instruction[1:])
        ins = ins.upper()
        args = args.upper().replace(" ", "").replace("\t", "").split(",")
        if ins == "ORG":
            check_args(ins, args, [1], f_line)
            if (v := sym.hex(args[0])) != None:
                PTR = int(v[1], 16)
            elif (v := sym.dec(args[0])) != None:
                PTR = int(v[1])
            else:
                ins_err(ins, f_line)


def parser(asm_code):
    global PTR
    asm_code = remove_space_comment(asm_code)
    create_label(asm_code)
    PTR = 0
    for f_line, ll in asm_code:
        # instructions
        instruction = ll.split()
        ins, args = instruction[0], "".join(instruction[1:])
        ins = ins.upper()
        args = args.upper().replace(" ", "").replace("\t", "").split(",")
        print(f"I: {ins} {args}")
        if ins == "ORG":
            check_args(ins, args, [1], f_line)
            if (v := sym.hex(args[0])) != None:
                PTR = int(v[1], 16)
            elif (v := sym.dec(args[0])) != None:
                PTR = int(v[1])
            else:
                ins_err(ins, f_line)
        elif ins == "NOP":
            write_rom([0x01])
        elif ins == "AJMP":
            check_args(ins, args, [1], f_line)
            if (v := sym.normal_word(args[0])) != None:
                addr11 = search_label(v[0], 11)
                write_rom([
                    int(addr11[8:][::-1] + "00001", 2),
                    int(addr11[0:8][::-1], 2)
                ])
            else:
                ins_err(ins, f_line)
        elif ins == "LJMP":
            check_args(ins, args, [1], f_line)
            if (v := sym.normal_word(args[0])) != None:
                addr16 = search_label(v[0], 16)
                write_rom([
                    0x02,
                    int(addr16[8:16][::-1], 2),
                    int(addr16[0:8][::-1], 2)
                ])
            else:
                ins_err(ins, f_line)
        elif ins == "RR":
            if args[0] != "A":
                ins_err(ins, f_line)
            write_rom([0x03])
        elif ins == "INC":
            check_args(ins, args, [1], f_line)
            if args[0] == "A":
                write_rom([0x04])
            elif args[0] == "DPTR":
                write_rom([0xA3])
            elif (v := sym.internal_R_ram(args[0])) != None:
                write_rom([0x06 + int(v[1])])
            elif (v := sym.general_reg(args[0])) != None:
                write_rom([0x08 + int(v[1])])
            elif (v := sym.sfr(args[0])) != None:
                write_rom([0x05, sfr_hex(v)])
            elif (v := sym.hex(args[0])) != None:
                write_rom([0x05, int(v[1], 16)])
            elif (v := sym.dec(args[0])) != None:
                write_rom([0x05, int(v[1])])
            else:
                ins_err(ins, f_line)
        elif ins == "JBC":
            check_args(ins, args, [2], f_line)
        elif ins == "ACALL":
            check_args(ins, args, [1], f_line)
            if (v := sym.normal_word(args[0])) != None:
                addr11 = search_label(v[0], 11)
                write_rom([
                    int(addr11[8:][::-1] + "10001", 2),
                    int(addr11[0:8][::-1], 2)
                ])
            else:
                ins_err(ins, f_line)
        elif ins == "LCALL":
            check_args(ins, args, [1], f_line)
            if (v := sym.normal_word(args[0])) != None:
                addr16 = search_label(v[0], 16)
                write_rom([
                    0x12,
                    int(addr16[8:16][::-1], 2),
                    int(addr16[0:8][::-1], 2)
                ])
            else:
                ins_err(ins, f_line)
        elif ins == "RRC":
            if args[0] != "A":
                ins_err(ins, f_line)
            write_rom([0x13])
        elif ins == "DEC":
            check_args(ins, args, [1], f_line)
            if args[0] == "A":
                write_rom([0x14])
            elif (v := sym.internal_R_ram(args[0])) != None:
                write_rom([0x16 + int(v[1])])
            elif (v := sym.general_reg(args[0])) != None:
                write_rom([0x18 + int(v[1])])
            elif (v := sym.sfr(args[0])) != None:
                write_rom([0x15, sfr_hex(v)])
            elif (v := sym.hex(args[0])) != None:
                write_rom([0x15, int(v[1], 16)])
            elif (v := sym.dec(args[0])) != None:
                write_rom([0x15, int(v[1])])
            else:
                ins_err(ins, f_line)
        elif ins == "JB":
            check_args(ins, args, [2], f_line)
        elif ins == "RET":
            write_rom([0x22])
        elif ins == "RL":
            if args[0] != "A":
                ins_err(ins, f_line)
            write_rom([0x23])
        elif ins == "ADD":
            check_args(ins, args, [2], f_line)
            if args[0] == "A":
                pass
            else:
                ins_err(ins, f_line)
            if (v := sym.internal_R_ram(args[1])) != None:
                write_rom([0x26 + int(v[1])])
            elif (v := sym.general_reg(args[1])) != None:
                write_rom([0x28 + int(v[1])])
            elif (v := sym.sfr(args[0])) != None:
                write_rom([0x25, sfr_hex(v)])
            elif (v := sym.hex(args[1])) != None:
                write_rom([0x25, int(v[1], 16)])
            elif (v := sym.dec(args[1])) != None:
                write_rom([0x25, int(v[1])])
            elif (v := sym.imm_hex(args[1])) != None:
                write_rom([0x24, int(v[1], 16)])
            elif (v := sym.imm_dec(args[1])) != None:
                write_rom([0x24, int(v[1])])
            else:
                ins_err(ins, f_line)
        elif ins == "JNB":
            check_args(ins, args, [2], f_line)
        elif ins == "RET":
            write_rom([0x32])
        elif ins == "RLC":
            if args[0] != "A":
                ins_err(ins, f_line)
            write_rom([0x33])
            check_args(ins, args, [2], f_line)
        elif ins == "ADDC":
            if args[0] == "A":
                pass
            else:
                ins_err(ins, f_line)
            if (v := sym.internal_R_ram(args[1])) != None:
                write_rom([0x36 + int(v[1])])
            elif (v := sym.general_reg(args[1])) != None:
                write_rom([0x38 + int(v[1])])
            elif (v := sym.sfr(args[0])) != None:
                write_rom([0x35, sfr_hex(v)])
            elif (v := sym.hex(args[1])) != None:
                write_rom([0x35, int(v[1], 16)])
            elif (v := sym.dec(args[1])) != None:
                write_rom([0x35, int(v[1])])
            elif (v := sym.imm_hex(args[1])) != None:
                write_rom([0x34, int(v[1], 16)])
            elif (v := sym.imm_dec(args[1])) != None:
                write_rom([0x34, int(v[1])])
            else:
                ins_err(ins, f_line)
        elif ins == "JC":
            check_args(ins, args, [1], f_line)
        else:
            pass
            # err_line(f"unknown instruction \"{ins}\"", f_line)
    print_ROM()
    exit(0)


def main():
    args = os.sys.argv
    if len(args) != 2:
        help()
    filename = args[1]
    if not os.path.isfile(filename):
        err("input file not exist.")
    with open(filename, "r") as f:
        parser(f.read())


if __name__ == '__main__':
    main()