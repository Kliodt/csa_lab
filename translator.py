import re
import sys

from isa import Opcode
import json


class Expression:
    # нужен для представления строковой программы в виде дерева объектов этого класса
    # и последующего преобразовании его в машинный код
    def __init__(self, name: str, args: list):
        self.name = name
        self.arguments = args

    def str(self):
        return f"Command: {self.name}, args: {[str(a) for a in self.arguments]};"


class Instr:
    def __init__(self, opcode: Opcode, arg=None, term=None):
        self.opcode = opcode
        self.arg = arg
        self.term = term

    def __str__(self):
        return (
            str(self.opcode.name)
            + " "
            + (str(self.arg) if self.arg is not None else "")
        )

    def to_dict(self):
        return {
            "opcode": self.opcode,
            "arg": self.arg,
            "term": self.term,
        }


def parse_string(text: str) -> tuple[Expression, list[str], int]:
    """Парсит программу, представленную в текстовом виде.
    Возвращает массив вложенных выражений
    """
    # заменить все строковые литералы
    is_str = False
    str_literals = []
    curr_literal = ""
    for char in text:
        if not is_str and char == '"':
            is_str = True
            continue
        if is_str and char == '"':
            is_str = False
            str_literals.append(curr_literal)
            curr_literal = ""
            continue
        if is_str:
            curr_literal += char

    for i in range(len(str_literals)):
        text = text.replace(f'"{str_literals[i]}"', f'"STR[{i}]')

    # парсинг происходит по одинарному пробелу, поэтому надо убрать лишние и добавить недостающие пробелы
    text = text.replace(")(", ") (").strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)

    dynamic_strings_count = text.count("(read_str")

    def parse_expression(line: str) -> Expression:
        assert line[0] == "(" and line[-1] == ")", ""
        tokens = []
        current_token = ""
        stack = 0

        for char in line[1:-1]:
            if char == "(":
                stack += 1
            elif char == ")":
                stack -= 1
            assert stack >= 0, "Несбалансированные скобочки"

            if char == " " and stack == 0:
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
            else:
                current_token += char

        if current_token:
            tokens.append(current_token)

        assert stack == 0, "Несбалансированные скобочки"

        args = []
        for token in tokens[1:]:
            if token[0] == "(":
                # аргумент - вложенная функция
                args.append(parse_expression(token))
            else:
                # аргумент - строка/число
                args.append(token)
        return Expression(tokens[0], args)

    return parse_expression(text), str_literals, dynamic_strings_count


instructions: dict
variables: dict
functions: dict
str_literals_addresses: list
next_var_addr: int
def_port = 0  # default i/o port
dynamic_string_max_length = 40  # default


def defun_process(func_vars: list, body: list) -> list[Instr]:
    # returns function name and list of instructions
    global variables, next_var_addr
    code = []
    func_vars.reverse()

    for var_name in func_vars:
        assert (
            var_name not in variables
        ), f"Двойное объявление переменной запрещено: {var_name}"
        assert re.match(
            r"^[a-zA-Z][-_a-zA-Z0-9]*", var_name
        ), f"Запрещенное имя переменной: {var_name}"
        variables.update({var_name: next_var_addr})
        # load variable from stack
        code.extend(
            [
                Instr(Opcode.PUSH, arg=next_var_addr, term="call"),
                Instr(Opcode.STORE, term="call"),
                Instr(Opcode.POP, term="call"),
            ]
        )
        next_var_addr += 1
    code.extend(to_machine_code(Expression('"FUNC', body)))
    code.append(Instr(Opcode.RET, term="ret"))
    return code


