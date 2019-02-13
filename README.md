# pysh
A Python system shell with pipes and special syntax

Dependencies:
 - Python >= 3.6
 - prompt_toolkit

## Special Syntax

#### Backticks
A system command surrounded by \`backticks\` evaluates to the stdout of that command.
E.g.:
```
>>> `git log`
```
inside a Git repository will evaluate to a string containing commit data for that repository.

#### Backslashes

You can also run a system command traditionally by prepending it with a backslash.
E.g.:
```
>>> \mv foo.txt bar.txt
```
will run the expected move operation.
This works as it should for processes which take control of the terminal, for example text editors or games.
It is fully equivalent to running said command in any traditional shell, since it is a direct system call.

#### Interpolation

You can use `format()`-style string interpolation with backticks and backslashes.
`locals()` is automatically passed to `format()`,
  so you can interpolate variables implicitly.

If you're running Python 3.6 or newer,
  you can use arbitrary expressions inside your `{}`.
You can even put backticks inside interpolation.
Nesting can be finicky, but in theory if you escape the backticks with `\` correctly it'll work.

## Chain Objects

Chainable functions are functions which return a *chain object* when called.
Chain objects are pretty much closures with special syntax:
They store some parameters
  and take their final argument not through the normal calling syntax, but through the bitwise or operator.
This allows multiple chain objects to be connected with pipes,
  reminiscent of a traditional shell.
This will all make more sense with an example:
```
>>> `ps -A` | grep("chrome") | write("chrome.txt")
```
When executed, this line will get a list of all running processes and write the lines which contain the string `"chrome"` to the file `chrome.txt`. `grep` and `write` are chainable functions, and `grep("chrome")` and  `write("chrome.txt")` are chain objects.

## Accessing Environment Variables

Pysh has no built-in way of accessing environment variables.
Python does, however, meaning you can easily extend Pysh to do so as well.
For convenience, an `env` object is included in `.pyshrc.default`.
You can access environment variables as `env.<var>`,
  where `var` is the case-sensitive environment variable name.
For example, `env.PATH` evaluates to the system PATH variable.
