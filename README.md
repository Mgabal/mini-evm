# mini-evm

A minimal Ethereum Virtual Machine implementation in Python, built to understand EVM internals at the opcode level.

## What This Is

This is not a tutorial project. It is a ground-up implementation of the EVM execution engine covering the core opcode set, built to deeply understand how Ethereum processes transactions at the bytecode level.

## Architecture

The EVM is a stack-based virtual machine. Every operation reads from and writes to a 256-bit wide stack. There are no registers.

Transaction Bytecode

↓

Program Counter (pc)

↓

Opcode Dispatcher


## Opcodes Implemented

| Opcode | Hex | Description |
|--------|-----|-------------|
| STOP | 0x00 | Halt execution |
| ADD | 0x01 | 256-bit addition with overflow wrapping |
| MUL | 0x02 | 256-bit multiplication |
| SUB | 0x03 | 256-bit subtraction |
| MLOAD | 0x51 | Load 32 bytes from memory |
| MSTORE | 0x52 | Store 32 bytes to memory |
| SLOAD | 0x54 | Load from persistent storage |
| SSTORE | 0x55 | Write to persistent storage |
| JUMP | 0x56 | Unconditional jump to JUMPDEST |
| JUMPI | 0x57 | Conditional jump |
| JUMPDEST | 0x5B | Valid jump destination marker |
| PUSH1 | 0x60 | Push 1 byte onto stack |
| POP | 0x50 | Remove top stack item |
| ISZERO | 0x15 | 1 if top of stack is zero, else 0 |

## Key Design Decisions

**256-bit arithmetic overflow wrapping**
All arithmetic operations wrap at 2^256 using bitwise AND masking. This is how the real EVM handles overflow — and why integer overflow vulnerabilities existed before Solidity 0.8 added built-in checks.

**JUMPDEST validation**
JUMP and JUMPI both validate that the destination byte is a JUMPDEST (0x5B) opcode. Jumping to an arbitrary offset is invalid and reverts. This prevents attackers from jumping into the middle of PUSH data to execute arbitrary opcodes — a real attack vector.

**Memory vs Storage**
- Memory (`bytearray`) is temporary — allocated per execution, gone when execution ends
- Storage (`dict`) is persistent — survives across transactions, maps to the Ethereum state trie
- This is why SSTORE costs 20,000 gas for a new slot vs MSTORE costing 3 gas

## Running Tests

```bash
python3 -m venv venv
source venv/bin/activate
pip install pytest
pytest test_evm.py -v
```

## What I Learned

Building this exposed the exact mechanism behind several vulnerability classes:

- **Integer overflow** — before Solidity 0.8, unchecked arithmetic silently wrapped. I implemented this wrapping myself.
- **Invalid jump destinations** — without JUMPDEST validation, an attacker could redirect execution flow into arbitrary bytecode positions
- **Stack ordering bugs** — JUMPI operand order confusion is the same class of error that causes real arithmetic vulnerabilities in assembly/Yul code

## Next Steps

- [ ] Add CALLER, ORIGIN, CALLVALUE context opcodes
- [ ] Implement CALL and DELEGATECALL to demonstrate proxy vulnerability mechanics
- [ ] Add gas metering
- [ ] Implement REVERT with return data

## Resources

- [evm.codes](https://evm.codes) — opcode reference
- [Ethereum Yellow Paper](https://ethereum.github.io/yellowpaper/paper.pdf)
- [noxx EVM deep dive series](https://noxx.substack.com)
