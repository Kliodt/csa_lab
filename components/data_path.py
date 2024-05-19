from components.alu import alu
from components.io import IOController
from components.memory import Memory
from components.stacks import DataStack
from isa import Opcode

import logging


class DataPath:
    def __init__(self, stack: DataStack, memory: Memory, io_controller: IOController):
        self.stack = stack
        self.memory = memory
        self.io_controller = io_controller
        self.data_addr = 0
        self.zero_flag = False
        self.negative_flag = False

    def latch_tos(self, instr):
        opcode = instr["opcode"]
        if opcode == Opcode.LOAD:
            self.stack.push(self.memory.signal_read(self.data_addr))
        elif opcode == Opcode.STORE:
            pass #не сюда, в CU

        elif opcode in {Opcode.ADD, Opcode.SUB, Opcode.MUL, Opcode.DIV, Opcode.MOD, Opcode.AND, Opcode.OR}:
            self.stack.push(alu(opcode, self.stack.pop(), self.stack.pop()))
        elif opcode in {Opcode.INC, Opcode.DEC, Opcode.NOT, Opcode.NEG}:
            self.stack.push(alu(opcode, self.stack.pop(), 0))

        elif opcode == Opcode.READ:
            symbol = self.io_controller.signal_read()
            self.stack.push(symbol)
            logging.debug("ввод: %s", chr(symbol))
        elif opcode == Opcode.WRITE:
            pass #не сюда, в CU

        elif opcode == Opcode.PUSH:
            self.stack.push(instr["arg"])
        elif opcode == Opcode.POP:
            pass #не сюда, в CU


    def latch_data_addr(self):
        self.data_addr = self.stack.pop()

    def signal_store(self):
        self.stack.pop()
        self.memory.signal_write(self.data_addr, self.stack.top())

    def signal_write(self):
        self.io_controller.signal_write(self.stack.pop())

    def signal_set_flags(self):
        self.zero_flag = self.stack.top() == 0
        self.negative_flag = self.stack.top() < 0
