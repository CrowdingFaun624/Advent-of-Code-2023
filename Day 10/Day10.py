from pathlib2 import Path
from typing import Any, TypeVar, Union

Flatten = TypeVar('Flatten')

def load_document(name:str) -> str:
    if isinstance(name, str):
        name = parent_path.joinpath(name)
    path = Path(name)
    if parent_path not in path.parents:
        raise FileNotFoundError("File is not in the correct directory!")
    with open(path, "rt") as file:
        return file.read()

def flatten(matrix:list[list[Flatten]]) -> list[Flatten]:
    return [item for row in matrix for item in row]

DIRECTION_NAMES = ["North", "East", "South", "West"]
DIRECTIONS:dict[str,tuple[bool,bool,bool,bool]] = {
    "|": (True, False, True, False),
    "-": (False, True, False, True),
    "L": (True, True, False, False),
    "J": (True, False, False, True),
    "7": (False, False, True, True),
    "F": (False, True, True, False),
    ".": (False, False, False, False)
}
REVERSED_DIRECTIONS = {value: key for key, value in DIRECTIONS.items()}
UNKNOWN_CHARACTERS = ["S"]
INTERNAL_QUADRANT_PROPAGATION:dict[str,list[tuple[int]]] = {
    "|": [(0, 3), (1, 2)],
    "-": [(0, 1), (2, 3)],
    "L": [(0,), (1, 2, 3)],
    "J": [(0, 2, 3), (1,)],
    "7": [(0, 1, 3), (2,)],
    "F": [(0, 1, 2), (3,)],
    ".": [(0, 1, 2, 3)]
}

