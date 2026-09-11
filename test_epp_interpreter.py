import unittest

from epp_interpreter import EppInterpreter


def run_epp(source: str) -> list[str]:
    output: list[str] = []
    EppInterpreter(output=output.append).run(source)
    return output


class EppInterpreterTests(unittest.TestCase):
    def test_say_and_variables(self) -> None:
        self.assertEqual(
            run_epp(
                """
                let name be "Tom".
                say "Hi, " + name.
                """
            ),
            ["Hi, Tom"],
        )

    def test_if_otherwise(self) -> None:
        self.assertEqual(
            run_epp(
                """
                let score be 10.
                if score > 5 then.
                    say "win".
                otherwise.
                    say "lose".
                end.
                """
            ),
            ["win"],
        )

    def test_while_updates_outer_variable(self) -> None:
        self.assertEqual(
            run_epp(
                """
                let count be 1.
                while count <= 3 do.
                    count = count + 1.
                end.
                say count.
                """
            ),
            ["4"],
        )

    def test_functions(self) -> None:
        self.assertEqual(
            run_epp(
                """
                function double(number) do.
                    return number * 2.
                end.
                say double(21).
                """
            ),
            ["42"],
        )


if __name__ == "__main__":
    unittest.main()
