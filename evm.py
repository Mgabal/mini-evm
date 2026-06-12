class EVM:
    def __init__(self, bytecode: bytes, calldata: bytes = b""):
        self.bytecode = bytecode
        self.calldata = calldata
        self.stack = []
        self.memory = bytearray()
        self.storage = {}
        self.pc = 0  # program counter
        self.stopped = False

    def push(self, value: int):
        self.stack.append(value)

    def pop(self) -> int:
        if not self.stack:
            raise Exception("Stack underflow")
        return self.stack.pop()

    def run(self):
        while not self.stopped and self.pc < len(self.bytecode):
            opcode = self.bytecode[self.pc]
            self.pc += 1
            self.execute(opcode)

    def execute(self, opcode: int):

        # STOP
        if opcode == 0x00:
            self.stopped = True

        # ADD
        elif opcode == 0x01:
            a = self.pop()
            b = self.pop()
            self.push((a + b) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

        # MUL
        elif opcode == 0x02:
            a = self.pop()
            b = self.pop()
            self.push((a * b) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

        # SUB
        elif opcode == 0x03:
            a = self.pop()
            b = self.pop()
            self.push((b - a) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        
        # PUSH1
        elif opcode == 0x60:
            value = self.bytecode[self.pc]
            self.pc += 1
            self.push(value)

        # POP
        elif opcode == 0x50:
            self.pop()

        # MSTORE
        elif opcode == 0x52:
            offset = self.pop()
            value = self.pop()
            # expand memory if needed
            if offset + 32 > len(self.memory):
                self.memory.extend(b"\x00" * (offset + 32 - len(self.memory)))
            self.memory[offset:offset + 32] = value.to_bytes(32, "big")

        # MLOAD
        elif opcode == 0x51:
            offset = self.pop()
            if offset + 32 > len(self.memory):
                self.memory.extend(b"\x00" * (offset + 32 - len(self.memory)))
            value = int.from_bytes(self.memory[offset:offset + 32], "big")
            self.push(value)

        # SSTORE
        elif opcode == 0x55:
            key = self.pop()
            value = self.pop()
            self.storage[key] = value

        # SLOAD
        elif opcode == 0x54:
            key = self.pop()
            self.push(self.storage.get(key, 0))

        # ISZERO
        elif opcode == 0x15:
            a = self.pop()
            self.push(1 if a == 0 else 0)

        # JUMP
        elif opcode == 0x56:
            dest = self.pop()
            if dest >= len(self.bytecode) or self.bytecode[dest] != 0x5B:
                raise Exception(f"Invalid JUMP destination: {dest}")
            self.pc = dest

        # JUMPI (conditional jump)
        elif opcode == 0x57:
            condition = self.pop()
            dest = self.pop()
            if condition != 0:
                if dest >= len(self.bytecode) or self.bytecode[dest] != 0x5B:
                    raise Exception(f"Invalid JUMPI destination: {dest}")
                self.pc = dest

        # JUMPDEST
        elif opcode == 0x5B:
            pass  # just marks a valid jump destination, does nothing itself    

        else:
            raise Exception(f"Unknown opcode: {hex(opcode)} at pc={self.pc - 1}")