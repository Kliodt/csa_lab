
from components.data_path import DataPath
from components.stacks import CallStack
from isa import Opcode

import logging

class ControlUnit:

    def __init__(self, program: list, call_stack: CallStack, data_path: DataPath):
        self.program = program
        self.program_counter = 0
        self.call_stack = call_stack
        self.tick_counter = 0
        self.data_path = data_path

    def tick(self):
        self.tick_counter += 1

    def signal_latch_program_counter(self, sel_next: Opcode, arg=None):
        if sel_next == Opcode.JUMP:
            self.program_counter += 1 + arg

        elif sel_next == Opcode.JZ and self.data_path.zero_flag:
            self.program_counter += 1 + arg

        elif sel_next == Opcode.JNZ and not self.data_path.zero_flag:
            self.program_counter += 1 + arg

        elif sel_next == Opcode.JP and not self.data_path.negative_flag:
            self.program_counter += 1 + arg

        elif sel_next == Opcode.JM and self.data_path.negative_flag:
            self.program_counter += 1 + arg

        elif sel_next == Opcode.CALL:
            self.call_stack.push(self.program_counter+1)
            self.program_counter = arg

        elif sel_next == Opcode.RET:
            self.program_counter = self.call_stack.pop()

        else:
            self.program_counter += 1

    # если True, то сразу перейти к следующему такту
    def decode_and_execute_control_flow_instruction(self, instr) -> bool:
        opcode = instr["opcode"]
        if opcode == Opcode.HALT:
            raise StopIteration()

        elif opcode in {Opcode.JUMP, Opcode.JNZ, Opcode.JZ, Opcode.JP, Opcode.JM,
                        Opcode.CALL, Opcode.RET}:
            self.signal_latch_program_counter(opcode, instr["arg"])
            self.tick()
            return True

        return False

    def decode_and_execute_instruction(self):
        instr = self.program[self.program_counter]
        opcode = instr["opcode"]

        if self.decode_and_execute_control_flow_instruction(instr):
            return

        if opcode in {Opcode.LOAD, Opcode.STORE}:
            self.data_path.latch_data_addr()
            self.tick()

        if opcode == Opcode.STORE:
            self.data_path.memory.signal_write(self.data_path.data_addr, self.data_path.stack.top())
            self.signal_latch_program_counter(opcode)
            self.tick()

        elif opcode == Opcode.WRITE:
            symbol = self.data_path.stack.pop()
            self.data_path.io_controller.signal_write(symbol)
            self.signal_latch_program_counter(opcode)
            logging.debug("вывод: %s", chr(symbol) if symbol != 0 else "\\0") # fix for golden test parser
            self.tick()

        elif opcode == Opcode.POP:
            self.data_path.stack.pop()
            self.signal_latch_program_counter(opcode)
            self.tick()

        elif opcode == Opcode.FLAGS:
            self.data_path.signal_set_flags()
            self.signal_latch_program_counter(opcode)
            self.tick()

        elif opcode == Opcode.DUP:
            self.data_path.stack.dup()
            self.signal_latch_program_counter(opcode)
            self.tick()

        elif opcode == Opcode.SWAP:
            self.data_path.stack.swap()
            self.signal_latch_program_counter(opcode)
            self.tick()

        else:
            self.data_path.latch_tos(instr)
            self.signal_latch_program_counter(opcode)
            self.tick()


    def __repr__(self):
        state_repr = "TICK: {:3},  PC: {:3},  AR: {:3},  MEM_OUT: {:3},  TOS: {:22},".format(
            self.tick_counter,
            self.program_counter,
            self.data_path.data_addr,
            self.data_path.memory.memory[self.data_path.data_addr],
            str(self.data_path.stack),
        )

        instr = self.program[self.program_counter]

        instr_repr = instr["opcode"]
        instr_repr += " {}".format(instr["arg"]) if instr["arg"] is not None else ""
        instr_term = " // {}".format(instr["term"]) if instr["term"] is not None else ""

        return "{}    {:10}{}".format(state_repr, instr_repr, instr_term)
