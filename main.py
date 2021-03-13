#!/usr/bin/python3
import re
import os

ROM = [0xFF] * (2**16)
LOCCTR = 0
SYMTAB = {}
LABELPROCESSTABLE = []

SFRs = {
    "A": 0xE0,
    "ACC": 0xE0,
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

SFRs_bit = {
    "P0.0": 0x80,
    "P0.1": 0x81,
    "P0.2": 0x82,
    "P0.3": 0x83,
    "P0.4": 0x84,
    "P0.5": 0x85,
    "P0.6": 0x86,
    "P0.7": 0x87,
    "P1.0": 0x90,
    "P1.1": 0x91,
    "P1.2": 0x92,
    "P1.3": 0x93,
    "P1.4": 0x94,
    "P1.5": 0x95,
    "P1.6": 0x96,
    "P1.7": 0x97,
    "P2.0": 0xA0,
    "P2.1": 0xA1,
    "P2.2": 0xA2,
    "P2.3": 0xA3,
    "P2.4": 0xA4,
    "P2.5": 0xA5,
    "P2.6": 0xA6,
    "P2.7": 0xA7,
    "P3.0": 0xB0,
    "P3.1": 0xB1,
    "P3.2": 0xB2,
    "P3.3": 0xB3,
    "P3.4": 0xB4,
    "P3.5": 0xB5,
    "P3.6": 0xB6,
    "P3.7": 0xB7,
    "TCON.0": 0x88,
    "TCON.1": 0x89,
    "TCON.2": 0x8A,
    "TCON.3": 0x8B,
    "TCON.4": 0x8C,
    "TCON.5": 0x8D,
    "TCON.6": 0x8E,
    "TCON.7": 0x8F,
    "SCON.0": 0x98,
    "SCON.1": 0x99,
    "SCON.2": 0x9A,
    "SCON.3": 0x9B,
    "SCON.4": 0x9C,
    "SCON.5": 0x9D,
    "SCON.6": 0x9E,
    "SCON.7": 0x9F,
    "IE.0": 0xA8,
    "IE.1": 0xA9,
    "IE.2": 0xAA,
    "IE.3": 0xAB,
    "IE.4": 0xAC,
    "IE.7": 0xAF,
    "IP.0": 0xB8,
    "IP.1": 0xB9,
    "IP.2": 0xBA,
    "IP.3": 0xBB,
    "IP.4": 0xBC,
    "PSW.0": 0xD0,
    "PSW.1": 0xD1,
    "PSW.2": 0xD2,
    "PSW.3": 0xD3,
    "PSW.4": 0xD4,
    "PSW.5": 0xD5,
    "PSW.6": 0xD6,
    "PSW.7": 0xD7,
    "ACC.0": 0xE0,
    "ACC.1": 0xE1,
    "ACC.2": 0xE2,
    "ACC.3": 0xE3,
    "ACC.4": 0xE4,
    "ACC.5": 0xE5,
    "ACC.6": 0xE6,
    "ACC.7": 0xE7,
    "A.0": 0xE0,
    "A.1": 0xE1,
    "A.2": 0xE2,
    "A.3": 0xE3,
    "A.4": 0xE4,
    "A.5": 0xE5,
    "A.6": 0xE6,
    "A.7": 0xE7,
    "B.0": 0xF0,
    "B.1": 0xF1,
    "B.2": 0xF2,
    "B.3": 0xF3,
    "B.4": 0xF4,
    "B.5": 0xF5,
    "B.6": 0xF6,
    "B.7": 0xF7,
}


class syntax_match():
    def __init__(self) -> None:
        self.label = lambda x: re.match(r"^(\w*?):", x)  # MAIN:
        self.normal_word = lambda x: re.match(r"^(\w*?)$", x)  # LABEL
        self.hex = lambda x: re.match(r"^([0-9A-F]+?)H$", x)  # EEH
        self.dec = lambda x: re.match(r"^([0-9]+?)$", x)  # 255
        self.imm_hex = lambda x: re.match(r"^#([0-9A-F]+?)H$", x
                                          )  # hashtag EEH
        self.imm_dec = lambda x: re.match(r"^#([0-9]+?)$", x)  # hashtag 255
        self.internal_R_ram = lambda x: re.match(r"^@R(\d?)", x)  # @R0
        self.general_reg = lambda x: re.match(r"^R(\d?)", x)  # R7
        self.inverse_bit = lambda x: re.match(r"^\/(.*?)$", x)  # /P0.0

    def sfr_bit(self, x):
        for name in SFRs_bit.keys():
            if x == name:
                return SFRs_bit[x]
        return None

    def sfr(self, x):
        for name in SFRs.keys():
            if x == name:
                return SFRs[x]
        return None


sym = syntax_match()


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
    if label not in SYMTAB.keys():
        print(label, SYMTAB)
        err(f"label: {label} not found.")
    addr = ("{:0" + str(bit) + "b}").format(SYMTAB[label])
    return addr


def label_process(ins, label):
    LABELPROCESSTABLE.append({"instruction": ins, "label": label})


def insert_label(label):
    if label in SYMTAB.keys():
        err(f"label: {label} already been used.")
    SYMTAB[label] = LOCCTR


def write_rom(opcodes):
    global LOCCTR
    global ROM
    print(" ".join([hex(i) for i in opcodes]))
    for o in opcodes:
        ROM[LOCCTR] = o
        LOCCTR += 1


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


def twos_comp(val):
    if val >= 0:
        return val
    return int("{:08b}".format((-val ^ 0xff) + 1), 2)


def pass_1st(asm_code):
    optab = []
    for f_line, ll in asm_code:
        # label
        if (label := sym.label(ll)) != None:
            optab.append((f_line, "label", label[1], None))
            continue
        # instructions
        instruction = ll.split()
        ins, args = instruction[0], "".join(instruction[1:])
        ins = ins.upper()
        args = args.upper().replace(" ", "").replace("\t", "").split(",")
        optab.append((f_line, "instruction", ins, args))
    return optab


def pass_2nd(optab):
    global LOCCTR
    LOCCTR = 0
    for f_line, ins_type, ins, args in optab:
        if ins_type == "label":
            insert_label(ins)
            continue
        print(ins, args)
        if ins == "ORG":
            check_args(ins, args, [1], f_line)
            if (v := sym.hex(args[0])) != None:
                LOCCTR = int(v[1], 16)
            elif (v := sym.dec(args[0])) != None:
                LOCCTR = int(v[1])
            else:
                ins_err(ins, f_line)
        elif ins == "NOP":
            write_rom([0x01])
        elif ins == "AJMP":
            check_args(ins, args, [1], f_line)
            if (v := sym.normal_word(args[0])) != None:
                write_rom([0xA5, 0xA5])
                label_process("AJMP", v[0])
            else:
                ins_err(ins, f_line)
        elif ins == "LJMP" or ins == "JMP":
            check_args(ins, args, [1], f_line)
            if (v := sym.normal_word(args[0])) != None:
                write_rom([0xA5, 0xA5, 0xA5])
                label_process("LJMP", v[0])
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
            elif args[0] == "DLOCCTR":
                write_rom([0xA3])
            elif (v := sym.internal_R_ram(args[0])) != None:
                write_rom([0x06 + int(v[1])])
            elif (v := sym.general_reg(args[0])) != None:
                write_rom([0x08 + int(v[1])])
            elif (v := sym.sfr(args[0])) != None:
                write_rom([0x05, v])
            elif (v := sym.hex(args[0])) != None:
                write_rom([0x05, int(v[1], 16)])
            elif (v := sym.dec(args[0])) != None:
                write_rom([0x05, int(v[1])])
            else:
                ins_err(ins, f_line)
        elif ins == "JBC":
            check_args(ins, args, [2], f_line)
            bit_addr = 0
            offset = 0
            if (v := sym.sfr_bit(args[0])) != None:
                bit_addr = v
            elif (v := sym.hex(args[0])) != None:
                bit_addr = int(v[0], 16)
            elif (v := sym.dec(args[0])) != None:
                bit_addr = int(v[0])
            else:
                ins_err(ins, f_line)
            if (v := sym.normal_word(args[1])) != None:
                offset = 0xA5
                label_process("JBC", v[0])
            else:
                ins_err(ins, f_line)
            write_rom([0x10, bit_addr, offset])
        elif ins == "ACALL":
            check_args(ins, args, [1], f_line)
            if (v := sym.normal_word(args[0])) != None:
                write_rom([0xA5, 0xA5])
                label_process("ACALL", v[0])
            else:
                ins_err(ins, f_line)
        elif ins == "LCALL":
            check_args(ins, args, [1], f_line)
            if (v := sym.normal_word(args[0])) != None:
                write_rom([0xA5, 0xA5, 0xA5])
                label_process("LCALL", v[0])
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
                write_rom([0x15, v])
            elif (v := sym.hex(args[0])) != None:
                write_rom([0x15, int(v[1], 16)])
            elif (v := sym.dec(args[0])) != None:
                write_rom([0x15, int(v[1])])
            else:
                ins_err(ins, f_line)
        elif ins == "JB":
            check_args(ins, args, [2], f_line)
            bit_addr = 0
            offset = 0
            if (v := sym.sfr_bit(args[0])) != None:
                bit_addr = v
            elif (v := sym.hex(args[0])) != None:
                bit_addr = int(v[0], 16)
            elif (v := sym.dec(args[0])) != None:
                bit_addr = int(v[0])
            else:
                ins_err(ins, f_line)
            if (v := sym.normal_word(args[1])) != None:
                offset = 0xA5
                label_process("JB", v[0])
            else:
                ins_err(ins, f_line)
            write_rom([0x20, bit_addr, offset])
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
            elif (v := sym.sfr(args[1])) != None:
                write_rom([0x25, v])
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
            bit_addr = 0
            offset = 0
            if (v := sym.sfr_bit(args[0])) != None:
                bit_addr = v
            elif (v := sym.hex(args[0])) != None:
                bit_addr = int(v[0], 16)
            elif (v := sym.dec(args[0])) != None:
                bit_addr = int(v[0])
            else:
                ins_err(ins, f_line)
            if (v := sym.normal_word(args[1])) != None:
                offset = 0xA5
                label_process("JNB", v[0])
            else:
                ins_err(ins, f_line)
            write_rom([0x30, bit_addr, offset])
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
            elif (v := sym.sfr(args[1])) != None:
                write_rom([0x35, v])
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
            offset = 0
            if (v := sym.normal_word(args[0])) != None:
                offset = 0xA5
                label_process("JC", v[0])
            else:
                ins_err(ins, f_line)
            write_rom([0x40, offset])
        elif ins == "ORL":
            if args[0] == "A":
                if (v := sym.internal_R_ram(args[1])) != None:
                    write_rom([0x46 + int(v[1])])
                elif (v := sym.general_reg(args[1])) != None:
                    write_rom([0x48 + int(v[1])])
                elif (v := sym.sfr(args[1])) != None:
                    write_rom([0x45, v])
                elif (v := sym.hex(args[1])) != None:
                    write_rom([0x45, int(v[1], 16)])
                elif (v := sym.dec(args[1])) != None:
                    write_rom([0x45, int(v[1])])
                elif (v := sym.imm_hex(args[1])) != None:
                    write_rom([0x44, int(v[1], 16)])
                elif (v := sym.imm_dec(args[1])) != None:
                    write_rom([0x44, int(v[1])])
                else:
                    ins_err(ins, f_line)
            elif args[0] == "C":
                bit = args[1]
                opcode = 0x72
                if (v := sym.inverse_bit(args[1])) != None:
                    bit = v[1]
                    opcode = 0xA0
                if (v := sym.sfr_bit(bit)) != None:
                    write_rom([opcode, v])
                elif (v := sym.hex(bit)) != None:
                    write_rom([opcode, int(v[1], 16)])
                elif (v := sym.dec(bit)) != None:
                    write_rom([opcode, int(v[1])])
                else:
                    ins_err(ins, f_line)
            else:
                if args[1] == "A":
                    if (v := sym.sfr(args[0])) != None:
                        write_rom([0x42, v])
                    elif (v := sym.hex(args[0])) != None:
                        write_rom([0x42, int(v[1], 16)])
                    elif (v := sym.dec(args[0])) != None:
                        write_rom([0x42, int(v[1])])
                    else:
                        ins_err(ins, f_line)
                elif (v := sym.imm_hex(args[1])) != None:
                    immediate = int(v[1], 16)
                    if (v := sym.sfr(args[0])) != None:
                        write_rom([0x43, v, immediate])
                    elif (v := sym.hex(args[0])) != None:
                        write_rom([0x43, int(v[1], 16), immediate])
                    elif (v := sym.dec(args[0])) != None:
                        write_rom([0x43, int(v[1]), immediate])
                    else:
                        ins_err(ins, f_line)
                elif (v := sym.imm_dec(args[1])) != None:
                    immediate = int(v[1])
                    if (v := sym.sfr(args[0])) != None:
                        write_rom([0x43, v, immediate])
                    elif (v := sym.hex(args[0])) != None:
                        write_rom([0x43, int(v[1], 16), immediate])
                    elif (v := sym.dec(args[0])) != None:
                        write_rom([0x43, int(v[1]), immediate])
                    else:
                        ins_err(ins, f_line)
                else:
                    ins_err(ins, f_line)
        elif ins == "JNC":
            check_args(ins, args, [1], f_line)
            offset = 0
            if (v := sym.normal_word(args[0])) != None:
                offset = 0xA5
                label_process("JNC", v[0])
            else:
                ins_err(ins, f_line)
            write_rom([0x50, offset])
        elif ins == "ANL":
            if args[0] == "A":
                if (v := sym.internal_R_ram(args[1])) != None:
                    write_rom([0x56 + int(v[1])])
                elif (v := sym.general_reg(args[1])) != None:
                    write_rom([0x58 + int(v[1])])
                elif (v := sym.sfr(args[1])) != None:
                    write_rom([0x55, v])
                elif (v := sym.hex(args[1])) != None:
                    write_rom([0x55, int(v[1], 16)])
                elif (v := sym.dec(args[1])) != None:
                    write_rom([0x55, int(v[1])])
                elif (v := sym.imm_hex(args[1])) != None:
                    write_rom([0x54, int(v[1], 16)])
                elif (v := sym.imm_dec(args[1])) != None:
                    write_rom([0x54, int(v[1])])
                else:
                    ins_err(ins, f_line)
            elif args[0] == "C":
                bit = args[1]
                opcode = 0x82
                if (v := sym.inverse_bit(args[1])) != None:
                    bit = v[1]
                    opcode = 0xB0
                if (v := sym.sfr_bit(bit)) != None:
                    write_rom([opcode, v])
                elif (v := sym.hex(bit)) != None:
                    write_rom([opcode, int(v[1], 16)])
                elif (v := sym.dec(bit)) != None:
                    write_rom([opcode, int(v[1])])
                else:
                    ins_err(ins, f_line)
            else:
                if args[1] == "A":
                    if (v := sym.sfr(args[0])) != None:
                        write_rom([0x52, v])
                    elif (v := sym.hex(args[0])) != None:
                        write_rom([0x52, int(v[1], 16)])
                    elif (v := sym.dec(args[0])) != None:
                        write_rom([0x52, int(v[1])])
                    else:
                        ins_err(ins, f_line)
                elif (v := sym.imm_hex(args[1])) != None:
                    immediate = int(v[1], 16)
                    if (v := sym.sfr(args[0])) != None:
                        write_rom([0x53, v, immediate])
                    elif (v := sym.hex(args[0])) != None:
                        write_rom([0x53, int(v[1], 16), immediate])
                    elif (v := sym.dec(args[0])) != None:
                        write_rom([0x53, int(v[1]), immediate])
                    else:
                        ins_err(ins, f_line)
                elif (v := sym.imm_dec(args[1])) != None:
                    immediate = int(v[1])
                    if (v := sym.sfr(args[0])) != None:
                        write_rom([0x53, v, immediate])
                    elif (v := sym.hex(args[0])) != None:
                        write_rom([0x53, int(v[1], 16), immediate])
                    elif (v := sym.dec(args[0])) != None:
                        write_rom([0x53, int(v[1]), immediate])
                    else:
                        ins_err(ins, f_line)
                else:
                    ins_err(ins, f_line)
        elif ins == "JZ":
            check_args(ins, args, [1], f_line)
            offset = 0
            if (v := sym.normal_word(args[0])) != None:
                offset = 0xA5
                label_process("JZ", v[0])
            else:
                ins_err(ins, f_line)
            write_rom([0x60, offset])
        elif ins == "XRL":
            if args[0] == "A":
                if (v := sym.internal_R_ram(args[1])) != None:
                    write_rom([0x66 + int(v[1])])
                elif (v := sym.general_reg(args[1])) != None:
                    write_rom([0x68 + int(v[1])])
                elif (v := sym.sfr(args[1])) != None:
                    write_rom([0x65, v])
                elif (v := sym.hex(args[1])) != None:
                    write_rom([0x65, int(v[1], 16)])
                elif (v := sym.dec(args[1])) != None:
                    write_rom([0x65, int(v[1])])
                elif (v := sym.imm_hex(args[1])) != None:
                    write_rom([0x64, int(v[1], 16)])
                elif (v := sym.imm_dec(args[1])) != None:
                    write_rom([0x64, int(v[1])])
                else:
                    ins_err(ins, f_line)
            else:
                if args[1] == "A":
                    if (v := sym.sfr(args[0])) != None:
                        write_rom([0x62, v])
                    elif (v := sym.hex(args[0])) != None:
                        write_rom([0x62, int(v[1], 16)])
                    elif (v := sym.dec(args[0])) != None:
                        write_rom([0x62, int(v[1])])
                    else:
                        ins_err(ins, f_line)
                elif (v := sym.imm_hex(args[1])) != None:
                    immediate = int(v[1], 16)
                    if (v := sym.sfr(args[0])) != None:
                        write_rom([0x63, v, immediate])
                    elif (v := sym.hex(args[0])) != None:
                        write_rom([0x63, int(v[1], 16), immediate])
                    elif (v := sym.dec(args[0])) != None:
                        write_rom([0x63, int(v[1]), immediate])
                    else:
                        ins_err(ins, f_line)
                elif (v := sym.imm_dec(args[1])) != None:
                    immediate = int(v[1])
                    if (v := sym.sfr(args[0])) != None:
                        write_rom([0x63, v, immediate])
                    elif (v := sym.hex(args[0])) != None:
                        write_rom([0x63, int(v[1], 16), immediate])
                    elif (v := sym.dec(args[0])) != None:
                        write_rom([0x63, int(v[1]), immediate])
                    else:
                        ins_err(ins, f_line)
                else:
                    ins_err(ins, f_line)
        elif ins == "MOV":
            check_args(ins, args, [2], f_line)
            if (v := sym.internal_R_ram(args[0])) != None:
                Ri = int(v[1])
                if args[1] == "A":
                    write_rom([0xF6 + Ri])
                elif (v := sym.imm_hex(args[1])) != None:
                    write_rom([0x76 + Ri, int(v[1], 16)])
                elif (v := sym.imm_dec(args[1])) != None:
                    write_rom([0x76 + Ri, int(v[1])])
                elif (v := sym.sfr(args[1])) != None:
                    write_rom([0xA6 + Ri, v])
                elif (v := sym.hex(args[1])) != None:
                    write_rom([0xA6 + Ri, int(v[1], 16)])
                elif (v := sym.dec(args[1])) != None:
                    write_rom([0xA6 + Ri, int(v[1])])
                else:
                    ins_err(ins, f_line)
            elif args[0] == "A":
                if (v := sym.internal_R_ram(args[1])) != None:
                    write_rom([0xE6 + int(v[1])])
                elif (v := sym.general_reg(args[1])) != None:
                    write_rom([0xE8 + int(v[1])])
                elif (v := sym.imm_hex(args[1])) != None:
                    write_rom([0x74, int(v[1], 16)])
                elif (v := sym.imm_dec(args[1])) != None:
                    write_rom([0x74, int(v[1])])
                elif (v := sym.sfr(args[1])) != None:
                    write_rom([0xE5, v])
                elif (v := sym.hex(args[1])) != None:
                    write_rom([0xE5, int(v[1], 16)])
                elif (v := sym.dec(args[1])) != None:
                    write_rom([0xE5, int(v[1])])
                else:
                    ins_err(ins, f_line)
            elif args[0] == "C":
                if (v := sym.hex(args[1])) != None:
                    write_rom([0xA2, int(v[1], 16)])
                elif (v := sym.dec(args[1])) != None:
                    write_rom([0xA2, int(v[1])])
                elif (v := sym.sfr_bit(args[1])) != None:
                    write_rom([0xA2, v])
                else:
                    ins_err(ins, f_line)
            elif args[1] == "C":
                if (v := sym.hex(args[0])) != None:
                    write_rom([0x92, int(v[1], 16)])
                elif (v := sym.dec(args[0])) != None:
                    write_rom([0x92, int(v[1])])
                elif (v := sym.sfr_bit(args[0])) != None:
                    write_rom([0x92, v])
                else:
                    ins_err(ins, f_line)
            elif args[0] == "DPTR":
                if (v := sym.imm_hex(args[1])) != None:
                    imm_val = int(v[1], 16)
                    write_rom([0x90, imm_val // 256, imm_val % 256])
                elif (v := sym.imm_dec(args[1])) != None:
                    imm_val = int(v[1])
                    write_rom([0x90, imm_val // 256, imm_val % 256])
                else:
                    ins_err(ins, f_line)
            elif (v := sym.general_reg(args[0])) != None:
                Rn = int(v[1])
                if args[1] == "A":
                    write_rom([0xF8 + Rn])
                elif (v := sym.imm_hex(args[1])) != None:
                    write_rom([0x78 + Rn, int(v[1], 16)])
                elif (v := sym.imm_dec(args[1])) != None:
                    write_rom([0x78 + Rn, int(v[1])])
                elif (v := sym.sfr(args[1])) != None:
                    write_rom([0xA8 + Rn, v])
                elif (v := sym.hex(args[1])) != None:
                    write_rom([0xA8 + Rn, int(v[1], 16)])
                elif (v := sym.dec(args[1])) != None:
                    write_rom([0xA8 + Rn, int(v[1])])
                else:
                    ins_err(ins, f_line)
            else:
                val = -1
                if (v := sym.sfr(args[0])) != None:
                    val = int(v)
                elif (v := sym.hex(args[0])) != None:
                    val = int(v[1], 16)
                elif (v := sym.dec(args[0])) != None:
                    val = int(v[1])
                else:
                    ins_err(ins, f_line)
                if args[1] == "A":
                    write_rom([0xF5, val])
                elif (v := sym.imm_hex(args[1])) != None:
                    write_rom([0x75, val, int(v[1], 16)])
                elif (v := sym.imm_dec(args[1])) != None:
                    write_rom([0x75, val, int(v[1])])
                elif (v := sym.sfr(args[1])) != None:
                    write_rom([0x85, v, val])
                elif (v := sym.hex(args[1])) != None:
                    write_rom([0x85, int(v[1], 16), val])
                elif (v := sym.dec(args[1])) != None:
                    write_rom([0x85, int(v[1]), val])
                elif (v := sym.general_reg(args[1])) != None:
                    write_rom([0x88 + int(v[1]), val])
                elif (v := sym.internal_R_ram(args[1])) != None:
                    write_rom([0x86 + int(v[1]), val])
                else:
                    ins_err(ins, f_line)
        elif ins == "JNZ":
            check_args(ins, args, [1], f_line)
            offset = 0
            if (v := sym.normal_word(args[0])) != None:
                offset = 0xA5
                label_process("JNZ", v[0])
            else:
                ins_err(ins, f_line)
            write_rom([0x70, offset])
        elif ins == "SJMP":
            check_args(ins, args, [1], f_line)
            offset = 0
            if (v := sym.normal_word(args[0])) != None:
                offset = 0xA5
                label_process("SJMP", v[0])
            else:
                ins_err(ins, f_line)
            write_rom([0x80, offset])
        elif ins == "MOVC":
            if args[0] == "A":
                pass
            else:
                ins_err(ins, f_line)
            if args[1] == "@A+DPTR":
                write_rom([0x93])
            elif args[1] == "@A+PC":
                write_rom(0x83)
            else:
                ins_err(ins, f_line)
        elif ins == "DIV":
            if args[0] == "AB":
                write_rom([0x84])
            else:
                ins_err(ins, f_line)
        elif ins == "SUBB":
            check_args(ins, args, [2], f_line)
            if args[0] == "A":
                pass
            else:
                ins_err(ins, f_line)
            if (v := sym.internal_R_ram(args[1])) != None:
                write_rom([0x96 + int(v[1])])
            elif (v := sym.general_reg(args[1])) != None:
                write_rom([0x98 + int(v[1])])
            elif (v := sym.sfr(args[1])) != None:
                write_rom([0x95, v])
            elif (v := sym.hex(args[1])) != None:
                write_rom([0x95, int(v[1], 16)])
            elif (v := sym.dec(args[1])) != None:
                write_rom([0x95, int(v[1])])
            elif (v := sym.imm_hex(args[1])) != None:
                write_rom([0x94, int(v[1], 16)])
            elif (v := sym.imm_dec(args[1])) != None:
                write_rom([0x94, int(v[1])])
            else:
                ins_err(ins, f_line)
        elif ins == "MUL":
            if args[0] == "AB":
                write_rom([0xA3])
            else:
                ins_err(ins, f_line)
        elif ins == "CPL":
            check_args(ins, args, [2], f_line)
            if args[0] == "A":
                write_rom([0xF4])
            elif args[0] == "C":
                write_rom([0xB3])
            else:
                if (v := sym.sfr_bit(args[1])) != None:
                    write_rom([0xB2 + v])
                elif (v := sym.hex(args[1])) != None:
                    write_rom([0xB2, int(v[1], 16)])
                elif (v := sym.dec(args[1])) != None:
                    write_rom([0xB2, int(v[1])])
                else:
                    ins_err(ins, f_line)
        elif ins == "CJNE":
            check_args(ins, args, [3], f_line)
            if args[0] == "A":
                if (v := sym.imm_hex(args[1])) != None:
                    write_rom([0xB4, int(v[1], 16), 0xA5])
                elif (v := sym.imm_dec(args[1])) != None:
                    write_rom([0xB4, int(v[1]), 0xA5])
                elif (v := sym.sfr(args[1])) != None:
                    write_rom([0xB4, v, 0xA5])
                elif (v := sym.hex(args[1])) != None:
                    write_rom([0xB5, int(v[1], 16), 0xA5])
                elif (v := sym.dec(args[1])) != None:
                    write_rom([0xB5, int(v[1]), 0xA5])
                else:
                    ins_err(ins, f_line)
            elif (v := sym.internal_R_ram(args[0])) != None:
                opcode = 0xB6 + int(v[1])
                if (v := sym.imm_hex(args[1])) != None:
                    write_rom([opcode, int(v[1], 16), 0xA5])
                elif (v := sym.imm_dec(args[1])) != None:
                    write_rom([opcode, int(v[1]), 0xA5])
                else:
                    ins_err(ins, f_line)
            elif (v := sym.general_reg(args[0])) != None:
                opcode = 0xB8 + int(v[1])
                if (v := sym.imm_hex(args[1])) != None:
                    write_rom([opcode, int(v[1], 16), 0xA5])
                elif (v := sym.imm_dec(args[1])) != None:
                    write_rom([opcode, int(v[1]), 0xA5])
                else:
                    ins_err(ins, f_line)
            else:
                ins_err(ins, f_line)
            if (v := sym.normal_word(args[2])) != None:
                label_process("CJNE", v[1])
            else:
                ins_err(ins, f_line)
        elif ins == "PUSH":
            check_args(ins, args, [1], f_line)
            if (v := sym.sfr(args[0])) != None:
                write_rom([0xC0, v])
            elif (v := sym.hex(args[0])) != None:
                write_rom([0xC0, int(v[1], 16)])
            elif (v := sym.dec(args[0])) != None:
                write_rom([0xC0, int(v[1])])
            else:
                ins_err(ins, f_line)
        elif ins == "CLR":
            check_args(ins, args, [1], f_line)
            if args[0] == "A":
                write_rom([0xE4])
            elif args[0] == "C":
                write_rom([0xC3])
            elif (v := sym.hex(args[0])) != None:
                write_rom([0xC2, int(v[1], 16)])
            elif (v := sym.dec(args[0])) != None:
                write_rom([0xC2, int(v[1])])
            elif (v := sym.sfr_bit(args[0])) != None:
                write_rom([0xC2, v])
            else:
                ins_err(ins, f_line)
        elif ins == "SWAP":
            check_args(ins, args, [1], f_line)
            if args[0] == "A":
                write_rom([0xC4])
            else:
                ins_err(ins, f_line)
        elif ins == "XCH":
            check_args(ins, args, [2], f_line)
            if args[0] == "A":
                pass
            else:
                ins_err(ins, f_line)
            if (v := sym.internal_R_ram(args[1])) != None:
                write_rom([0xC6 + int(v[1])])
            elif (v := sym.general_reg(args[1])) != None:
                write_rom([0xC8 + int(v[1])])
            elif (v := sym.hex(args[0])) != None:
                write_rom([0xC5, int(v[1], 16)])
            elif (v := sym.dec(args[0])) != None:
                write_rom([0xC5, int(v[1])])
            elif (v := sym.sfr(args[0])) != None:
                write_rom([0xC5, v])
            else:
                ins_err(ins, f_line)
        elif ins == "POP":
            check_args(ins, args, [1], f_line)
            if (v := sym.sfr(args[0])) != None:
                write_rom([0xD0, v])
            elif (v := sym.hex(args[0])) != None:
                write_rom([0xD0, int(v[1], 16)])
            elif (v := sym.dec(args[0])) != None:
                write_rom([0xD0, int(v[1])])
            else:
                ins_err(ins, f_line)
        elif ins == "SETB":
            check_args(ins, args, [1], f_line)
            if args[0] == "C":
                write_rom([0xD3])
            elif (v := sym.hex(args[0])) != None:
                write_rom([0xD2, int(v[1], 16)])
            elif (v := sym.dec(args[0])) != None:
                write_rom([0xD2, int(v[1])])
            elif (v := sym.sfr_bit(args[0])) != None:
                write_rom([0xD2, v])
            else:
                ins_err(ins, f_line)
        elif ins == "DA":
            check_args(ins, args, [1], f_line)
            if args[0] == "A":
                write_rom([0xD4])
            else:
                ins_err(ins, f_line)
        elif ins == "DJNZ":
            check_args(ins, args, [2], f_line)
            if (v := sym.sfr(args[0])) != None:
                write_rom([0xD5, v, 0xA5])
            elif (v := sym.hex(args[0])) != None:
                write_rom([0xD5, int(v[1], 16), 0xA5])
            elif (v := sym.dec(args[0])) != None:
                write_rom([0xD5, int(v[1]), 0xA5])
            elif (v := sym.general_reg(args[0])) != None:
                write_rom([0xD8 + int(v[1]), 0xA5])
            else:
                ins_err(ins, f_line)
            if (v := sym.normal_word(args[1])) != None:
                label_process("DJNZ", v[1])
            else:
                ins_err(ins, f_line)
        elif ins == "XCHD":
            check_args(ins, args, [2], f_line)
            if args[0] == "A":
                pass
            else:
                ins_err(ins, f_line)
            if (v := sym.internal_R_ram(args[1])) != None:
                write_rom([0xD6 + int(v[1])])
            else:
                ins_err(ins, f_line)
        elif ins == "MOVX":
            check_args(ins, args, [2], f_line)
            if args[0] == "A":
                if args[1] == "@DPTR":
                    write_rom([0xE0])
                elif (v := sym.internal_R_ram(args[1])) != None:
                    write_rom([0xE2 + int(v[1])])
                else:
                    ins_err(ins, f_line)
            elif (v := sym.internal_R_ram(args[0])) != None:
                if args[1] == "A":
                    write_rom([0xF2 + int(v[1])])
                else:
                    ins_err(ins, f_line)
            else:
                ins_err(ins, f_line)
        else:
            err_line(f"unknown instruction \"{ins}\"", f_line)


def replace_label():
    PTR = 0
    T = 0
    while PTR < len(ROM):
        if ROM[PTR] == 0xA5:
            now = LABELPROCESSTABLE[T]
            ins = now["instruction"]
            l = now["label"]
            if ins in ["JB", "JNB", "JBC"]:
                label_addr = int(search_label(l, 11), 2)
                offset = twos_comp(label_addr - PTR)
                ROM[PTR] = offset
                PTR += 1
                T += 1
            elif ins in ["JC", "JNC", "JZ", "JNZ", "SJMP", "CJNE", "DJNZ"]:
                label_addr = int(search_label(l, 11), 2)
                offset = twos_comp(label_addr - PTR - 1)
                ROM[PTR] = offset
                PTR += 1
                T += 1
            elif ins == "AJMP":
                addr11 = search_label(l, 11)
                ROM[PTR:PTR +
                    2] = [int(addr11[:3] + "00001", 2),
                          int(addr11[3:], 2)]
                PTR += 2
                T += 1
            elif ins == "ACALL":
                addr11 = search_label(l, 11)
                ROM[PTR:PTR +
                    2] = [int(addr11[:3] + "10001", 2),
                          int(addr11[3:], 2)]
                PTR += 2
                T += 1
            elif ins == "LJMP":
                addr16 = search_label(l, 16)
                ROM[PTR:PTR + 3] = [
                    0x02,
                    int(addr16[:8], 2),
                    int(addr16[8:], 2),
                ]
                PTR += 3
                T += 1
            elif ins == "LCALL":
                addr16 = search_label(l, 16)
                ROM[PTR:PTR + 3] = [
                    0x12,
                    int(addr16[:8], 2),
                    int(addr16[8:], 2),
                ]
                PTR += 3
                T += 1
            else:
                PTR += 1
        else:
            PTR += 1


def parser(asm_code):
    asm_code = remove_space_comment(asm_code)
    optab = pass_1st(asm_code)
    pass_2nd(optab)
    replace_label()
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
