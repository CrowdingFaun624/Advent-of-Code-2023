import math
from pathlib2 import Path

def load_document(name:str) -> str:
    if isinstance(name, str):
        name = parent_path.joinpath(name)
    path = Path(name)
    if parent_path not in path.parents:
        raise FileNotFoundError("File is not in the correct directory!")
    with open(path, "rt") as file:
        return file.read()

def parse_document_with_kerning(document:str) -> list[tuple[int,int]]:
    assert document.count("\n") == 1
    time_line, distance_line = document.split("\n")
    times = [int(time) for time in time_line.replace("Time:", "").split(" ") if len(time) > 0]
    distances = [int(distance) for distance in distance_line.replace("Distance:", "").split(" ") if len(distance) > 0]
    return list(zip(times, distances))

def parse_document_no_kerning(document:str) -> tuple[int,int]:
    assert document.count("\n") == 1
    time_line, distance_line = document.split("\n")
    time = int(time_line.replace("Time:", "").replace(" ", ""))
    distance = int(distance_line.replace("Distance:", "").replace(" ", ""))
    return time, distance

def quadratic_formula(time:int, distance:int) -> tuple[float, float]:
    return (
        (time - math.sqrt(time**2 - 4 * distance)) / 2,
        (time + math.sqrt(time**2 - 4 * distance)) / 2
    )

def get_number_of_integers_in_range(start:float, stop:float) -> int:
    count = math.floor(stop) - math.floor(start)
    if stop.is_integer(): count -= 1
    return count

def product(_list:list[int|float]) -> int|float:
    output = 1
    for item in _list:
        output *= item
    return output

def main() -> None:
    document_string = load_document("Input.txt")
    races = parse_document_with_kerning(document_string)
    number_of_ways = [get_number_of_integers_in_range(*quadratic_formula(time, distance)) for time, distance in races]
    print("Part 1: %i" % product(number_of_ways))
    race = parse_document_no_kerning(document_string)
    print("Part 2: %i" % get_number_of_integers_in_range(*quadratic_formula(*race)))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()
