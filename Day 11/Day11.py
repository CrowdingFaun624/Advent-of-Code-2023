from typing import Generator
from itertools import combinations
from pathlib2 import Path

def load_document(name:str) -> str:
    if isinstance(name, str):
        name = parent_path.joinpath(name)
    path = Path(name)
    if parent_path not in path.parents:
        raise FileNotFoundError("File is not in the correct directory!")
    with open(path, "rt") as file:
        return file.read()

class Galaxy():
    def __init__(self, x:int, y:int, id:int) -> None:
        self.x = x
        self.y = y
        self.id = id
    
    def __repr__(self) -> str:
        return "<Galaxy %i at (%i, %i)>" % (self.id, self.x, self.y)

def parse_galaxies(document:str, empty_amount:int) -> list[Galaxy]:
    lines = document.split("\n")
    empty_rows = set(range(len(lines[0])))
    empty_columns = set(range(len(lines)))
    galaxy_positions:list[tuple[int,int]] = []
    for y, line in enumerate(lines):
        for x, char in enumerate(line):
            if char == "#":
                empty_rows.discard(y)
                empty_columns.discard(x)
                galaxy_positions.append((x, y))
    horizontal_offsets:list[int] = []
    total_offset = 0
    for x in range(len(lines[0])):
        if x in empty_columns:
            total_offset += empty_amount - 1
        horizontal_offsets.append(total_offset)
    vertical_offsets:list[int] = []
    total_offset = 0
    for y in range(len(lines)):
        if y in empty_rows:
            total_offset += empty_amount - 1
        vertical_offsets.append(total_offset)
    galaxies = [Galaxy(pos[0] + horizontal_offsets[pos[0]], pos[1] + vertical_offsets[pos[1]], index + 1) for index, pos in enumerate(galaxy_positions)]
    return galaxies

def get_distances(galaxies:list[Galaxy]) -> Generator[int,None,None]:
    pairs = combinations(galaxies, 2)
    for galaxy1, galaxy2 in pairs:
        yield abs(galaxy1.x - galaxy2.x) + abs(galaxy1.y - galaxy2.y)

def main() -> None:
    document_string = load_document("Input.txt")
    galaxies = parse_galaxies(document_string, 2)
    distances = get_distances(galaxies)
    print("Part 1: %i" % sum(distances))
    galaxies = parse_galaxies(document_string, 1000000)
    distances = get_distances(galaxies)
    print("Part 2: %i" % sum(distances))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()
