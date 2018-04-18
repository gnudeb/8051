
def token(terminal, value=None):
    for child in Token.__subclasses__():
        if child.terminal == terminal:
            return child(value)


class Token:
    terminal = None
    is_operand = False
    is_helper = False

    def __init__(self, value=None):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return "Token <{} {}>".format(self.terminal, self.value)


class OperandMixin:
    is_operand = True


class HelperMixin:
    is_helper = True


class OpcodeToken(Token):
    terminal = "opcode"


class Addr11Token(OperandMixin, Token):
    terminal = "addr11"


class Addr16Token(OperandMixin, Token):
    terminal = "addr16"


class EndOfInstrToken(HelperMixin, Token):
    terminal = "eoi"

    def __str__(self):
        return "\n"


class RegisterToken(OperandMixin, Token):
    terminal = "register"

    def __str__(self):
        return "r{}".format(self.value)


class BitToken(OperandMixin, Token):
    terminal = "bit"

    def __str__(self):
        if self.value < 128:
            byte = 0x20 + (self.value // 8)
            bit = self.value % 8
            return "{:#x}.{}".format(byte, bit)
        raise NotImplementedError("Bit values above 127 not implemented")


class OffsetToken(OperandMixin, Token):
    terminal = "offset"


class SFRToken(OperandMixin, Token):
    terminal = "sfr"


class AddressToken(HelperMixin, Token):
    terminal = "address"

    def __str__(self):
        return "{:04x}".format(self.value)


class ImmediateToken(OperandMixin, Token):
    terminal = "immediate"

    def __str__(self):
        return "#{}".format(self.value)


class RawByteToken(Token):
    terminal = "raw_byte"

    def __str__(self):
        return "{:#04x}".format(self.value)


class IndirectToken(Token):
    terminal = "indirect"

    def __str__(self):
        return "@r{}".format(self.value)
