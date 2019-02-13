import sys
import re
import os
from pathlib import Path
from tempfile import mkstemp
from contextlib import contextmanager
from importlib.util import spec_from_file_location, module_from_spec

version = sys.version_info
have_fstrings = version.major == 3 and version.minor >= 6
if not have_fstrings:
    print("Python <3.6 detected. Advanced interpolation disabled.")

format_string = r'fr""" {} """' if have_fstrings else r'r""" {} """.format(**locals)'
format_string_alt = r"fr''' {} '''" if have_fstrings else r"r''' {} '''.format(**locals)"

def compile_pysh(string, prelude=True):
    pysh_lib_path = Path(sys.path[0]) / "pysh_lib.py"
    prelude = """\
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
spec = spec_from_file_location("pysh_lib", Path("{}").resolve())
pysh_lib = module_from_spec(spec)
spec.loader.exec_module(pysh_lib)
for (name, value) in pysh_lib.shell_locals.items():
    vars()[name] = value
del spec_from_file_location, module_from_spec, Path, spec, pysh_lib
""".format(pysh_lib_path)
    compiled = parse_backslashes(parse_backquotes(string))
    if prelude:
        return '\n'.join((prelude, compiled))
    else:
        return compiled

def pyshimport(path):
    path = Path(path).resolve()
    name = path.stem
    try:
        with open(path.resolve(strict=True)) as lib:
            pysh_code = lib.read()
    except FileNotFoundError:
        raise ImportError("No Pysh file found at {}".format(str(path)))

    python_code = compile_pysh(pysh_code)

    try:
        with MultiWriteTempfile(suffix='.py', text=True) as tmp_path:
            with open(tmp_path, 'wt') as tmp_lib:
                tmp_lib.write(python_code)
            spec = spec_from_file_location(path.stem, tmp_path)
            module = module_from_spec(spec)
            spec.loader.exec_module(module)
            sys.modules[name] = module
            return module
    finally:
        pass

# This replicates bash's `backquote` behavior, evaluating to the stdout of the enclosed command, with automatic string interpolation
def parse_backquotes(string):
    return re.sub(r"(?<!\\)`(([^`]|(?<=\\)`)*)(?<!\\)`",
                  r'__cmd( __sp( {} ) )'.format(format_string.format(r'\1')), string)\
             .replace(r"\`", '`')

def parse_backslashes(string):
    return re.sub(r"^(\s*)\\(.*)$",
                  r'\1__r( __sp( {} ) )'.format(format_string_alt.format(r'\2')),
                  string, flags=re.MULTILINE)

@contextmanager
def MultiWriteTempfile(**kwargs):
    handle, path = mkstemp(**kwargs)
    try:
        yield path
    finally:
        os.remove(path)
