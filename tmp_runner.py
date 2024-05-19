import os
if __name__ == '__main__':
    os.system("python translator.py program.lisp machine_code.json")
    os.system("python machine.py machine_code.json input_tmp")