def to_machine_code(exp: Expression) -> list[Instr]:
    global next_var_addr, str_literals_addresses
    # 1 вызвать для каждого аргумента
    arg_code: list[list] = []

    for i in range(len(exp.arguments)):
        arg = exp.arguments[i]

        # выражения раскрываем рекурсивно
        if isinstance(arg, Expression):
            assert not (
                i == 0 and (exp.name == "defvar" or exp.name == "setq")
            ), "Недопустимое выражение для переменной"
            arg_code.append(to_machine_code(arg))

        # числовые литералы пушим в стек
        elif re.match(r"^-?[0-9]+$", arg):
            arg_code.append(
                [Instr(Opcode.PUSH, arg=int(arg), term=f"(number literal: {arg})")]
            )

        # статическая строка заменяется на ее адрес в памяти
        elif '"STR' in arg:
            str_num = int(arg.replace('"STR[', "").replace("]", ""))
            str_addr = str_literals_addresses[str_num]
            # в стеке должен оказаться указатель на строку
            arg_code.append([Instr(Opcode.PUSH, arg=str_addr, term="(static string)")])

        # отдельный случай для новых переменных
        elif exp.name == "defvar" and i == 0:
            assert (
                arg not in variables
            ), f"Двойное объявление переменной запрещено: {arg}"
            assert re.match(
                r"^[a-zA-Z][-_a-zA-Z0-9]*", arg
            ), f"Запрещенное имя переменной: {arg}"
            variables.update({arg: next_var_addr})
            arg_code.append([Instr(Opcode.PUSH, arg=next_var_addr, term="defvar")])
            next_var_addr += 1

        # отдельный случай для объявления функций
        elif exp.name == "defun" and i == 0:
            assert (
                0
            ), "Объявление функции разрешено только на верхнем уровне вложенности"

        # переменные загружаем из памяти
        elif arg in variables:
            var_addr = variables.get(arg)
            if exp.name == "setq" and i == 0:  # исключение - 1-й арг. команды setq
                arg_code.append([Instr(Opcode.PUSH, arg=var_addr, term="setq")])

            else:
                arg_code.append(
                    [
                        Instr(Opcode.PUSH, arg=var_addr, term=f"(variable: {arg})"),
                        Instr(Opcode.LOAD, term=f"(variable: {arg})"),
                    ]
                )

        else:
            assert 0, f"Нераспознанный аргумент: {arg}"

    # 2 вызвать для выражения
    if exp.name in instructions:
        instr_code = instructions.get(exp.name)(arg_code)
        return instr_code
    if exp.name in functions:
        instr_code = []
        for ac in arg_code:
            instr_code.extend(ac)
        instr_code.extend(
            [
                Instr(
                    Opcode.CALL,
                    arg=1 + functions.get(exp.name),
                    term=f"call {exp.name}",
                )
            ]
        )
        return instr_code

    assert 0, f"Нераспознанная инструкция: {exp.name}"


def defvar(args_codes: list[list]) -> list[Instr]:
    term = "defvar"
    assert 1 <= len(args_codes) <= 2, "Недопустимое число аргументов для функции defvar"
    code = []

    if len(args_codes) == 1:
        code.append(Instr(Opcode.PUSH, arg=0, term=term))
        code.extend(args_codes[0])
        code.append(Instr(Opcode.STORE, term=term))
    else:
        code.extend(args_codes[1])
        code.extend((args_codes[0]))
        code.append(Instr(Opcode.STORE, term=term))

    return code


def setq(args_codes: list[list]) -> list[Instr]:
    term = "setq"
    assert len(args_codes) == 2, "Недопустимое число аргументов для setq"
    code = []
    code.extend(args_codes[1])
    code.extend((args_codes[0]))
    code.append(Instr(Opcode.STORE, term=term))

    return code


def add(args_codes: list[list]) -> list[Instr]:
    term = "+"
    code = []
    if len(args_codes) == 0:
        code.append(Instr(Opcode.PUSH, 0, term=term))
    else:
        code.extend(args_codes[0])
        for c in args_codes[1:]:
            code.extend(c)
            code.append(Instr(Opcode.ADD, term=term))

    return code


