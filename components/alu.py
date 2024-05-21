from isa import Opcode

def alu(op: Opcode, right: int, left: int) -> int:
    if op == Opcode.ADD:
        return left + right
    elif op == Opcode.SUB:
        return left - right
    elif op == Opcode.MUL:
        return left * right
    elif op == Opcode.DIV:
        return left // right
    elif op == Opcode.MOD:
        return left % right
    elif op == Opcode.INC:
        return right + 1
    elif op == Opcode.DEC:
        return right - 1
    elif op == Opcode.AND:
        return left and right
    elif op == Opcode.OR:
        return left or right
    elif op == Opcode.NOT:
        return int(not right)
    elif op == Opcode.NEG:
        return -right