class Pipe():
    def __init__(self, char:str, position:tuple[int,int]) -> None:
        if not isinstance(char, str):
            raise TypeError("`char` is not a str!")
        if len(char) != 1:
            raise ValueError("`char` is not a str with length 1!")
        if not isinstance(position, tuple):
            raise TypeError("`position` is not a tuple!")
        if len(position) != 2:
            raise ValueError("`position` is not a tuple with length 2!")
        if not all(isinstance(coordinate, int) for coordinate in position):
            raise TypeError("`position` has an item that is not an int!")
        
        self.char = char
        self.position = position
        self.unknown = self.char in UNKNOWN_CHARACTERS
        self.distance_from_start:int|None = None
        self.filled_quadrants = [False] * 4
        if not self.unknown:
            self.directions = DIRECTIONS[self.char]
        else:
            self.directions = None
        self.neighbors:tuple[Pipe|None,Pipe|None,Pipe|None,Pipe|None] = None
    
    def set_neighbors(self, pipes:list[list["Pipe"]]) -> None:
        '''Sets this Pipe's `neighbors` attribute, and the `directions` attribute if it is an unknown character.'''
        self.neighbors = [None, None, None, None]
        shape = (len(pipes[0]), len(pipes))
        if self.position[1] != 0:
            self.neighbors[0] = pipes[self.position[1]-1][self.position[0]]
        if self.position[0] != shape[0] - 1:
            self.neighbors[1] = pipes[self.position[1]][self.position[0]+1]
        if self.position[1] != shape[1] -1:
            self.neighbors[2] = pipes[self.position[1]+1][self.position[0]]
        if self.position[0] != 0:
            self.neighbors[3] = pipes[self.position[1]][self.position[0]-1]
        
        if self.unknown:
            self.unknown = False
            self.directions = [None, None, None, None]
            self.directions[0] = self.north_neighbor.south if self.north_neighbor is not None else False
            self.directions[1] = self.east_neighbor.west if self.east_neighbor is not None else False
            self.directions[2] = self.south_neighbor.north if self.south_neighbor is not None else False
            self.directions[3] = self.west_neighbor.east if self.west_neighbor is not None else False
            self.directions = tuple(self.directions)
            assert self.directions.count(True) == 2
    
    def follow(self, away:"Pipe") -> "Pipe":
        '''Returns the neighbor of this pipe that is not the `away` Pipe.'''
        for connected, neighbor in zip(self.directions, self.neighbors):
            if connected and neighbor is not away:
                return neighbor
        else:
            raise RuntimeError("Failed to follow %s away from %s!" % (repr(self), repr(away)))

    def fill_quadrants(self, *quadrants:int) -> None:
        output = not all(self.filled_quadrants[quadrant] for quadrant in quadrants)
        for quadrant in quadrants:
            self.filled_quadrants[quadrant] = True
        return output

    def propagate(self, next_pipes:set["Pipe"]) -> None:
        '''Sets the pipes propagated quadrants and neighboring pipes' adjacent quadrants.'''
        propagations = INTERNAL_QUADRANT_PROPAGATION[REVERSED_DIRECTIONS[self.directions]]
        for propagation in propagations:
            if any(self.filled_quadrants[index] for index in propagation):
                self.fill_quadrants(*propagation)
        if self.filled_quadrants[0]:
            if self.north_neighbor is not None and self.north_neighbor.fill_quadrants(3): next_pipes.add(self.north_neighbor)
            if self.east_neighbor is not None and self.east_neighbor.fill_quadrants(1): next_pipes.add(self.east_neighbor)
        if self.filled_quadrants[1]:
            if self.north_neighbor is not None and self.north_neighbor.fill_quadrants(2): next_pipes.add(self.north_neighbor)
            if self.west_neighbor is not None and self.west_neighbor.fill_quadrants(0): next_pipes.add(self.west_neighbor)
        if self.filled_quadrants[2]:
            if self.south_neighbor is not None and self.south_neighbor.fill_quadrants(1): next_pipes.add(self.south_neighbor)
            if self.west_neighbor is not None and self.west_neighbor.fill_quadrants(3): next_pipes.add(self.west_neighbor)
        if self.filled_quadrants[3]:
            if self.east_neighbor is not None and self.east_neighbor.fill_quadrants(2): next_pipes.add(self.east_neighbor)
            if self.south_neighbor is not None and self.south_neighbor.fill_quadrants(0): next_pipes.add(self.south_neighbor)

    @property
    def north(self) -> bool:
        return self.directions[0]
    @property
    def east(self) -> bool:
        return self.directions[1]
    @property
    def south(self) -> bool:
        return self.directions[2]
    @property
    def west(self) -> bool:
        return self.directions[3]
    @property
    def north_neighbor(self) -> Union["Pipe",None]:
        return self.neighbors[0]
    @property
    def east_neighbor(self) -> Union["Pipe",None]:
        return self.neighbors[1]
    @property
    def south_neighbor(self) -> Union["Pipe",None]:
        return self.neighbors[2]
    @property
    def west_neighbor(self) -> Union["Pipe",None]:
        return self.neighbors[3]

    def __repr__(self) -> str:
        return "<Pipe \"%s\" at (%i, %i)>" % (self.char, self.position[0], self.position[1])
    def __str__(self) -> str:
        return self.char
    def __hash__(self) -> int:
        return hash((self.position, self.char))

class Map():
    def __init__(self, pipes:list[list[Pipe]]) -> None:
        if not isinstance(pipes, list):
            raise TypeError("`pipes` is not an list!")
        if not all(isinstance(pipe_line, list) for pipe_line in pipes):
            raise TypeError("`pipes` has an item that is not a list!")
        if not all(all(isinstance(pipe, Pipe) for pipe in pipe_line) for pipe_line in pipes):
            raise TypeError("`pipes` has an item that has an item that is not a Pipe!")
        
        self.pipes = pipes
        self.shape = (len(pipes[0]), len(pipes))
        self.start_pipe:Pipe = None
        self.pipes_in_main_loop:set[Pipe] = None
        for pipe in flatten(self.pipes):
            if pipe.char == "S":
                self.start_pipe = pipe
                break
        else:
            raise ValueError("`pipes` has no Pipe with `char` \"S\"!")
    
    def __getitem__(self, x:int, y:int) -> Pipe:
        return self.pipes[x, y]
    
    def __repr__(self) -> str:
        return "<Map %i×%i>" % self.shape
    
    def print(self, highlight:set[tuple[int,int]], highlight_char:str) -> str:
        lines = []
        for y, pipe_line in enumerate(self.pipes):
            line = ""
            for x, pipe in enumerate(pipe_line):
                if (x, y) in highlight:
                    line += highlight_char
                else:
                    line += pipe.char
            lines.append(line)
        return "\n".join(lines)

    def __str__(self) -> str:
        return "\n".join("".join(str(pipe) for pipe in pipe_line) for pipe_line in self.pipes)