def sub(args_codes: list[list]) -> list[Instr]:
    term = "-"
    assert len(args_codes) > 0, "Недопустимое число аргументов для sub"
    code = []
    if len(args_codes) == 1:
        code.append(Instr(Opcode.PUSH, 0, term=term))
        code.extend(args_codes[0])
        code.append(Instr(Opcode.SUB, term=term))
    else:
        code.extend(args_codes[0])
        for c in args_codes[1:]:
            code.extend(c)
            code.append(Instr(Opcode.SUB, term=term))

    return code


def mul(args_codes: list[list]) -> list[Instr]:
    term = "*"
    code = []
    if len(args_codes) == 0:
        code.append(Instr(Opcode.PUSH, 1, term=term))

    else:
        code.extend(args_codes[0])
        for c in args_codes[1:]:
            code.extend(c)
            code.append(Instr(Opcode.MUL, term=term))

    return code


def div(args_codes: list[list]) -> list[Instr]:
    term = "/"
    assert len(args_codes) > 0, "Недопустимое число аргументов для div"
    code = []
    if len(args_codes) == 1:
        code.append(Instr(Opcode.PUSH, arg=1, term=term))
        code.extend(args_codes[0])
        code.append(Instr(Opcode.DIV, term=term))
    else:
        for c in args_codes:
            code.extend(c)
        for _ in range(len(args_codes) - 1):
            code.append(Instr(Opcode.DIV, term=term))

    return code


def mod(args_codes: list[list]) -> list[Instr]:
    term = "%"
    assert len(args_codes) == 2, "Недопустимое число аргументов для mod"
    code = []
    code.extend(args_codes[0])
    code.extend(args_codes[1])
    code.append(Instr(Opcode.MOD, term=term))

    return code


def and_(args_codes: list[list]) -> list[Instr]:
    term = "and"
    assert len(args_codes) > 0, "Недопустимое число аргументов для and"
    code = []
    code.extend(args_codes[0])
    for c in args_codes[1:]:
        code.extend(c)
        code.append(Instr(Opcode.AND, term=term))

    return code


def or_(args_codes: list[list]) -> list[Instr]:
    term = "or"
    assert len(args_codes) > 0, "Недопустимое число аргументов для or"
    code = []
    code.extend(args_codes[0])
    for c in args_codes[1:]:
        code.extend(c)
        code.append(Instr(Opcode.OR, term=term))

    return code


def not_(args_codes: list[list]) -> list[Instr]:
    term = "not"
    assert len(args_codes) == 1, "Недопустимое число аргументов для not"
    code = []
    code.extend(args_codes[0])
    code.append(Instr(Opcode.NOT, term=term))

    return code


def eq(args_codes: list[list]) -> list[Instr]:
    term = "="
    assert 2 >= len(args_codes) >= 1, "Недопустимое число аргументов для eq"
    code = []
    if len(args_codes) == 1:
        code.extend(
            [Instr(Opcode.POP, term=term), Instr(Opcode.PUSH, arg=1, term=term)]
        )
    else:
        code.extend(args_codes[0])
        code.extend(args_codes[1])
        code.extend(
            [
                Instr(Opcode.SUB, term=term),
                Instr(Opcode.FLAGS, term=term),
                Instr(Opcode.POP, term=term),
                Instr(Opcode.JZ, arg=2, term=term),  # jump if eq
                Instr(Opcode.PUSH, arg=0, term=term),
                Instr(Opcode.JUMP, arg=1, term=term),
                Instr(Opcode.PUSH, arg=1, term=term),  # to here
            ]
        )

    return code


