from enum import Enum

class Opcode(str, Enum):

    PUSH = "push"
    POP = "pop"

    LOAD = "load"
    STORE = "store"

    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    MOD = "mod"

    DEC = "dec"
    INC = "inc"
    NEG = "neg"

    AND = "and"
    OR = "or"
    NOT = "not"

    SWAP = "swap"
    DUP = "dup"

    FLAGS = "flags"

    JUMP = "jump"
    JZ = "jump_zero"
    JNZ = "jump_non_zero"
    JP = "jump_plus"
    JM = "jump_minus"

    READ = "read"
    WRITE = "write"

    CALL = "call"
    RET = "ret"

    HALT = "halt"

    def __str__(self):
        """Переопределение стандартного поведения `__str__` для `Enum`: вместо
        `Opcode.INC` вернуть `increment`.
        """
        return str(self.value)