def parse_map(document:str) -> Map:
    pipes:list[list[Pipe]] = [[Pipe(pipe, (x, y)) for x, pipe in enumerate(pipe_line)] for y, pipe_line in enumerate(document.split("\n"))]
    for pipe in flatten(pipes):
        pipe.set_neighbors(pipes)
    return Map(pipes)

def follow_pipe_both(map:Map) -> set[Pipe]:
    '''Returns an set of Pipes such that all pipes are in the path of the starting Pipe.'''
    path_1_pipe = map.start_pipe
    path_2_pipe = map.start_pipe
    path_1_away = [neighbor for connected, neighbor in zip(map.start_pipe.directions, map.start_pipe.neighbors) if connected][0]
    path_2_away = [neighbor for connected, neighbor in zip(map.start_pipe.directions, map.start_pipe.neighbors) if connected][1]
    map.start_pipe.distance_from_start = 0
    visited_pipes:set[Pipe] = set()

    iterations = 0
    while path_1_pipe is not map.start_pipe or iterations == 0:
        visited_pipes.add(path_1_pipe)
        path_1_pipe, path_1_away = path_1_pipe.follow(path_1_away), path_1_pipe
        path_1_pipe.distance_from_start = min(path_1_pipe.distance_from_start, path_1_away.distance_from_start + 1) if path_1_pipe.distance_from_start is not None else path_1_away.distance_from_start + 1
        iterations += 1

    iterations = 0
    while path_2_pipe is not map.start_pipe or iterations == 0:
        visited_pipes.add(path_2_pipe)
        path_2_pipe, path_2_away = path_2_pipe.follow(path_2_away), path_2_pipe
        path_2_pipe.distance_from_start = min(path_2_pipe.distance_from_start, path_2_away.distance_from_start + 1) if path_2_pipe.distance_from_start is not None else path_2_away.distance_from_start + 1
        iterations += 1
    
    map.pipes_in_main_loop = visited_pipes
    return visited_pipes

def propagate_fill(map:Map) -> set[Pipe]:
    '''Returns the set of Pipes that are enclosed within the main loop of the Map.'''
    shape = map.shape
    current_pipes:set[Pipe] = set()
    for x in range(shape[0]):
        top_pipe = map.pipes[0][x]
        top_pipe.fill_quadrants(0, 1)
        current_pipes.add(top_pipe)
        bottom_pipe = map.pipes[shape[1]-1][x]
        bottom_pipe.fill_quadrants(2, 3)
        current_pipes.add(bottom_pipe)
    for y in range(shape[1]):
        left_pipe = map.pipes[y][0]
        left_pipe.fill_quadrants(1, 2)
        current_pipes.add(left_pipe)
        right_pipe = map.pipes[y][shape[0]-1]
        right_pipe.fill_quadrants(0, 3)
        current_pipes.add(right_pipe)
    flat_pipes = flatten(map.pipes)
    should_continue = True
    while should_continue:
        next_pipes:set[Pipe] = set()
        for pipe in current_pipes:
            pipe.propagate(next_pipes)
        current_pipes = next_pipes
        should_continue = len(current_pipes) > 0
    all_coords = {(x, y) for x in range(shape[0]) for y in range(shape[1])}
    outside_coords = {pipe.position for pipe in flat_pipes if any(pipe.filled_quadrants)}
    return all_coords - outside_coords
    

def main() -> None:
    document_string = load_document("Input.txt")
    map = parse_map(document_string)
    pipes_in_loop = follow_pipe_both(map)
    print("Part 1: %i" % max(pipe.distance_from_start for pipe in pipes_in_loop))
    enclosed_pipes = propagate_fill(map)
    print("Part 2: %i" % len(enclosed_pipes))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()
