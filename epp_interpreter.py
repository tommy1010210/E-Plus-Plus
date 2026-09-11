from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Any, Callable


class EppError(Exception):
    pass


class EppSyntaxError(EppError):
    pass


class EppRuntimeError(EppError):
    pass


@dataclass
class Statement:
    kind: str
    line: int
    value: Any = None
    extra: Any = None


@dataclass
class UserFunction:
    name: str
    params: list[str]
    body: list[Statement]
    closure: "Environment"
    interpreter: "EppInterpreter"

    def __call__(self, *args: Any) -> Any:
        if len(args) != len(self.params):
            raise EppRuntimeError(
                f"{self.name} expected {len(self.params)} argument(s), got {len(args)}."
            )

        local_env = Environment(parent=self.closure)
        for name, value in zip(self.params, args):
            local_env.define(name, value)

        try:
            self.interpreter._execute_block(self.body, local_env)
        except ReturnSignal as signal:
            return signal.value
        return None


class ReturnSignal(Exception):
    def __init__(self, value: Any) -> None:
        self.value = value


class Environment:
    def __init__(self, parent: "Environment | None" = None) -> None:
        self.parent = parent
        self.values: dict[str, Any] = {}

    def define(self, name: str, value: Any) -> None:
        self.values[name] = value

    def assign(self, name: str, value: Any) -> None:
        if name in self.values:
            self.values[name] = value
            return
        if self.parent is not None:
            self.parent.assign(name, value)
            return
        self.values[name] = value

    def get(self, name: str) -> Any:
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise EppRuntimeError(f"Unknown name '{name}'.")


class EppParser:
    def parse(self, source: str) -> list[Statement]:
        lines = self._prepare_lines(source)
        statements, index, terminator = self._parse_block(lines, 0, allow_terminators=False)
        if terminator is not None:
            line_no, value = terminator
            raise EppSyntaxError(f"Line {line_no}: unexpected '{value}'.")
        if index != len(lines):
            line_no, value = lines[index]
            raise EppSyntaxError(f"Line {line_no}: could not parse '{value}'.")
        return statements

    def _prepare_lines(self, source: str) -> list[tuple[int, str]]:
        prepared: list[tuple[int, str]] = []
        for number, raw_line in enumerate(source.splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if not line.endswith("."):
                raise EppSyntaxError(f"Line {number}: every E++ statement must end with a period.")
            statement = line[:-1].strip()
            if not statement:
                continue
            prepared.append((number, statement))
        return prepared

    def _parse_block(
        self,
        lines: list[tuple[int, str]],
        index: int,
        allow_terminators: bool,
    ) -> tuple[list[Statement], int, tuple[int, str] | None]:
        statements: list[Statement] = []

        while index < len(lines):
            line_no, text = lines[index]
            lowered = text.lower()

            if lowered in {"end", "otherwise"}:
                if allow_terminators:
                    return statements, index, (line_no, lowered)
                raise EppSyntaxError(f"Line {line_no}: unexpected '{text}'.")

            if lowered.startswith("if ") and lowered.endswith(" then"):
                condition = text[3:-5].strip()
                then_body, index, terminator = self._parse_block(lines, index + 1, True)
                else_body: list[Statement] = []
                if terminator and terminator[1] == "otherwise":
                    else_body, index, terminator = self._parse_block(lines, index + 1, True)
                if not terminator or terminator[1] != "end":
                    raise EppSyntaxError(f"Line {line_no}: if block must finish with 'end.'.")
                statements.append(Statement("if", line_no, condition, (then_body, else_body)))
                index += 1
                continue

            if lowered.startswith("while ") and lowered.endswith(" do"):
                condition = text[6:-3].strip()
                body, index, terminator = self._parse_block(lines, index + 1, True)
                if not terminator or terminator[1] != "end":
                    raise EppSyntaxError(f"Line {line_no}: while block must finish with 'end.'.")
                statements.append(Statement("while", line_no, condition, body))
                index += 1
                continue

            function_match = re.fullmatch(
                r"function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)\s+do",
                text,
                flags=re.IGNORECASE,
            )
            if function_match:
                name = function_match.group(1)
                params_text = function_match.group(2).strip()
                params = [] if not params_text else [part.strip() for part in params_text.split(",")]
                for param in params:
                    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", param):
                        raise EppSyntaxError(f"Line {line_no}: invalid parameter name '{param}'.")
                body, index, terminator = self._parse_block(lines, index + 1, True)
                if not terminator or terminator[1] != "end":
                    raise EppSyntaxError(f"Line {line_no}: function block must finish with 'end.'.")
                statements.append(Statement("function", line_no, name, (params, body)))
                index += 1
                continue

            statements.append(self._parse_simple_statement(line_no, text))
            index += 1

        return statements, index, None

    def _parse_simple_statement(self, line_no: int, text: str) -> Statement:
        lowered = text.lower()

        if lowered.startswith("say "):
            return Statement("say", line_no, text[4:].strip())

        if lowered.startswith("return "):
            return Statement("return", line_no, text[7:].strip())

        let_match = re.fullmatch(
            r"let\s+([A-Za-z_][A-Za-z0-9_]*)\s+(?:be|=)\s+(.+)",
            text,
            flags=re.IGNORECASE,
        )
        if let_match:
            return Statement("let", line_no, let_match.group(1), let_match.group(2).strip())

        assign_match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)", text)
        if assign_match:
            return Statement("assign", line_no, assign_match.group(1), assign_match.group(2).strip())

        return Statement("expr", line_no, text)


