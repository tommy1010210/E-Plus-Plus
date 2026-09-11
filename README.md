# E++

E++ is a small interpreted programming language with a Python-like feel and English-style statements.

Instead of `print`, E++ uses `say`. Every statement ends with a period.

```epp
say "Hello from E++".

let name be "Tom".
say "Hi, " + name.
```

## Features

- Interactive GUI shell
- `Enter` to run code in the shell
- `Shift+Enter` to write multiple lines in the shell
- Terminal shell fallback
- `.epp` source files
- Variables
- Arithmetic
- Strings
- Conditions
- Loops
- Functions
- Basic tests using Python's standard library

## Requirements

- Python 3.10 or newer
- Tkinter for the GUI shell

Tkinter is included with most Python installs. If the GUI shell does not open, use the terminal shell instead.

## Quick Start

Clone or download the project, then run the GUI shell:

```powershell
python epp_shell.py
```

Type this into the shell and press `Enter`:

```epp
say "Test".
```

Expected output:

```text
Test
```

## Multiline Code

In the GUI shell:

- Press `Enter` to run the current code.
- Press `Shift+Enter` to add a new line.

Example:

```epp
let count be 1.
while count <= 3 do.
    say count.
    count = count + 1.
end.
```

## Terminal Shell

Run:

```powershell
python epp_shell.py --terminal
```

Terminal mode cannot reliably detect `Shift+Enter`, so use multiline mode:

```text
:multi
```

Finish multiline input with a blank line.

## Running Files

E++ source files use the `.epp` extension.

Run the sample program:

```powershell
python epp.py sample.epp
```

Run your own file:

```powershell
python epp.py my_program.epp
```

## Syntax

### Say

```epp
say "Hello".
say 2 + 3.
```

### Variables

```epp
let score be 10.
score = score + 5.
say score.
```

### Conditions

```epp
let score be 10.

if score > 5 then.
    say "You win".
otherwise.
    say "Try again".
end.
```

### Loops

```epp
let count be 1.

while count <= 3 do.
    say count.
    count = count + 1.
end.
```

### Functions

```epp
function greet(name) do.
    return "Hello, " + name.
end.

say greet("Tom").
```

## Built-In Functions

| Function | Description |
| --- | --- |
| `text(value)` | Converts a value to text |
| `number(value)` | Converts a value to a decimal number |
| `whole(value)` | Converts a value to a whole number |
| `length(value)` | Gets the length of text or a list-like value |
| `ask(prompt)` | Asks for user input |

## Project Files

| File | Purpose |
| --- | --- |
| `epp_interpreter.py` | Parser, evaluator, runtime environment, and interpreter |
| `epp_shell.py` | GUI shell and terminal shell |
| `epp.py` | Command-line runner for `.epp` files |
| `sample.epp` | Example E++ program |
| `test_epp_interpreter.py` | Unit tests |

## Tests

Run:

```powershell
python -m unittest -v
```

## Status

E++ is an early toy language. It is interpreted in Python and is meant for learning, experimenting, and growing into a custom language step by step.