def larger(args_codes: list[list]) -> list[Instr]:
    term = ">"
    assert 2 >= len(args_codes) >= 1, "Недопустимое число аргументов для larger"
    code = []
    if len(args_codes) == 1:
        code.extend(
            [Instr(Opcode.POP, term=term), Instr(Opcode.PUSH, arg=1, term=term)]
        )
    else:
        code.extend(args_codes[0])
        code.extend(args_codes[1])
        code.extend(
            [
                Instr(Opcode.SWAP),
                Instr(Opcode.SUB, term=term),
                Instr(Opcode.FLAGS, term=term),
                Instr(Opcode.POP, term=term),
                Instr(Opcode.JM, arg=2, term=term),  # jump if lower
                Instr(Opcode.PUSH, arg=0, term=term),
                Instr(Opcode.JUMP, arg=1, term=term),
                Instr(Opcode.PUSH, arg=1, term=term),  # to here
            ]
        )

    return code


def lower(args_codes: list[list]) -> list[Instr]:
    term = "<"
    assert 2 >= len(args_codes) >= 1, "Недопустимое число аргументов для lower"
    code = []
    if len(args_codes) == 1:
        code.extend(
            [Instr(Opcode.POP, term=term), Instr(Opcode.PUSH, arg=1, term=term)]
        )
    else:
        code.extend(args_codes[0])
        code.extend(args_codes[1])
        code.extend(
            [
                Instr(Opcode.SUB, term=term),
                Instr(Opcode.FLAGS, term=term),
                Instr(Opcode.POP, term=term),
                Instr(Opcode.JM, arg=2, term=term),  # jump if lower
                Instr(Opcode.PUSH, arg=0, term=term),
                Instr(Opcode.JUMP, arg=1, term=term),
                Instr(Opcode.PUSH, arg=1, term=term),  # to here
            ]
        )

    return code


def if_(args_codes: list[list]) -> list[Instr]:
    term = "if"
    assert len(args_codes) == 3, "Недопустимое число аргументов для if"
    code = []
    # arg[0] - flags - jz to second (zero means false) - arg[1] - jmp to end of second - arg[2]
    code.extend(args_codes[0])
    code.extend(
        [
            Instr(Opcode.FLAGS, term=term),
            Instr(Opcode.POP, term=term),
            Instr(Opcode.JZ, arg=(len(args_codes[1]) + 1), term=term),
        ]
    )
    code.extend(args_codes[1])
    code.append(Instr(Opcode.JUMP, arg=(len(args_codes[2])), term=term))
    code.extend(args_codes[2])

    return code


def print_str(args_codes: list[list]) -> list[Instr]:
    # аргумент - адрес строки, которую надо вывести или статическая строка
    global def_port
    term = "print_str"
    assert len(args_codes) >= 1, "Недопустимое число аргументов для print_str"
    code = []
    # arg[0] - dup (addr) - load - flags - jz - write - inc - (loop) --- 1 arg
    for i in range(len(args_codes)):
        code.extend(args_codes[i])
        code.extend(
            [
                Instr(Opcode.DUP, term=term),
                Instr(Opcode.LOAD, term=term),
                Instr(Opcode.FLAGS, term=term),
                Instr(Opcode.JZ, arg=3, term=term),
                Instr(Opcode.WRITE, arg=def_port, term=term),
                Instr(Opcode.INC, term=term),
                Instr(Opcode.JUMP, arg=-7, term=term),
                Instr(Opcode.POP, term=term),
                Instr(Opcode.POP, term=term),
            ]
        )

    code.pop(-1)
    return code


