from collections import namedtuple
import re

from tokens import token


class Command:
    def __init__(self, bit_pattern, mnemonic, *operands):
        self.bit_pattern = bit_pattern
        self.mnemonic = mnemonic
        self.operands = operands

    def match(self, opcode):
        if type(opcode) == int:
            opcode = bin(opcode)[2:].rjust(8, "0")
        return bool(re.match(self.bit_pattern, opcode))


_commands = [
    Command("00000000", "nop"),
    Command("...00001", "ajmp", "addr11"),
    Command("00000010", "ljmp", "addr16"),
    Command("00000011", "rr", "a"),
    Command("00000100", "inc", "a"),
    Command("00000101", "inc", "direct"),
    Command("0000011.", "inc", "indirect"),
    Command("00001...", "inc", "register"),
    Command("00010000", "jbc", "bit", "offset"),
    Command("...10001", "acall", "addr11"),
    Command("...10010", "lcall", "addr16"),
    Command("00010011", "rrc", "a"),
    Command("00010100", "dec", "a"),
    Command("00010101", "dec", "direct"),
    Command("0001011.", "dec", "indirect"),
    Command("00011...", "dec", "register"),
    Command("00100000", "jb", "bit", "offset")
]


class Intel8051StateMachine:
    def __init__(self, byte_source, commands=_commands):
        self.current_opcode = None
        self.byte_source = iter(byte_source)
        self.commands = commands
        self.tokens = []

    def next_byte(self):
        return next(self.byte_source)

    def consume_command(self):
        opcode = self.current_opcode = self.next_byte()
        command = self.get_matching_command(opcode)
        self.tokens.append(token("opcode", command.mnemonic))

        for operand in command.operands:
            self.consume_operand(operand)

        self.tokens.append(token("eoi"))

    def consume_operand(self, operand):
        terminal = operand
        if operand == "addr11":
            address = (self.current_opcode & 0b11100000) << 3
            address += self.next_byte()
            value = address
        elif operand == "addr16":
            address = self.next_byte() << 8
            address += self.next_byte()
            value = address
        elif operand == "register":
            register = self.current_opcode & 0b00000111
            value = register
        elif operand == "a":
            terminal = "sfr"
            value = "a"
        elif operand == "bit":
            value = self.next_byte()
        elif operand == "offset":
            value = self.next_byte()
        else:
            raise Exception("Unknown operand {}".format(operand))
        self.tokens.append(token(terminal, value))

    def listing(self):
        return ''.join(self.iterate_token_values())

    def iterate_token_values(self):
        last_token = None
        for token in self.tokens:
            if token.terminal is "opcode":
                yield str(token).ljust(8)
            elif token.is_operand and last_token.is_operand:
                yield ", "
                yield str(token)
            else:
                yield str(token)
            last_token = token

    def get_matching_command(self, opcode):
        for command in self.commands:
            if command.match(opcode):
                return command
