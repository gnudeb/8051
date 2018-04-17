
class Token:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class OpcodeToken(Token):
    pass


class Addr11Token(Token):
    pass


class Addr16Token(Token):
    pass


class EndOfInstrToken(Token):
    def __init__(self):
        super().__init__("\n")


class RegisterToken(Token):
    def __str__(self):
        return "r{}".format(self.value)