def print_int(args_codes: list[list]) -> list[Instr]:
    global def_port
    term = "print_int"
    assert len(args_codes) == 1, "Недопустимое число аргументов для print_int"
    code = []
    # arg[0] - dup - %10 - +48 - write
    code.append(Instr(Opcode.PUSH, arg=-1, term=term))  # terminator
    code.extend(args_codes[0])
    code.extend(
        [
            Instr(Opcode.FLAGS, term=term),
            Instr(Opcode.JP, arg=3, term=term),
            Instr(Opcode.NEG, term=term),
            Instr(Opcode.PUSH, arg=45, term=term),  # symbol "-"
            Instr(Opcode.WRITE, arg=def_port, term=term),
            Instr(Opcode.DUP, term=term),
            Instr(Opcode.PUSH, arg=10, term=term),
            Instr(Opcode.MOD, term=term),
            Instr(Opcode.PUSH, arg=48, term=term),
            Instr(Opcode.ADD, term=term),
            Instr(Opcode.SWAP, term=term),
            Instr(Opcode.PUSH, arg=10, term=term),
            Instr(Opcode.DIV, term=term),
            Instr(Opcode.FLAGS, term=term),
            Instr(Opcode.JNZ, arg=-10, term=term),
            # print from stack
            Instr(Opcode.POP, term=term),
            Instr(Opcode.FLAGS, term=term),
            Instr(Opcode.JM, arg=2, term=term),
            Instr(Opcode.WRITE, arg=def_port, term=term),
            Instr(Opcode.JUMP, arg=-4, term=term),
        ]
    )
    return code


def read_str(args_codes: list[list]) -> list[Instr]:
    # возвращает адрес прочитанной строки
    global def_port, str_literals_addresses
    term = "read_str"
    assert len(args_codes) == 0, "Недопустимое число аргументов для read_str"
    code = []
    addr = str_literals_addresses.pop()  # addr for new string to read
    code.extend(
        [
            Instr(Opcode.PUSH, arg=addr, term=term),
            Instr(Opcode.DUP, term=term),
            Instr(Opcode.READ, arg=def_port, term=term),
            Instr(Opcode.FLAGS, term=term),
            Instr(Opcode.SWAP, term=term),
            Instr(Opcode.STORE, term=term),
            Instr(Opcode.POP, term=term),
            Instr(Opcode.INC, term=term),
            Instr(Opcode.JNZ, arg=-8, term=term),
            Instr(Opcode.POP, term=term),
            Instr(Opcode.PUSH, arg=addr, term=term),
        ]
    )
    return code


def read_char(args_codes: list[list]) -> list[Instr]:
    global def_port
    term = "read_char"
    assert len(args_codes) == 0, "Недопустимое число аргументов для read_char"
    code = []
    code.extend(
        [
            Instr(Opcode.READ, arg=def_port, term=term),
        ]
    )
    return code


def print_char(args_codes: list[list]) -> list[Instr]:
    global def_port
    term = "print_char"
    assert len(args_codes) == 1, "Недопустимое число аргументов для print_char"
    code = []
    code.extend(args_codes[0])
    code.extend(
        [
            Instr(Opcode.DUP, term=term),
            Instr(Opcode.WRITE, arg=def_port, term=term),
        ]
    )
    return code


def loop_while(args_codes: list[list]) -> list[Instr]:
    term = "loop_while"
    assert len(args_codes) >= 1, "Недопустимое число аргументов для loop_while"
    code = []
    in_loop_code = []

    for ac in args_codes[1:]:
        in_loop_code.extend(ac)
        in_loop_code.append(Instr(Opcode.POP, term=term))

    code.extend(args_codes[0])
    code.extend(
        [
            Instr(Opcode.FLAGS, term=term),
            Instr(Opcode.POP, term=term),
            Instr(Opcode.JZ, arg=len(in_loop_code) + 1, term=term),
        ]
    )
    code.extend(in_loop_code)
    jump_dist = -len(in_loop_code) - len(args_codes[0]) - 4
    code.append(Instr(Opcode.JUMP, arg=jump_dist, term=term))
    code.append(Instr(Opcode.PUSH, arg=0, term=term))

    return code


def _func(args_codes: list[list]) -> list[Instr]:
    code = []
    for arg in args_codes:
        code.extend(arg)
        code.append(Instr(Opcode.POP, term="call"))
    code.pop()

    return code


