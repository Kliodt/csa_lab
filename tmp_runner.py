import os
if __name__ == '__main__':
    test_num = 4
    if test_num == 1:
        os.system("python translator.py examples/programs/cat.lisp machine_code.json")
        os.system("python machine.py machine_code.json examples/inputs/cat.txt")
    if test_num == 2:
        os.system("python translator.py examples/programs/hello.lisp machine_code.json")
        os.system("python machine.py machine_code.json examples/inputs/hello.txt")
    if test_num == 3:
        os.system("python translator.py examples/programs/hello_user.lisp machine_code.json")
        os.system("python machine.py machine_code.json examples/inputs/hello_user.txt")
    if test_num == 4:
        os.system("python translator.py examples/programs/prob2.lisp machine_code.json")
        os.system("python machine.py machine_code.json examples/inputs/prob2.txt")
