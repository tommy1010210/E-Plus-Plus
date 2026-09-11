from __future__ import annotations

import sys
import tkinter as tk
from tkinter import scrolledtext

from epp_interpreter import EppError, EppInterpreter


PROMPT = "E++> "


class EppGuiShell:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("E++ Shell")
        self.root.geometry("900x560")

        self.text = scrolledtext.ScrolledText(
            self.root,
            wrap="word",
            font=("Consolas", 12),
            bg="#101418",
            fg="#e8eef2",
            insertbackground="#e8eef2",
            selectbackground="#35506b",
            padx=12,
            pady=12,
            undo=True,
        )
        self.text.pack(fill="both", expand=True)

        self.text.tag_configure("prompt", foreground="#7cc7ff")
        self.text.tag_configure("output", foreground="#b8e986")
        self.text.tag_configure("error", foreground="#ff8f8f")
        self.text.tag_configure("hint", foreground="#9ca8b3")

        self.interpreter = EppInterpreter(output=self.write_output, input_func=self.ask_user)
        self.waiting_input: tk.StringVar | None = None

        self.text.bind("<Return>", self.run_current_input)
        self.text.bind("<Shift-Return>", self.insert_newline)
        self.text.bind("<BackSpace>", self.guard_backspace)
        self.text.bind("<Key>", self.guard_typing)

        self.write_hint("Enter runs code. Shift+Enter adds a new line. Every E++ line ends with a period.")
        self.write_hint('Try: say "Hello from E++".')
        self.prompt()

    def start(self) -> None:
        self.root.mainloop()

    def prompt(self) -> None:
        self.append(PROMPT, "prompt")
        self.text.mark_set("input_start", "end-1c")
        self.text.mark_gravity("input_start", "left")
        self.text.mark_set("insert", "end-1c")
        self.text.see("end")
        self.text.focus_set()

    def run_current_input(self, event: tk.Event | None = None) -> str:
        if self.waiting_input is not None:
            answer = self.text.get("input_start", "end-1c")
            self.append("\n")
            self.waiting_input.set(answer)
            return "break"

        code = self.text.get("input_start", "end-1c").strip()
        self.append("\n")
        if code:
            try:
                self.interpreter.run(code)
            except EppError as exc:
                self.write_error(str(exc))
        self.prompt()
        return "break"

    def insert_newline(self, event: tk.Event | None = None) -> str:
        self.text.insert("insert", "\n")
        return "break"

    def guard_backspace(self, event: tk.Event | None = None) -> str | None:
        if self.text.tag_ranges("sel"):
            selection_start = self.text.index("sel.first")
            if self.text.compare(selection_start, "<", "input_start"):
                return "break"
            return None
        if self.text.compare("insert", "<=", "input_start"):
            return "break"
        return None

    def guard_typing(self, event: tk.Event) -> str | None:
        if len(event.char) == 0:
            return None
        if self.text.compare("insert", "<", "input_start"):
            self.text.mark_set("insert", "end-1c")
        return None

    def append(self, message: str, tag: str | None = None) -> None:
        if tag:
            self.text.insert("end-1c", message, tag)
        else:
            self.text.insert("end-1c", message)
        self.text.see("end")

    def write_output(self, message: str) -> None:
        self.append(f"{message}\n", "output")

    def write_error(self, message: str) -> None:
        self.append(f"Error: {message}\n", "error")

    def write_hint(self, message: str) -> None:
        self.append(f"{message}\n", "hint")

    def ask_user(self, prompt: str = "") -> str:
        if prompt:
            self.write_output(prompt)
        self.append("input> ", "prompt")
        self.text.mark_set("input_start", "end-1c")
        self.text.mark_gravity("input_start", "left")
        self.text.mark_set("insert", "end-1c")
        variable = tk.StringVar()
        self.waiting_input = variable
        self.root.wait_variable(variable)
        self.waiting_input = None
        return variable.get()


def terminal_shell() -> None:
    interpreter = EppInterpreter()
    print("E++ terminal shell")
    print("Enter runs code. Type :multi for multiline mode, :quit to exit.")
    while True:
        try:
            line = input(PROMPT)
        except EOFError:
            print()
            return

        command = line.strip()
        if command == ":quit":
            return
        if command == ":multi":
            print("Multiline mode. Finish with a blank line.")
            lines: list[str] = []
            while True:
                next_line = input("...  ")
                if not next_line.strip():
                    break
                lines.append(next_line)
            command = "\n".join(lines)

        if not command:
            continue
        try:
            interpreter.run(command)
        except EppError as exc:
            print(f"Error: {exc}")


def main() -> None:
    if "--terminal" in sys.argv:
        terminal_shell()
        return
    EppGuiShell().start()


if __name__ == "__main__":
    main()
