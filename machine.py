import json

from components.control_unit import ControlUnit
from components.data_path import DataPath
from components.io import IOController, IO1
from components.memory import Memory
from components.stacks import DataStack, CallStack
from isa import Opcode


def simulation(program: list, input_buffer: list, data_memory_size: int, call_stack_size: int):

    io_controller = IOController()
    io_1 = IO1(input_buffer)
    io_controller.add_io(io_1, 0)

    data_path = DataPath(DataStack(100), Memory(data_memory_size), io_controller)

    control_unit = ControlUnit(program, CallStack(call_stack_size), data_path)

    # instr_counter = 0

    # logging.debug("%s", control_unit)
    try:
        while True:
            print(control_unit)
            control_unit.decode_and_execute_instruction()

    except StopIteration:
        pass

    output = io_1.get_received_data()
    return output


def main(code_file, input_file):
    """Функция запуска модели процессора. Параметры -- имена файлов с машинным
    кодом и с входными данными для симуляции.
    """
    code_file = "machine_code.json"
    with open(code_file, encoding="utf-8") as cf:
        code = json.loads(cf.read())
    for instr in code:
        # Конвертация строки в Opcode
        instr["opcode"] = Opcode(instr["opcode"])
    output = simulation(code, ["h", "e", "l", "l", "o", "\0", "w", "o", "r", "l", "d", "\0"], 1000, 30)
    print("-" * 100)
    print("Simulation output:")
    print("".join(output))

if __name__ == "__main__":
    main("","")