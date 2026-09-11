import time
from typing import Optional

from fandango.evolution.algorithm import LoggerLevel, SimpleGeneticAlgorithm
from fandango.language.parse.parse import parse


def is_syntactically_valid_byte(bit_string: str) -> bool:
    """
    Verifica che la stringa generata rispetti la grammatica e i vincoli
    definiti in test-byte.fan:

    Grammatica:
        <start> ::= <magic> <length> <payload>
        <magic> ::= <byte> <byte>
        <length> ::= <byte>
        <payload> ::= <byte>*
        <byte> ::= <bit>{8}
        <bit> ::= "0" | "1"

    Vincoli:
        1. Magic bytes: startswith "11001"
        2. length = numero di byte del payload
        4. Almeno un byte del payload ha 7 bit a 1
        5. Ogni byte del payload ha un numero dispari di bit a 1
    """
    try:
        s = bit_string.strip()

        # Deve essere una stringa binaria, lunghezza multipla di 8
        if not s or len(s) % 8 != 0:
            return False
        if any(c not in "01" for c in s):
            return False

        # Min length
        if len(s) < 24:
            return False

        # Suddivisione secondo la grammatica:
        # <magic> (16 bit) | <length> (8 bit) | <payload> (8*n bit)
        magic = s[0:16]
        length_byte = s[16:24]
        payload = s[24:]

        # --- Vincolo 1: magic bytes ---
        # where str(<magic>).startswith("11001")
        if not magic.startswith("11001010"):
            return False

        # Il payload deve essere composto da byte interi
        if len(payload) % 8 != 0:
            return False

        payload_bytes = [payload[i:i + 8] for i in range(0, len(payload), 8)]

        # --- Vincolo 4: almeno un byte del payload ha 7 bit a 1 ---
        # where exists <b> in <payload>.<byte>: str(<b>).count("1") == 7
        if not any(b.count("1") == 7 for b in payload_bytes):
            return False

        # --- Vincolo 5: ogni byte del payload ha un numero dispari di 1 ---
        # where forall <b> in <payload>.<byte>: str(<b>).count("1") % 2 == 1
        if not all(b.count("1") % 2 == 1 for b in payload_bytes):
            return False

        return True

    except Exception:
        return False


def evaluate_byte(
    seconds=60,
    ablation_csv_path: Optional[str] = None,
) -> tuple[str, int, int, float, tuple[float, int, int], float, float]:
    """
    Valuta le soluzioni generate da Fandango per test-byte.fan.
    """
    with open("../eval-tests/test-byte.fan", "r") as file:
        grammar, constraints = parse(file, use_stdlib=False)
        assert grammar is not None

    solutions = []
    time_in_an_hour = time.time() + seconds

    fandango = SimpleGeneticAlgorithm(
        grammar,
        constraints,
        logger_level=LoggerLevel.ERROR,
        csv_path=ablation_csv_path,  # Ablation PATH study
        stop_after_seconds=600,
    )

    fan_gen = fandango.generate()
    for solution in fan_gen:
        solutions.append(solution)
        if time.time() >= time_in_an_hour:
            break

    coverage = grammar.compute_grammar_coverage(solutions, 4)

    valid = []
    for solution in solutions:
        if is_syntactically_valid_byte(str(solution)):
            valid.append(solution)

    if valid:
        set_mean_length = sum(len(str(x)) for x in valid) / len(valid)
        set_medium_length = sorted(len(str(x)) for x in valid)[len(valid) // 2]
    else:
        set_mean_length = 0.0
        set_medium_length = 0.0

    valid_percentage = (len(valid) / len(solutions) * 100) if solutions else 0.0

    return (
        "BYTE",
        len(solutions),
        len(valid),
        valid_percentage,
        coverage,
        set_mean_length,
        set_medium_length,
    )


if __name__ == "__main__":
    result = evaluate_byte(seconds=10)
    print(
        f"Type: {result[0]}, "
        f"Solutions: {result[1]}, "
        f"Valid: {result[2]}, "
        f"Valid Percentage: {result[3]:.2f}%, "
        f"Coverage: {result[4]}, "
        f"Mean Length: {result[5]:.2f}, "
        f"Medium Length: {result[6]:.2f}"
    )