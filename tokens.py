
def token(terminal, value=None):
    for child in Token.__subclasses__():
        if child.terminal == terminal:
            return child(value)


class Token:
    terminal = None

    def __init__(self, value=None):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return "Token <{} {}>".format(self.terminal, self.value)


class OpcodeToken(Token):
    terminal = "opcode"


class Addr11Token(Token):
    terminal = "addr11"


class Addr16Token(Token):
    terminal = "addr16"


class EndOfInstrToken(Token):
    terminal = "eoi"

    def __str__(self):
        return "\n"


class RegisterToken(Token):
    terminal = "register"

    def __str__(self):
        return "r{}".format(self.value)


class SFRToken(Token):
    terminal = "sfr"
