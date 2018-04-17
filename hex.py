

class IntelHexParser:
    def __init__(self, hex_bytes):
        self.chars = map(chr, hex_bytes)

    def next_record(self):
        self.assume(self.next_char() is ':')
        byte_count = self.next_byte()
        address = self.next_byte(2)
        record_type = self.next_byte()
        data = self.next_bytelist(byte_count)
        return (byte_count, address, data)

    @staticmethod
    def assume(condition):
        if not condition:
            raise Exception

    def next_char(self, count=1):
        return ''.join(next(self.chars) for _ in range(count))

    def next_byte(self, count=1):
        return int(self.next_char(count), 16)

    def next_bytelist(self, count):
        return list(reversed([self.next_byte() for _ in range(count)]))


parser = IntelHexParser(b':02000B002100')
# record = parser.next_record()

print(parser.next_char(3))
