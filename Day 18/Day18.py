from collections import deque
from pathlib2 import Path
from typing import Generator

def load_document(name:str) -> str:
    if isinstance(name, str):
        name = parent_path.joinpath(name)
    path = Path(name)
    if parent_path not in path.parents:
        raise FileNotFoundError("File is not in the correct directory!")
    with open(path, "rt") as file:
        return file.read()

UP = "U"
DOWN = "D"
LEFT = "L"
RIGHT = "R"
DIRECTIONS:list[str] = [UP, DOWN, LEFT, RIGHT]
DIRECTION_VECTORS:dict[str,tuple[int,int]] = {UP: (0, -1), DOWN: (0, 1), LEFT: (-1, 0), RIGHT: (1, 0)}
DIRECTION_HEX_ENCODING:dict[str:str] = {"0": RIGHT, "1": DOWN, "2": LEFT, "3": UP}

class Instruction():
    def __init__(self, direction:str, distance:int) -> None:
        if not isinstance(direction, str):
            raise TypeError("`direction` is not a str!")
        if not any(direction is direction_reference for direction_reference in DIRECTIONS):
            raise ValueError("`direction` \"%s\" is not a reference to any direction in `DIRECTIONS`!")
        if not isinstance(distance, int):
            raise TypeError("`distance` is not an int!")
        if distance < 1:
            raise ValueError("`distance` is less than 1!")
        
        self.direction = direction
        self.distance = distance
    
    def __repr__(self) -> str:
        return "<Instruction %s %i>" % (self.direction, self.distance)
    def __str__(self) -> str:
        return "%s %i" % (self.direction, self.distance)

class DigPlan():
    def __init__(self, instructions:list[Instruction]) -> None:
        if not isinstance(instructions, list):
            raise TypeError("`instructions` is not a list!")
        if not all(isinstance(instruction, Instruction) for instruction in instructions):
            raise TypeError("An item of `instructions` is not an Instruction!")
        if len(instructions) == 0:
            raise ValueError("`instructions` is empty!")
        
        self.instructions = instructions
    
    def __repr__(self) -> str:
        return "<DigPlan len %i>" % len(self.instructions)
    
    def get_perimeter(self, path:list[tuple[int,int]]) -> int:
        total = sum(path[0])
        for node1, node2 in zip(path[:-1], path[1:]):
            distance = abs(node1[0] - node2[0]) + abs(node1[1] - node2[1])
            total += distance
        total += sum(path[-1])
        return total
    
    def get_instruction_circular(self, index:int, instructions:list[Instruction]) -> Instruction:
        return instructions[(index) % len(instructions)]

    def follow_instructions(self) -> tuple[list[tuple[int, int]]]:
        '''Returns multiple lists of positions that are in the border of the path at the turns.'''
        tiles_in_path:list[tuple[int,int]] = []
        OFFSETS = {
            (UP, LEFT, UP, True):        (0, 0, False), (UP, LEFT, UP, False):       (0, 0, True),
            (UP, LEFT, DOWN, True):      (-1, 0, True), (UP, LEFT, DOWN, False):     (1, 0, False),
            (UP, RIGHT, UP, True):       (0, 0, False), (UP, RIGHT, UP, False):      (0, 0, True),
            (UP, RIGHT, DOWN, True):     (1, 0, True),  (UP, RIGHT, DOWN, False):    (-1, 0, False),
            (DOWN, LEFT, UP, True):      (-1, 0, True), (DOWN, LEFT, UP, False):     (1, 0, False),
            (DOWN, LEFT, DOWN, True):    (0, 0, False), (DOWN, LEFT, DOWN, False):   (0, 0, True),
            (DOWN, RIGHT, UP, True):     (1, 0, True),  (DOWN, RIGHT, UP, False):    (-1, 0, False),
            (DOWN, RIGHT, DOWN, True):   (0, 0, False), (DOWN, RIGHT, DOWN, False):  (0, 0, True),
            (LEFT, UP, LEFT, True):      (0, 0, False), (LEFT, UP, LEFT, False):     (0, 0, True),
            (LEFT, UP, RIGHT, True):     (0, -1, True), (LEFT, UP, RIGHT, False):    (0, 1, False),
            (LEFT, DOWN, LEFT, True):    (0, 0, False), (LEFT, DOWN, LEFT, False):   (0, 0, True),
            (LEFT, DOWN, RIGHT, True):   (0, 1, True),  (LEFT, DOWN, RIGHT, False):  (0, -1, False),
            (RIGHT, UP, LEFT, True):     (0, -1, True), (RIGHT, UP, LEFT, False):    (0, 1, False),
            (RIGHT, UP, RIGHT, True):    (0, 0, False), (RIGHT, UP, RIGHT, False):   (0, 0, True),
            (RIGHT, DOWN, LEFT, True):   (0, 1, True),  (RIGHT, DOWN, LEFT, False):  (0, -1, False),
            (RIGHT, DOWN, RIGHT, True):  (0, 0, False), (RIGHT, DOWN, RIGHT, False): (0, 0, True)
        }
        convex = True
        x, y = 0, 0
        for index, instruction in enumerate(self.instructions):
            direction_vector = DIRECTION_VECTORS[instruction.direction]
            previous_direction = self.get_instruction_circular(index - 1, self.instructions).direction
            next_direction = self.get_instruction_circular(index + 1, self.instructions).direction
            offset_x, offset_y, convex = OFFSETS[(previous_direction, instruction.direction, next_direction, convex)]
            x += direction_vector[0] * instruction.distance + offset_x
            y += direction_vector[1] * instruction.distance + offset_y
            tiles_in_path.append((x, y))
        assert x == 0 and y == 0
        return tiles_in_path

    def circular_generator(self, path:list[tuple[int,int]]) -> Generator[tuple[int,int],None,None]:
        yield from ((position1, position2) for position1, position2 in zip(path[:-1], path[1:]))
        yield (path[-1], path[0])

    def get_area(self, path:tuple[list[tuple[int,int]]]) -> int:
        return abs(0.5 * sum(position1[0] * position2[1] - position2[0] * position1[1] for position1, position2 in self.circular_generator(path)))

def parse_dig_plan(document:str, reverse_colors:bool) -> DigPlan:
    instructions:list[Instruction] = []
    if reverse_colors:
        for line in document.split("\n"):
            _, _, color_str = line.split(" ")
            color_str = color_str.strip("(#)")  
            distance = int(color_str[:5], base=16)
            direction = color_str[5]
            assert direction in ("0", "1", "2", "3")
            instructions.append(Instruction(DIRECTION_HEX_ENCODING[direction], distance))
    else:
        for line in document.split("\n"):
            direction, distance, _ = line.split(" ")
            direction = DIRECTIONS[DIRECTIONS.index(direction)]
            distance = int(distance)
            instructions.append(Instruction(direction, distance))
    return DigPlan(instructions)

def main() -> None:
    document_string = load_document("Input.txt")
    dig_plan = parse_dig_plan(document_string, reverse_colors=False)
    path = dig_plan.follow_instructions()
    print("Part 1: %i" % dig_plan.get_area(path))
    dig_plan = parse_dig_plan(document_string, reverse_colors=True)
    path = dig_plan.follow_instructions()
    print("Part 2: %i" % dig_plan.get_area(path))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()