from enum import Enum
import re

import tokens


class Operand(Enum):
    IMMEDIATE = 0
    DIRECT = 1
    ADDR11 = 2
    ADDR16 = 3
    BIT = 4
    ACCUMULATOR = 5
    INDIRECT = 6
    REGISTER = 7
    OFFSET = 8


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
    Command("...00001", "ajmp", Operand.ADDR11),
    Command("00000010", "ljmp", Operand.ADDR16),
    Command("00000011", "rr", Operand.ACCUMULATOR),
    Command("00000100", "inc", Operand.ACCUMULATOR),
    Command("00000101", "inc", Operand.DIRECT),
    Command("0000011.", "inc", Operand.INDIRECT),
    Command("00001...", "inc", Operand.REGISTER),
    Command("00010000", "jbc", Operand.BIT, Operand.OFFSET),
    Command("...10001", "acall", Operand.ADDR11),
    Command("...10010", "lcall", Operand.ADDR16),
    Command("00010011", "rrc", Operand.ACCUMULATOR),
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
        self.tokens.append(tokens.OpcodeToken(command.mnemonic))

        for operand in command.operands:
            self.consume_operand(operand)

        self.tokens.append(tokens.EndOfInstrToken())

    def consume_operand(self, operand: Operand):
        if operand == Operand.ADDR11:
            address = (self.current_opcode & 0b11100000) << 3
            address += self.next_byte()
            self.tokens.append(tokens.Addr11Token(address))
        elif operand == Operand.ADDR16:
            address = self.next_byte() << 8
            address += self.next_byte()
            self.tokens.append(tokens.Addr16Token(address))
        elif operand == Operand.REGISTER:
            register = self.current_opcode & 0b00000111
            self.tokens.append(tokens.RegisterToken(register))

    def listing(self):
        return ' '.join(map(str, self.tokens))

    def get_matching_command(self, opcode):
        for command in self.commands:
            if command.match(opcode):
                return command
