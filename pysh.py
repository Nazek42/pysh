from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

import os
import re
import subprocess
import shutil
import importlib

from pysh_lib import shell_locals

shell_locals['__sp'] = subprocess

def is_valid_expr(string):
    try:
        compile(string, "<pysh>", "eval")
        return True
    except (SyntaxError, ValueError, TypeError):
        return False

# This replicates bash's `backquote` behavior, evaluating to the stdout of the enclosed command, with automatic string interpolation
def parse_backquotes(string):
    return re.sub(r"(?<!\\)`(([^`]|(?<=\\)`)*)(?<!\\)`",
                  r'__sp.check_output(r"""\1""".format(**locals()).split()).decode()', string)\
             .replace(r"\`", '`')

print("pysh pre-alpha")

try:
    with open(".pyshrc") as rc:
        exec(parse_backquotes(rc.read()), shell_locals, shell_locals)
except FileNotFoundError:
    print("no pyshrc found")

multiline = False

while True:
    try:
        cmd = prompt("{} >>> ".format(os.getcwd()),
                     history=FileHistory("pysh_history.txt"),
                     auto_suggest=AutoSuggestFromHistory(),
                     multiline=multiline)
    except EOFError:
        break
    multiline = False
    if cmd.strip() == "multi":
        multiline = True
        print("Multiline mode active. Press Escape + Enter to terminate input.")
    elif cmd.strip() == "clear":
        print('\n' * (shutil.get_terminal_size()[1] + 5))
    elif cmd.strip().startswith('\\'):
        subprocess.run(cmd.strip()[1:].split())
    else:
        multiline = False
        filtered_cmd = parse_backquotes(cmd)
        try:
            if is_valid_expr(filtered_cmd):
                result = eval(filtered_cmd, shell_locals, shell_locals)
                shell_locals['_'] = result
                if result is not None:
                    print(result)
            else:
                exec(filtered_cmd, shell_locals, shell_locals)
        except subprocess.CalledProcessError:
            pass
        except Exception as err:
            print("{}: {}".format(err.__class__.__name__, err))