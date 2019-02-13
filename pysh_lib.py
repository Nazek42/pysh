from functools import wraps, partial, reduce
from collections.abc import Callable

import re
import os
from pathlib import Path
import sys
import subprocess
import shlex

from transpile import pyshimport

class ChainSource:
    def __init__(self, thing):
        if isinstance(thing, Callable):
            self.closure = thing
        else:
            self.closure = lambda: thing

    def __invert__(self):
        return self.closure()

    def __or__(self, rhs):
        if isinstance(rhs, Chain):
            return Chain(rhs.transforms, source=self)
        if isinstance(rhs, Callable):
            return Chain([rhs], source=self)
        raise TypeError

class Chain:
    def __init__(self, transforms, source=None):
        self.transforms = transforms
        self.source = source

    def __invert__(self):
        return reduce(lambda x, f: f(x), self.transforms, ~self.source)

    def __or__(self, rhs):
        if isinstance(rhs, Chain):
            return Chain(self.transforms + rhs.transforms, source=self.source)
        if isinstance(rhs, Callable):
            return Chain(self.transforms + [rhs], source=self.source)
        raise TypeError

    def __ror__(self, lhs):
        if isinstance(lhs, Chain):
            return Chain(lhs.transforms + self.transforms, source=lhs.source)
        if isinstance(lhs, ChainSource):
            return Chain(self.transforms, source=lhs)
        if isinstance(lhs, Callable):
            return Chain([lhs] + self.transforms, source=None)
        return Chain(self.transforms, source=ChainSource(lambda: lhs))

def chainable(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return Chain([func(*args, **kwargs)])
    return wrapper

def direct(func):
    return Chain([func])

def source(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return ChainSource(partial(func, *args, **kwargs))
    return wrapper

@chainable
def grep(regex, flags=0):
    def pregrep(thing):
        if isinstance(thing, str):
            return [line for line in thing.splitlines() if re.search(regex, line, flags=flags)]
        else:
            return [line for line in thing if re.search(regex, line, flags=flags)]
    return pregrep

@chainable
def cmap(func):
    return lambda list_: [func(item) for item in list_]

@chainable
def cfilter(func):
    return lambda list_: [item for item in list_ if func(item)]

@chainable
def join(with_):
    return with_.join

joinlines = join('\n')

@chainable
def write(file, mode='t'):
    fp = open(file, 'w'+mode)
    def writer(thing):
        if isinstance(thing, (str, bytes)):
            fp.write(thing)
        else:
            fp.write('\n'.join(thing))
    return writer

@chainable
def append(file, mode='t'):
    fp = open(file, 'a'+mode)
    def writer(thing):
        if isinstance(thing, (str, bytes)):
            fp.write(thing)
        else:
            fp.write('\n'.join(thing))
    return writer

def read(file, mode='t'):
    with open(file, 'r'+mode) as fp:
        return fp.read()

def readlines(file, mode='t'):
    with open(file, 'r'+mode) as fp:
        return fp.readlines()

def cd(newdir='~'):
    newdir_abs = str(Path(newdir).expanduser().resolve())
    try:
        sys.path.remove(str(Path.cwd()))
    except ValueError:
        pass
    os.chdir(newdir_abs)
    sys.path.append(newdir_abs)

@source
def __cmd(args):
    return subprocess.check_output(args).decode()

@chainable
def sort(key=None, reverse=False):
    return partial(sorted, key=key, reverse=reverse)

lib = [
    'chainable',
    'direct',
    'grep',
    'cmap',
    'cfilter',
    'joinlines',
    'join',
    'cd',
    'sort',
    'write',
    'append',
    'read',
    'readlines',
    'pyshimport',
    'source',
    'ChainSource',
    'Chain',
    '__cmd',
]

shell_locals = {f: eval(f) for f in lib}
shell_locals['__co'] = subprocess.check_output
shell_locals['__r'] = subprocess.run
shell_locals['__sp'] = shlex.split
