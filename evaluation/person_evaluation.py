import time
from typing import Optional
import re

from fandango.evolution.algorithm import LoggerLevel, SimpleGeneticAlgorithm
from fandango.language.parse.parse import parse


def is_valid_word(word: str) -> bool:
    """verify: <uppercase> <lowercase>+"""
    if not word or len(word) < 2:
        return False
    return word[0].isupper() and all(c.islower() for c in word[1:])

def is_valid_age(age_str: str) -> bool:
    """Verify age is numeric"""
    return bool(age_str) and age_str.isdigit()

def is_syntactically_valid_person(person_string: str) -> bool:
    try:
        s = person_string.strip()

        # <person_record> ::= <name> "," <age>
        parts = s.split(",", 1)
        if len(parts) != 2:
            print(person_string)
            return False

        name_part, age_str = parts[0].strip(), parts[1].strip()

        # <name> ::= <first_name> " " <last_name>
        name_tokens = name_part.split(" ", 1)
        if len(name_tokens) != 2:
            print(person_string)
            return False

        first_name, last_name = name_tokens

        # <word> structure
        if not is_valid_word(first_name):
            print(person_string)
            return False
        if not is_valid_word(last_name):
            print(person_string)
            return False

        # <age> structure
        if not is_valid_age(age_str):
            print(person_string)
            return False

        age = int(age_str)

        # 21 <= età <= 100
        if not (21 <= age <= 100):
            print(person_string)
            return False

        # mod 7
        if age % 7 != 0:
            print(person_string)
            return False

        # names start with "A"
        if not first_name.startswith("A"):
            print(person_string)
            return False
        if not last_name.startswith("A"):
            print(person_string)
            return False

        # name length check
        if not (8 <= len(first_name) <= 20):
            print(person_string)
            return False
        if not (8 <= len(last_name) <= 20):
            print(person_string)
            return False

        return True

    except Exception:
        print("OPS", person_string)
        return False

def evaluate_person(
    seconds=60,
    ablation_csv_path: Optional[str] = None,
) -> tuple[str, int, int, float, tuple[float, int, int], float, float]:
    with open("../eval-tests/test-person.fan", "r") as file:
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
        if is_syntactically_valid_person(str(solution)):
            valid.append(solution)

    # Gestione sicura del calcolo della lunghezza in caso di 0 soluzioni valide
    if valid:
        set_mean_length = sum(len(str(x)) for x in valid) / len(valid)
        set_medium_length = sorted(len(str(x)) for x in valid)[len(valid) // 2]
    else:
        set_mean_length = 0.0
        set_medium_length = 0.0

    valid_percentage = (len(valid) / len(solutions) * 100) if solutions else 0.0

    return (
        "PERSON",
        len(solutions),
        len(valid),
        valid_percentage,
        coverage,
        set_mean_length,
        set_medium_length,
    )


if __name__ == "__main__":
    result = evaluate_person(seconds=10)
    print(
        f"Type: {result[0]}, "
        f"Solutions: {result[1]}, "
        f"Valid: {result[2]}, "
        f"Valid Percentage: {result[3]:.2f}%, "
        f"Coverage: {result[4]}, "
        f"Mean Length: {result[5]:.2f}, "
        f"Medium Length: {result[6]:.2f}"
    )