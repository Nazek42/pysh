# pysh
A Python system shell with pipes and special syntax

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
