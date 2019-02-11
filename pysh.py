#!/usr/bin/env python3

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition
from prompt_toolkit.completion import WordCompleter, ThreadedCompleter

import os
import re
import subprocess
import shutil
import importlib
import shlex
import sys
from getpass import getuser
from socket import gethostname
from pathlib import Path

start_dir = Path.cwd()

version = sys.version_info
have_fstrings = version.major == 3 and version.minor >= 6
if not have_fstrings:
    print("Python <3.6 detected. Advanced interpolation disabled.")

format_string = r'fr""" {} """' if have_fstrings else r'r""" {} """.format(**locals)'

from pysh_lib import shell_locals, cd

shell_locals['__co'] = subprocess.check_output
shell_locals['__sp'] = shlex.split

def is_valid_expr(string):
    try:
        compile(string, "<pysh>", "eval")
        return True
    except (SyntaxError, ValueError, TypeError):
        return False

keys = KeyBindings()

# This replicates bash's `backquote` behavior, evaluating to the stdout of the enclosed command, with automatic string interpolation
def parse_backquotes(string):
    return re.sub(r"(?<!\\)`(([^`]|(?<=\\)`)*)(?<!\\)`",
                  r'__co( __sp( {} ) ).decode()'.format(format_string.format(r'\1')), string)\
             .replace(r"\`", '`')

def get_autocomplete_suggestions():
    sugg = os.listdir()
    sugg.extend(shell_locals.keys())
    return sugg

home = Path.home().resolve()
def get_dir_str():
    cwd = Path.cwd()
    if cwd == home:
        rel = Path('~')
    elif home in cwd.parents:
        rel = (Path('~') / cwd.relative_to(home))
    else:
        rel = cwd
    return str(rel)

cd(home)

try:
    with open(".pyshrc") as rc:
        exec(parse_backquotes(rc.read()), shell_locals, shell_locals)
except FileNotFoundError:
    print("no pyshrc found")
except Exception as err:
    print("while reading .pyshrc: {}: {}".format(err.__class__.__name__, err))

#print("help")
#print(Path(__file__))

if 'ps1' not in shell_locals or 'ps2' not in shell_locals:
    cd(start_dir)
    with open(str(Path(__file__).resolve().parent / '.pyshrc.default')) as rc:
        exec(parse_backquotes(rc.read()), shell_locals, shell_locals)
    cd(home)

multiline = False

while True:
    try:
        ps1 = shell_locals['ps1'](
            host=gethostname(),
            user=getuser(),
            cwd=get_dir_str(),
        )
        cmd = prompt(ps1,
                     history=FileHistory(".pysh_history"),
                     auto_suggest=AutoSuggestFromHistory(),
                     multiline=multiline,
                     key_bindings=keys,
                     prompt_continuation=shell_locals['ps2'],
                     completer=ThreadedCompleter(WordCompleter(get_autocomplete_suggestions())))
    except EOFError:
        break
    multiline = False
    if cmd.strip() == "multi":
        multiline = True
        print("Multiline mode active. Press Escape + Enter to terminate input.")
    elif cmd.strip() == "clear":
        print('\n' * (shutil.get_terminal_size()[1] + 5))
    elif cmd.strip().startswith('\\'):
        try:
            cmd_list = shlex.split(eval(format_string.format(cmd.strip()[1:]), shell_locals, shell_locals))
            subprocess.run(cmd_list)
        except FileNotFoundError:
            print("no command `{}` found".format(cmd_list[0]))
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
