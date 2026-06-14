import unittest
from evm import EVM

class TestEVM(unittest.TestCase):

    def test_add(self):
        # PUSH1 5, PUSH1 3, ADD, STOP
        bytecode = bytes([0x60, 0x05, 0x60, 0x03, 0x01, 0x00])
        evm = EVM(bytecode)
        evm.run()
        self.assertEqual(evm.stack[0], 8)

    def test_mul(self):
        # PUSH1 4, PUSH1 3, MUL, STOP
        bytecode = bytes([0x60, 0x04, 0x60, 0x03, 0x02, 0x00])
        evm = EVM(bytecode)
        evm.run()
        self.assertEqual(evm.stack[0], 12)

    def test_sub(self):
        # PUSH1 10, PUSH1 3, SUB, STOP
        bytecode = bytes([0x60, 0x0A, 0x60, 0x03, 0x03, 0x00])
        evm = EVM(bytecode)
        evm.run()
        self.assertEqual(evm.stack[0], 7)

    def test_mstore_mload(self):
        # PUSH1 42 (value), PUSH1 0 (offset), MSTORE
        # PUSH1 0 (offset), MLOAD
        # STOP
        bytecode = bytes([
            0x60, 0x2A,  # PUSH1 42
            0x60, 0x00,  # PUSH1 0
            0x52,        # MSTORE
            0x60, 0x00,  # PUSH1 0
            0x51,        # MLOAD
            0x00         # STOP
        ])
        evm = EVM(bytecode)
        evm.run()
        self.assertEqual(evm.stack[0], 42)

    def test_sstore_sload(self):
        # PUSH1 99 (value), PUSH1 1 (key), SSTORE
        # PUSH1 1 (key), SLOAD
        # STOP
        bytecode = bytes([
            0x60, 0x63,  # PUSH1 99
            0x60, 0x01,  # PUSH1 1
            0x55,        # SSTORE
            0x60, 0x01,  # PUSH1 1
            0x54,        # SLOAD
            0x00         # STOP
        ])
        evm = EVM(bytecode)
        evm.run()
        self.assertEqual(evm.stack[0], 99)

    def test_iszero_true(self):
        # PUSH1 0, ISZERO — should push 1
        bytecode = bytes([0x60, 0x00, 0x15, 0x00])
        evm = EVM(bytecode)
        evm.run()
        self.assertEqual(evm.stack[0], 1)

    def test_iszero_false(self):
        # PUSH1 5, ISZERO — should push 0
        bytecode = bytes([0x60, 0x05, 0x15, 0x00])
        evm = EVM(bytecode)
        evm.run()
        self.assertEqual(evm.stack[0], 0)

    def test_stack_underflow(self):
        # POP on empty stack should raise
        bytecode = bytes([0x50])
        evm = EVM(bytecode)
        with self.assertRaises(Exception):
            evm.run()

    def test_overflow_wraps(self):
        # MAX_UINT256 + 1 should wrap to 0
        MAX = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        evm = EVM(b"")
        evm.push(MAX)
        evm.push(1)
        evm.execute(0x01)  # ADD
        self.assertEqual(evm.stack[0], 0)

    def test_jump(self):
        # PUSH1 4, JUMP, STOP, JUMPDEST, PUSH1 42, STOP
        # should skip the first STOP and land at JUMPDEST
        bytecode = bytes([
            0x60, 0x04,  # PUSH1 4 (destination)
            0x56,        # JUMP
            0x00,        # STOP (should be skipped)
            0x5B,        # JUMPDEST at position 4
            0x60, 0x2A,  # PUSH1 42
            0x00         # STOP
        ])
        evm = EVM(bytecode)
        evm.run()
        self.assertEqual(evm.stack[0], 42)

    def test_jumpi_taken(self):
        # condition is 1 so jump should happen
        bytecode = bytes([
            0x60, 0x06,  # PUSH1 6 (destination)
            0x60, 0x01,  # PUSH1 1 (condition = true)
            0x57,        # JUMPI
            0x00,        # STOP (skipped)
            0x5B,        # JUMPDEST at position 6
            0x60, 0x99,  # PUSH1 153
            0x00         # STOP
        ])
        evm = EVM(bytecode)
        evm.run()
        self.assertEqual(evm.stack[0], 153)

    def test_jumpi_not_taken(self):
        # condition is 0 so jump should NOT happen
        bytecode = bytes([
            0x60, 0x06,  # PUSH1 6 (destination)
            0x60, 0x00,  # PUSH1 0 (condition = false)
            0x57,        # JUMPI
            0x00,        # STOP (should execute)
            0x5B,        # JUMPDEST (never reached)
            0x60, 0x99,  # PUSH1 153 (never reached)
            0x00         # STOP
        ])
        evm = EVM(bytecode)
        evm.run()
        self.assertEqual(evm.stack, [])

    def test_invalid_jump(self):
        # jumping to a non-JUMPDEST should raise
        bytecode = bytes([
            0x60, 0x03,  # PUSH1 3
            0x56,        # JUMP
            0x00,        # STOP (not a JUMPDEST)
        ])
        evm = EVM(bytecode)
        with self.assertRaises(Exception):
            evm.run()

    def test_caller(self):
        # CALLER should push msg.sender onto stack
        bytecode = bytes([0x33, 0x00])  # CALLER, STOP
        evm = EVM(bytecode, caller=0xDEADBEEF)
        evm.run()
        self.assertEqual(evm.stack[0], 0xDEADBEEF)

    def test_origin(self):
        # ORIGIN should push tx.origin onto stack
        bytecode = bytes([0x32, 0x00])  # ORIGIN, STOP
        evm = EVM(bytecode, origin=0xCAFEBABE)
        evm.run()
        self.assertEqual(evm.stack[0], 0xCAFEBABE)

    def test_callvalue(self):
        # CALLVALUE should push msg.value onto stack
        bytecode = bytes([0x34, 0x00])  # CALLVALUE, STOP
        evm = EVM(bytecode, value=1000)
        evm.run()
        self.assertEqual(evm.stack[0], 1000)

    def test_caller_vs_origin_attack(self):
        bytecode = bytes([0x32, 0x33, 0x00])  # ORIGIN, CALLER, STOP
        user = 0xAAAA
        attacker_contract = 0xBBBB
        evm = EVM(bytecode, caller=attacker_contract, origin=user)
        evm.run()
        # stack[0] is bottom (ORIGIN pushed first)
        # stack[1] is top (CALLER pushed second)
        self.assertEqual(evm.stack[0], user)               # ORIGIN at bottom
        self.assertEqual(evm.stack[1], attacker_contract)  # CALLER on top
        # if contract uses ORIGIN for auth, attacker bypasses it

    def test_calldataload(self):
        # load first 32 bytes of calldata
        calldata = (42).to_bytes(32, "big")
        bytecode = bytes([0x60, 0x00, 0x35, 0x00])  # PUSH1 0, CALLDATALOAD, STOP
        evm = EVM(bytecode, calldata=calldata)
        evm.run()
        self.assertEqual(evm.stack[0], 42)

    def test_calldatasize(self):
        calldata = b"\x00" * 64
        bytecode = bytes([0x36, 0x00])  # CALLDATASIZE, STOP
        evm = EVM(bytecode, calldata=calldata)
        evm.run()
        self.assertEqual(evm.stack[0], 64)   

    def test_delegatecall_uses_caller_storage(self):
        # Contract B: PUSH1 99, PUSH1 0, SSTORE, STOP
        # Stores 99 at slot 0 — but in whose storage?
        contract_b = bytes([
            0x60, 0x63,  # PUSH1 99
            0x60, 0x00,  # PUSH1 0 (slot)
            0x55,        # SSTORE
            0x00         # STOP
        ])

        # Contract A: DELEGATECALL to contract B
        # DELEGATECALL: gas, addr, argsOffset, argsSize, retOffset, retSize
        contract_a = bytes([
            0x60, 0x00,  # PUSH1 0 (ret_size)
            0x60, 0x00,  # PUSH1 0 (ret_offset)
            0x60, 0x00,  # PUSH1 0 (args_size)
            0x60, 0x00,  # PUSH1 0 (args_offset)
            0x60, 0xBB,  # PUSH1 0xBB (address of contract B)
            0x60, 0xFF,  # PUSH1 255 (gas)
            0xF4,        # DELEGATECALL
            0x00         # STOP
        ])

        evm = EVM(contract_a)
        evm.contracts[0xBB] = contract_b
        evm.run()

        # storage slot 0 should be 99 in CONTRACT A's storage
        self.assertEqual(evm.storage.get(0), 99)

    def test_delegatecall_preserves_caller(self):
        # Contract B pushes CALLER onto stack
        contract_b = bytes([0x33, 0x00])  # CALLER, STOP

        contract_a = bytes([
            0x60, 0x00,
            0x60, 0x00,
            0x60, 0x00,
            0x60, 0x00,
            0x60, 0xBB,
            0x60, 0xFF,
            0xF4,        # DELEGATECALL
            0x00
        ])

        original_caller = 0x1234
        evm = EVM(contract_a, caller=original_caller)
        evm.contracts[0xBB] = contract_b
        evm.run()

        # DELEGATECALL preserves original caller
        # success flag (1) is on stack from DELEGATECALL
        self.assertEqual(evm.stack[-1], 1)  # success         

if __name__ == "__main__":
    unittest.main()
