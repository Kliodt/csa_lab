import json
import logging
import sys

from components.control_unit import ControlUnit
from components.data_path import DataPath
from components.io import IOController, IO1
from components.memory import Memory
from components.stacks import DataStack, CallStack
from isa import Opcode


def simulation(
    program: list, input_buffer: list, data_memory_size: int, call_stack_size: int
) -> tuple[list, int, int]:
    io_controller = IOController()
    io_1 = IO1(input_buffer)
    io_controller.add_io(io_1, 0)

    data_path = DataPath(DataStack(100), Memory(data_memory_size), io_controller)

    control_unit = ControlUnit(program, CallStack(call_stack_size), data_path)

    try:
        logging.debug("%s", control_unit)
        while True:
            control_unit.decode_and_execute_instruction()
            logging.debug("%s", control_unit)
    except EOFError:
        logging.warning("Пустой буфер ввода!")
    except StopIteration:
        pass
    program_counter = control_unit.program_counter
    tick_counter = control_unit.tick_counter
    output = io_1.get_received_data()
    return output, program_counter, tick_counter


def main(code_file: str, input_file: str):
    with open(input_file, encoding="utf-8") as inp:
        input_text = inp.read()
        input_buffer = []
        for char in input_text:
            input_buffer.append(char)
        input_buffer.append("\0")

    with open(code_file, encoding="utf-8") as cf:
        code = json.loads(cf.read())

    for instr in code:
        # Конвертация строки в Opcode
        instr["opcode"] = Opcode(instr["opcode"])

    output, pc, tc = simulation(code, input_buffer, 1000, 30)
    print(f"program counter: {pc}, ticks: {tc}.")
    print("Вывод:")
    print("".join(output))


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert (
        len(sys.argv) == 3
    ), "Неверное число аргументов. Использование: machine.py <code_file> <input_file>"
    _, code_file, input_file = sys.argv
    main(code_file, input_file)
