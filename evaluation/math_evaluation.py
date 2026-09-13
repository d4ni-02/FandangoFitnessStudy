import re
import time
import ast
from typing import Optional

from fandango.evolution.algorithm import LoggerLevel, SimpleGeneticAlgorithm
from fandango.language.parse.parse import parse




def is_syntactically_valid_math(math_string: str) -> bool:
    try:
        s = math_string.strip()
        if not s:
            return False

        for num_str in re.findall(r"\d+", s):
            if int(num_str) % 2 != 0:
                return False

        value = eval(s)
        if abs(value - 42) > 25:
            return False

        if not (10 <= len(s) <= 40):
            return False

        return True
    except Exception as e:
        return False



    

def evaluate_math(
    seconds=60,
    # Ablation study
    ablation_csv_path: Optional[str] = None,
) -> tuple[str, int, int, float, tuple[float, int, int], float, float]:
    
    with open("../eval-tests/test-math.fan", "r") as file:
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
        if is_syntactically_valid_math(str(solution)):
            valid.append(solution)

    set_mean_length = sum(len(str(x)) for x in valid) / len(valid) if valid else 0.0
    set_medium_length = (
        sorted(len(str(x)) for x in valid)[len(valid) // 2] if valid else 0.0
    )
    valid_percentage = (len(valid) / len(solutions) * 100) if solutions else 0.0
    
    return (
        "Math",
        len(solutions),
        len(valid),
        valid_percentage,
        coverage,
        set_mean_length,
        set_medium_length,
    )


if __name__ == "__main__":
    result = evaluate_math(seconds=10)
    print(
        f"Type: {result[0]}, "
        f"Solutions: {result[1]}, "
        f"Valid: {result[2]}, "
        f"Valid Percentage: {result[3]:.2f}%, "
        f"Coverage: {result[4]}, "
        f"Mean Length: {result[5]:.2f}, "
        f"Medium Length: {result[6]:.2f}"
    )