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

EMPTY_SPACE = "."
FORWARD_MIRROR = "/"
BACKWARD_MIRROR = "\\"
VERTICAL_SPLITTER = "|"
HORIZONTAL_SPLITTER = "-"
MIRROR_CHARACTERS = [FORWARD_MIRROR, BACKWARD_MIRROR, VERTICAL_SPLITTER, HORIZONTAL_SPLITTER]

UP = 0
DOWN = 1
LEFT = 2
RIGHT = 3

class Mirror():
    def __init__(self, x:int, y:int, char:str) -> None:
        if not isinstance(x, int):
            raise TypeError("`x` is not an int!")
        if x < 0:
            raise ValueError("`x` is less than 0!")
        if not isinstance(y, int):
            raise TypeError("`y` is not an int!")
        if y < 0:
            raise ValueError("`y` is less than 0!")
        if not isinstance(char, str):
            raise TypeError("`char` is not a str!")
        if not any(char is mirror_character for mirror_character in MIRROR_CHARACTERS):
            raise ValueError("`char` is not a reference to any item in `MIRROR_CHARACTERS`!")
        
        self.x = x
        self.y = y
        self.char = char
    
    def __repr__(self) -> str:
        return "<Mirror %s at (%i, %i)>" % (self.char, self.x, self.y)
    def __str__(self) -> str:
        return self.char
    
    def beam_interaction(self, beam:"Beam") -> list["Beam"]:
        '''Modifies existing beams or creates new beams. Returns a list of beams.'''
        if self.char is FORWARD_MIRROR:
            if beam.direction is UP:
                beam.direction = RIGHT
            elif beam.direction is DOWN:
                beam.direction = LEFT
            elif beam.direction is LEFT:
                beam.direction = DOWN
            elif beam.direction is RIGHT:
                beam.direction = UP
            else: raise RuntimeError()
            return [beam]
        elif self.char is BACKWARD_MIRROR:
            if beam.direction is UP:
                beam.direction = LEFT
            elif beam.direction is DOWN:
                beam.direction = RIGHT
            elif beam.direction is LEFT:
                beam.direction = UP
            elif beam.direction is RIGHT:
                beam.direction = DOWN
            else: raise RuntimeError()
            return [beam]
        elif self.char is VERTICAL_SPLITTER:
            if beam.direction is UP or beam.direction is DOWN:
                return [beam]
            elif beam.direction is LEFT or beam.direction is RIGHT:
                beam.direction = UP
                new_beam = Beam(DOWN, beam.x, beam.y)
                return [beam, new_beam]
            else: raise RuntimeError()
        elif self.char is HORIZONTAL_SPLITTER:
            if beam.direction is UP or beam.direction is DOWN:
                beam.direction = LEFT
                new_beam = Beam(RIGHT, beam.x, beam.y)
                return [beam, new_beam]
            elif beam.direction is LEFT or beam.direction is RIGHT:
                return [beam]
            else: raise RuntimeError()
        else: raise RuntimeError()

class Beam():
    def __init__(self, direction:int, x:int, y:int) -> None:
        if not isinstance(direction, int):
            raise TypeError("`direction` is not an int!")
        if direction < 0 or direction > 3:
            raise ValueError("`direction` is less than 0 or greater than 3!")
        if not isinstance(x, int):
            raise TypeError("`x` is not an int!")
        if not isinstance(y, int):
            raise TypeError("`y` is not an int!")

        self.direction = direction
        self.x = x
        self.y = y
    
    def move(self, mirrors:dict[tuple[int,int],Mirror], width:int, height:int) -> list["Beam"]:
        if   self.direction is UP:    self.y -= 1
        elif self.direction is DOWN:  self.y += 1
        elif self.direction is LEFT:  self.x -= 1
        elif self.direction is RIGHT: self.x += 1
        else: raise RuntimeError()
        if (self.x, self.y) in mirrors:
            return mirrors[self.x, self.y].beam_interaction(self)
        elif self.x < 0 or self.x >= width or self.y < 0 or self.y >= height:
            return []
        else:
            return [self]

def parse_mirrors(document:str) -> tuple[list[Mirror],int,int]:
    mirrors:list[Mirror] = []
    for y, line in enumerate(document.split("\n")):
        for x, char in enumerate(line):
            if char == EMPTY_SPACE:
                pass
            elif char in MIRROR_CHARACTERS:
                mirrors.append(Mirror(x, y, MIRROR_CHARACTERS[MIRROR_CHARACTERS.index(char)])) # doing the weird index thing so it's a reference and I can use `is` later.
            else: raise RuntimeError("Invalid character \"%s\" at (%i, %i)" % (char, x, y))
    return mirrors, x + 1, y + 1

def bounce_beam(mirrors:list[Mirror], width:int, height:int, starting_position:tuple[int,int]=(-1, 0), starting_direction:int=RIGHT) -> set[tuple[int,int]]:
    '''Returns a set of energized tile positions.'''
    mirrors_dict = {(mirror.x, mirror.y): mirror for mirror in mirrors}
    beams = [Beam(starting_direction, starting_position[0], starting_position[1])]
    energized_tiles:set[tuple[int,int]] = set()
    cycle_memoization:set[tuple[int,int,int]] = set() # {(x, y, direction)}

    while len(beams) > 0:
        new_beams:list[Beam] = []
        for beam in beams:
            if (beam.x, beam.y, beam.direction) in cycle_memoization:
                continue # It has already been tracked.
            else:
                cycle_memoization.add((beam.x, beam.y, beam.direction))
            energized_tiles.add((beam.x, beam.y))
            new_beams.extend(beam.move(mirrors_dict, width, height))
        beams = new_beams
    
    energized_tiles.remove(starting_position)
    return energized_tiles

def all_beam_starting_positions(width:int, height:int) -> Generator[tuple[int,int,int],None,None]:
    yield from ((x, height, UP) for x in range(width))
    yield from ((x, -1, DOWN) for x in range(width))
    yield from ((width, y, LEFT) for y in range(height))
    yield from ((-1, y, RIGHT) for y in range(height))

def find_bounciest_beam(mirrors:list[Mirror], width:int, height:int) -> set[tuple[int,int]]:
    largest_set:set[tuple[int,int]] = None
    for start_x, start_y, start_direction in all_beam_starting_positions(width, height):
        this_set = bounce_beam(mirrors, width, height, (start_x, start_y), start_direction)
        if largest_set is None or len(this_set) > len(largest_set):
            largest_set = this_set
    if largest_set is None: raise RuntimeError()
    return largest_set

def main() -> None:
    document_string = load_document("Input.txt")
    mirrors, width, height = parse_mirrors(document_string)
    print("Part 1: %i" % len(bounce_beam(mirrors, width, height)))
    print("Part 2: %i" % len(find_bounciest_beam(mirrors, width, height)))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()