instructions = {
    "defvar": defvar,
    "setq": setq,
    "+": add,
    "-": sub,
    "*": mul,
    "/": div,
    "mod": mod,
    "=": eq,
    ">": larger,
    "<": lower,
    "if": if_,
    "and": and_,
    "or": or_,
    "not": not_,
    "print_str": print_str,
    "print_char": print_char,
    "print_int": print_int,
    "read_str": read_str,
    "read_char": read_char,
    "loop_while": loop_while,
    '"FUNC': _func,  # technical thing
}


def main(program_str: str) -> list:
    global next_var_addr, str_literals_addresses, dynamic_string_max_length
    expressions, str_literals, str_dynamic = parse_string(f"(A {program_str})")
    func_definitions_code = []
    program_code = []
    # запись строковых литералов в память
    # (записываются в начало памяти данных)
    str_lit_addr = 0
    for str_lit in str_literals:
        str_literals_addresses.append(str_lit_addr)
        for char in str_lit:
            program_code.extend(
                [
                    Instr(
                        Opcode.PUSH,
                        arg=ord(char),
                        term=f"(static string, char: {char})",
                    ),
                    Instr(Opcode.PUSH, arg=str_lit_addr),
                    Instr(Opcode.STORE),
                    Instr(Opcode.POP),
                ]
            )
            str_lit_addr += 1

        program_code.extend(
            [
                Instr(Opcode.PUSH, arg=0, term="(static string, 0-termination)"),
                Instr(Opcode.PUSH, arg=str_lit_addr),
                Instr(Opcode.STORE),
                Instr(Opcode.POP),
            ]
        )
        str_lit_addr += 1

    for i in range(str_dynamic):
        str_literals_addresses.append(str_lit_addr)
        str_lit_addr += dynamic_string_max_length

    # код программы
    next_var_addr = str_lit_addr + 1
    next_func_addr = 0

    for exp in expressions.arguments:
        if exp.name == "defun":
            assert len(exp.arguments) >= 2, "Функция должна иметь тело"
            name_and_vars = re.search(r"(.*)\s*\((.*)\)", exp.arguments[0])

            assert (
                name_and_vars is not None
            ), f"Неверное объявление функции: {exp.arguments[0]}"
            func_name = name_and_vars.groups()[0]

            assert (
                func_name not in functions
            ), f"Двойное объявление функции запрещено: {func_name}"
            assert (
                func_name not in instructions
            ), f"Имя функции совпадает с именем конструкции языка: {func_name}"

            func_vars = name_and_vars.groups()[1].split(" ")
            if func_vars[0] == "":
                func_vars.pop()

            functions.update({func_name: next_func_addr})

            function_code = defun_process(func_vars, exp.arguments[1:])

            func_definitions_code.extend(function_code)
            next_func_addr += len(function_code)
        else:
            program_code.extend(to_machine_code(exp))
            program_code.append(Instr(Opcode.POP, term="(top-level expression)"))

    program_code.append(Instr(Opcode.HALT))

    if next_func_addr != 0:
        full_code = [Instr(Opcode.JUMP, arg=next_func_addr)]
    else:
        full_code = []
    full_code.extend(func_definitions_code)
    full_code.extend(program_code)

    # for p in full_code:
    #     print(str(p))
    return full_code


def translate(input_file: str, output_file: str):
    global variables, functions, str_literals_addresses, next_var_addr
    variables = {}
    functions = {}
    str_literals_addresses = []
    next_var_addr = 0

    with open(input_file, "r") as src_file:
        with open(output_file, "w+") as out_file:
            program_lines = src_file.readlines()
            program_lines_no_comments = [re.sub(r"#.*", "", pl) for pl in program_lines]
            program: str = "".join(program_lines_no_comments)
            json.dump(main(program), out_file, default=Instr.to_dict, indent=2)


if __name__ == "__main__":
    assert (
        len(sys.argv) == 3
    ), "Неверное число аргументов. Использование: translator.py <input_file> <output_file>"
    _, source, target = sys.argv
    translate(source, target)
