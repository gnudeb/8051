from collections import namedtuple
import re

from tokens import token


class ByteSourceExhausted(Exception):
    pass


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
    ("00000000", "nop"),
    ("...00001", "ajmp", "addr11"),
    ("00000010", "ljmp", "addr16"),
    ("00000011", "rr", "a"),
    ("00000100", "inc", "a"),
    ("00000101", "inc", "direct"),
    ("0000011.", "inc", "indirect"),
    ("00001...", "inc", "register"),
    ("00010000", "jbc", "bit", "offset"),
    ("...10001", "acall", "addr11"),
    ("...10010", "lcall", "addr16"),
    ("00010011", "rrc", "a"),
    ("00010100", "dec", "a"),
    ("00010101", "dec", "direct"),
    ("0001011.", "dec", "indirect"),
    ("00011...", "dec", "register"),
    ("00100000", "jb", "bit", "offset"),
    ("00100010", "ret"),
    ("00100011", "rl", "a"),
    ("00100100", "add", "a", "imm8"),
    ("00100101", "add", "direct"),
    ("0010011.", "add", "a", "indirect"),
    ("00101...", "add", "a", "register"),
    ("00110000", "jnb", "bit", "offset"),
    ("00110010", "reti"),
    ("00110011", "rlc", "a"),
    ("00110100", "addc", "a", "imm8"),
    ("00110101", "addc", "a", "direct"),
    ("0011011.", "addc", "a", "indirect"),
    ("00111...", "addc", "a", "register"),
    ("01000000", "jc", "offset"),
    ("01000010", "orl", "direct", "a"),
    ("01000011", "orl", "direct", "immediate"),
    ("01000100", "orl", "a", "imm8"),
    ("01000101", "orl", "a", "direct"),
    ("0100011.", "orl", "a", "register"),
    ("01001...", "orl", "a", "register"),
    ("01010000", "jnc", "offset"),
    ("01010010", "anl", "direct", "a"),
    ("01010011", "anl", "direct", "imm8"),
    ("01010100", "anl", "a", "imm8"),
    ("01010101", "anl", "a", "direct"),
    ("0101011.", "anl", "a", "indirect"),
    ("01011...", "anl", "a", "register"),
    ("01100000", "jz", "offset"),
    ("01100010", "xrl", "direct", "a"),
    ("01100011", "xrl", "direct", "imm8"),
    ("01100100", "xrl", "a", "imm8"),
    ("01100101", "xrl", "a", "direct"),
    ("0110011.", "xrl", "a", "indirect"),
    ("01101...", "xrl", "a", "register"),
    ("01110000", "jnz", "offset"),
]

_commands = [Command(*command) for command in _commands]


class Intel8051StateMachine:
    def __init__(self, byte_source, commands=_commands):
        self.current_opcode = None
        self.byte_source = iter(byte_source)
        self.commands = commands
        self.tokens = []
        self.pending_tokens = []
        self.leftover_bytes = []
        self.program_counter = -1

    def next_byte(self):
        self.program_counter += 1
        try:
            byte = next(self.byte_source)
            self.leftover_bytes.append(byte)
            return byte
        except StopIteration:
            raise ByteSourceExhausted

    def consume_byte_source(self):
        while True:
            try:
                self.consume_command()
            except ByteSourceExhausted:
                if self.pending_tokens:
                    address_token = self.pending_tokens[0]
                    assert address_token.terminal is "address"
                    self.tokens.append(address_token)

                    for byte in self.leftover_bytes:
                        self.tokens.append(token("raw_byte", byte))

                    self.pending_tokens = []
                    self.leftover_bytes = []

                break

    def consume_command(self):
        opcode = self.current_opcode = self.next_byte()
        command = self.get_matching_command(opcode)

        self.pending_tokens.append(token("address", self.program_counter))
        self.pending_tokens.append(token("opcode", command.mnemonic))

        for operand in command.operands:
            self.consume_operand(operand)

        self.pending_tokens.append(token("eoi"))
        self.tokens.extend(self.pending_tokens)
        self.pending_tokens = []
        self.leftover_bytes = []

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
        elif operand == "imm8":
            terminal = "immediate"
            value = self.next_byte()
        elif operand == "indirect":
            value = self.current_opcode & 0b00000001
        else:
            raise Exception("Unknown operand {}".format(operand))
        self.pending_tokens.append(token(terminal, value))

    def listing(self):
        return ''.join(self.iterate_token_values())

    def iterate_token_values(self):
        last_token = None
        for token in self.tokens:
            if token.terminal in ["opcode", "address"]:
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
