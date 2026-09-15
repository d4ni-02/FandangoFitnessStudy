import time
from typing import Optional

from fandango.evolution.algorithm import LoggerLevel, SimpleGeneticAlgorithm
from fandango.language.parse.parse import parse





def is_syntactically_valid_byte(bit_string: str) -> bool:
    """
    Verifica se una stringa soddisfa i vincoli della grammatica specificata:

        where 100 <= int(str(<magic_byte1>), 2) + int(str(<magic_byte2>), 2) <= 300
        where int(str(<magic_byte1>), 2) % 4 == 0
        where int(str(<magic_byte2>), 2) % 5 == 0
        where forall <b> in <payload>.<byte>: str(<b>) != "00000000"
        where forall <b> in <payload>.<byte>: str(<b>).count("0") >= 2
        where len(str(<payload>)) % 256 == int(str(<length>), 2) * 8
    """
    try:
        if not isinstance(bit_string, str):
            return False

        # Sintassi: solo '0' e '1', nessuna spaziatura
        if not bit_string or any(c not in "01" for c in bit_string):
            return False

        # Layout: <magic_byte1>(8) <magic_byte2>(8) <length>(8) <payload>(8*N, N >= 1)
        # Lunghezza minima = 32 bit (4 byte)
        if len(bit_string) < 32 or len(bit_string) % 8 != 0:
            return False

        magic_byte1 = bit_string[0:8]
        magic_byte2 = bit_string[8:16]
        length_byte = bit_string[16:24]
        payload = bit_string[24:]

        if len(payload) % 8 != 0 or len(payload) == 0:
            return False

        mb1_val = int(magic_byte1, 2)
        mb2_val = int(magic_byte2, 2)

        # Vincolo 1: 100 <= magic_byte1 + magic_byte2 <= 300
        if not (100 <= mb1_val + mb2_val <= 300):
            return False

        # Vincolo 2: magic_byte1 % 4 == 0
        if mb1_val % 4 != 0:
            return False

        # Vincolo 3: magic_byte2 % 5 == 0
        if mb2_val % 5 != 0:
            return False

        # Vincolo 4: Vincoli sui byte del payload
        payload_bytes = [payload[i:i + 8] for i in range(0, len(payload), 8)]
        for b in payload_bytes:
            if b == "00000000":
                return False
            if b.count("0") < 2:
                return False

        # Vincolo 5: len(payload) % 256 == int(length) * 8
        if len(payload) % 256 != int(length_byte, 2) * 8:
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