class ExpressionEvaluator:
    _binary_ops = {
        ast.Add: lambda a, b: a + b,
        ast.Sub: lambda a, b: a - b,
        ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: a / b,
        ast.FloorDiv: lambda a, b: a // b,
        ast.Mod: lambda a, b: a % b,
        ast.Pow: lambda a, b: a**b,
    }
    _unary_ops = {
        ast.UAdd: lambda a: +a,
        ast.USub: lambda a: -a,
        ast.Not: lambda a: not a,
    }
    _compare_ops = {
        ast.Eq: lambda a, b: a == b,
        ast.NotEq: lambda a, b: a != b,
        ast.Lt: lambda a, b: a < b,
        ast.LtE: lambda a, b: a <= b,
        ast.Gt: lambda a, b: a > b,
        ast.GtE: lambda a, b: a >= b,
    }

    def evaluate(self, expression: str, env: Environment) -> Any:
        expression = self._translate_keywords(expression)
        try:
            parsed = ast.parse(expression, mode="eval")
        except SyntaxError as exc:
            raise EppRuntimeError(f"Invalid expression '{expression}'.") from exc
        return self._eval_node(parsed.body, env)

    def _translate_keywords(self, expression: str) -> str:
        replacements = {
            r"\btrue\b": "True",
            r"\bfalse\b": "False",
            r"\bnothing\b": "None",
        }
        translated = expression
        for pattern, replacement in replacements.items():
            translated = re.sub(pattern, replacement, translated, flags=re.IGNORECASE)
        return translated

    def _eval_node(self, node: ast.AST, env: Environment) -> Any:
        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.Name):
            if node.id in {"True", "False", "None"}:
                return {"True": True, "False": False, "None": None}[node.id]
            return env.get(node.id)

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self._binary_ops:
                raise EppRuntimeError("That operator is not supported yet.")
            return self._binary_ops[op_type](
                self._eval_node(node.left, env),
                self._eval_node(node.right, env),
            )

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in self._unary_ops:
                raise EppRuntimeError("That unary operator is not supported yet.")
            return self._unary_ops[op_type](self._eval_node(node.operand, env))

        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                result = True
                for value in node.values:
                    result = self._eval_node(value, env)
                    if not result:
                        return result
                return result
            if isinstance(node.op, ast.Or):
                result = False
                for value in node.values:
                    result = self._eval_node(value, env)
                    if result:
                        return result
                return result
            raise EppRuntimeError("That boolean operator is not supported yet.")

        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left, env)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator, env)
                op_type = type(op)
                if op_type not in self._compare_ops:
                    raise EppRuntimeError("That comparison is not supported yet.")
                if not self._compare_ops[op_type](left, right):
                    return False
                left = right
            return True

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise EppRuntimeError("Only direct function calls are supported.")
            func = env.get(node.func.id)
            if not callable(func):
                raise EppRuntimeError(f"'{node.func.id}' is not callable.")
            args = [self._eval_node(arg, env) for arg in node.args]
            return func(*args)

        raise EppRuntimeError(f"Unsupported expression: {type(node).__name__}.")


class EppInterpreter:
    def __init__(
        self,
        output: Callable[[str], None] | None = None,
        input_func: Callable[[str], str] | None = None,
    ) -> None:
        self.output = output or print
        self.input_func = input_func or input
        self.parser = EppParser()
        self.evaluator = ExpressionEvaluator()
        self.globals = Environment()
        self._load_builtins()

    def run(self, source: str) -> None:
        statements = self.parser.parse(source)
        self._execute_block(statements, self.globals)

    def _load_builtins(self) -> None:
        self.globals.define("text", str)
        self.globals.define("number", float)
        self.globals.define("whole", int)
        self.globals.define("length", len)
        self.globals.define("ask", self.input_func)

    def _execute_block(self, statements: list[Statement], env: Environment) -> None:
        for statement in statements:
            try:
                self._execute(statement, env)
            except ReturnSignal:
                raise
            except EppError:
                raise
            except Exception as exc:
                raise EppRuntimeError(f"Line {statement.line}: {exc}") from exc

    def _execute(self, statement: Statement, env: Environment) -> None:
        if statement.kind == "say":
            value = self.evaluator.evaluate(statement.value, env)
            self.output(self._format_value(value))
            return

        if statement.kind == "let":
            value = self.evaluator.evaluate(statement.extra, env)
            env.define(statement.value, value)
            return

        if statement.kind == "assign":
            value = self.evaluator.evaluate(statement.extra, env)
            env.assign(statement.value, value)
            return

        if statement.kind == "expr":
            self.evaluator.evaluate(statement.value, env)
            return

        if statement.kind == "if":
            then_body, else_body = statement.extra
            if self.evaluator.evaluate(statement.value, env):
                self._execute_block(then_body, env)
            else:
                self._execute_block(else_body, env)
            return

        if statement.kind == "while":
            while self.evaluator.evaluate(statement.value, env):
                self._execute_block(statement.extra, env)
            return

        if statement.kind == "function":
            params, body = statement.extra
            env.define(statement.value, UserFunction(statement.value, params, body, env, self))
            return

        if statement.kind == "return":
            value = self.evaluator.evaluate(statement.value, env)
            raise ReturnSignal(value)

        raise EppRuntimeError(f"Unknown statement kind '{statement.kind}'.")

    def _format_value(self, value: Any) -> str:
        if value is True:
            return "true"
        if value is False:
            return "false"
        if value is None:
            return "nothing"
        return str(value)
