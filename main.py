#!/usr/bin/python3
import re
import os

ROM = [0x00] * (2**16)
PTR = 0
label_dict = {}


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
    addr = ("{:0"+str(bit)+"b}").format(label_dict[label])
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


def create_label(asm_code):
    global PTR
    for f_line, ll in enumerate(asm_code.split("\n")):
        ll = ll.lstrip()
        ll = re.sub(';(.*)', "", ll)
        # empty line
        if len(ll) == 0:
            continue
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
            if (v := re.match(r"^(\d*?)H", args[0])) != None:
                PTR = int(v[1], 16)


def parser(asm_code):
    global PTR
    create_label(asm_code)
    PTR = 0
    for f_line, ll in enumerate(asm_code.split("\n")):
        f_line += 1
        ll = ll.lstrip()
        ll = re.sub(';(.*)', "", ll)
        # empty line
        if len(ll) == 0:
            continue
        # instructions
        instruction = ll.split()
        ins, args = instruction[0], "".join(instruction[1:])
        ins = ins.upper()
        args = args.upper().replace(" ", "").replace("\t", "").split(",")
        print(f"I: {ins} {args}")
        if ins == "ORG":
            check_args(ins, args, [1], f_line)
            if (v := re.match(r"^(\d*?)H", args[0])) != None:
                PTR = int(v[1], 16)
        elif ins == "NOP":
            write_rom([0x01])
        elif ins == "AJMP":
            check_args(ins, args, [1], f_line)
            if (v := re.match(r"^(\w*?)$", args[0])) != None:
                addr11 = search_label(v[0], 11)
                write_rom([int(addr11[8:][::-1] + "00001", 2),
                           int(addr11[0:8][::-1], 2)])
            else:
                ins_err(ins, f_line)
        elif ins == "LJMP":
            check_args(ins, args, [1], f_line)
            if (v := re.match(r"^(\w*?)$", args[0])) != None:
                addr16 = search_label(v[0], 16)
                write_rom([0x02, int(addr16[8:16][::-1], 2),
                           int(addr16[0:8][::-1], 2)])
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
            elif (v := re.match(r"^@R(\d?)", args[0])) != None:
                write_rom([0x06 + int(v[1])])
            elif (v := re.match(r"^R(\d?)", args[0])) != None:
                write_rom([0x08 + int(v[1])])
            elif (v := re.match(r"^(\d*?)H", args[0])) != None:
                write_rom([0x05, int(v[1], 16)])
            elif (v := re.match(r"^(\d*?)", args[0])) != None:
                write_rom([0x05, int(v[1])])
            else:
                ins_err(ins, f_line)
        elif ins == "JBC":
            check_args(ins, args, [2], f_line)
        elif ins == "ACALL":
            check_args(ins, args, [1], f_line)
            if (v := re.match(r"^(\w*?)$", args[0])) != None:
                addr11 = search_label(v[0], 11)
                write_rom([int(addr11[8:][::-1] + "10001", 2),
                           int(addr11[0:8][::-1], 2)])
            else:
                ins_err(ins, f_line)
        elif ins == "LCALL":
            check_args(ins, args, [1], f_line)
            if (v := re.match(r"^(\w*?)$", args[0])) != None:
                addr16 = search_label(v[0], 16)
                write_rom([0x12, int(addr16[8:16][::-1], 2),
                           int(addr16[0:8][::-1], 2)])
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
            elif (v := re.match(r"^@R(\d?)", args[0])) != None:
                write_rom([0x16 + int(v[1])])
            elif (v := re.match(r"^R(\d?)", args[0])) != None:
                write_rom([0x18 + int(v[1])])
            elif (v := re.match(r"^(\d*?)H", args[0])) != None:
                write_rom([0x15, int(v[1], 16)])
            elif (v := re.match(r"^(\d*?)", args[0])) != None:
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
            if (v := re.match(r"^@R(\d?)", args[1])) != None:
                write_rom([0x26 + int(v[1])])
            elif (v := re.match(r"^R(\d?)", args[1])) != None:
                write_rom([0x28 + int(v[1])])
            elif (v := re.match(r"^(\d*?)H", args[1])) != None:
                write_rom([0x25, int(v[1], 16)])
            elif (v := re.match(r"^(\d*?)", args[1])) != None:
                write_rom([0x25, int(v[1])])
            elif (v := re.match(r"^#(\d*?)H", args[1])) != None:
                write_rom([0x24, int(v[1], 16)])
            elif (v := re.match(r"^#(\d*?)", args[1])) != None:
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
            if (v := re.match(r"^@R(\d?)", args[1])) != None:
                write_rom([0x36 + int(v[1])])
            elif (v := re.match(r"^R(\d?)", args[1])) != None:
                write_rom([0x38 + int(v[1])])
            elif (v := re.match(r"^(\d*?)H", args[1])) != None:
                write_rom([0x35, int(v[1], 16)])
            elif (v := re.match(r"^(\d*?)", args[1])) != None:
                write_rom([0x35, int(v[1])])
            elif (v := re.match(r"^#(\d*?)H", args[1])) != None:
                write_rom([0x34, int(v[1], 16)])
            elif (v := re.match(r"^#(\d*?)", args[1])) != None:
                write_rom([0x34, int(v[1])])
            else:
                ins_err(ins, f_line)
        elif ins == "JC":
            check_args(ins, args, [1], f_line)
        elif ins == "ADDC":
            if args[0] == "A":
                pass
            else:
                ins_err(ins, f_line)
            if (v := re.match(r"^@R(\d?)", args[1])) != None:
                write_rom([0x36 + int(v[1])])
            elif (v := re.match(r"^R(\d?)", args[1])) != None:
                write_rom([0x38 + int(v[1])])
            elif (v := re.match(r"^(\d*?)H", args[1])) != None:
                write_rom([0x35, int(v[1], 16)])
            elif (v := re.match(r"^(\d*?)", args[1])) != None:
                write_rom([0x35, int(v[1])])
            elif (v := re.match(r"^#(\d*?)H", args[1])) != None:
                write_rom([0x34, int(v[1], 16)])
            elif (v := re.match(r"^#(\d*?)", args[1])) != None:
                write_rom([0x34, int(v[1])])
            else:
                ins_err(ins, f_line)
        else:
            pass
            # err_line(f"unknown instruction \"{ins}\"", f_line)
    print(ROM[:100])
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
