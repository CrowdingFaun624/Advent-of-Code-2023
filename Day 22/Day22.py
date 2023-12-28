from enum import Enum
import math
from pathlib2 import Path
from typing import Literal

def load_document(name:str) -> str:
    if isinstance(name, str):
        name = parent_path.joinpath(name)
    path = Path(name)
    if parent_path not in path.parents:
        raise FileNotFoundError("File is not in the correct directory!")
    with open(path, "rt") as file:
        return file.read()

class Axis(Enum):
    x = 0
    y = 1
    z = 2

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

class Brick():
    def __init__(self, index:int, x1:int, y1:int, z1:int, x2:int, y2:int, z2:int) -> None:
        if not isinstance(index, int):
            raise TypeError("`index` is not an int!")
        if index < 0:
            raise ValueError("`index` is less than 0!")
        type_checking:list[tuple[str,int]] = [("x1", x1), ("y1", y1), ("z1", z1), ("x2", x2), ("y2", y2), ("z2", z2)]
        for label, value in type_checking:
            if not isinstance(value, int):
                raise TypeError("`%s` is not an int!" % label)
            if label.startswith("z"):
                if value < 1:
                    raise ValueError("`%s` is less than 1!" % label)
            elif value < 0:
                raise ValueError("`%s` is less than 0!" % label)
        if (x1 == x2, y1 == y2, z1 == z2).count(False) > 1:
            raise ValueError("Brick `%i,%i,%i~%i,%i,%i` is not a line!" % (x1, y1, z1, x2, y2, z2))
        type_checking:list[tuple[str,str,int,int]] = [("x1", "x2", x1, x2), ("y1", "y2", y1, y2), ("z1", "z2", z1, z2)]
        for label1, label2, value1, value2 in type_checking:
            if value1 > value2:
                raise ValueError("`%s` is greater than `%s`!" % (label1, label2))

        self.index = index
        self.x1 = x1
        self.y1 = y1
        self.z1 = z1
        self.x2 = x2
        self.y2 = y2
        self.z2 = z2
        self.length = max(abs(value) for value in (x2 - x1, y2 - y1, z2 - z1)) + 1
        self.axis = Axis.x if x1 != x2 else (Axis.y if y1 != y2 else Axis.z)
        self.__iter_index = 0
        self.supported_by:list[Brick] = []
        self.supports:list[Brick] = []

    def fall(self, amount:int=1) -> int:
        '''Lowers each z coord of this brick by `amount`, and returns the lowest point of the brick.'''
        self.z1 -= amount
        self.z2 -= amount
        return self.z1

    def __hash__(self) -> int:
        return hash((self.x1, self.y1, self.z1, self.x2, self.y2, self.z2))

    def __gt__(self, other:object) -> bool:
        if isinstance(other, Brick):
            return self.z1 > other.z1
        else:
            return NotImplemented

    def __repr__(self) -> str:
        return "<Brick %i axis %s>" % (self.index, "xyz"[self.axis.value])
    def __str__(self) -> str:
        return "%i,%i,%i~%i,%i,%i" % (self.x1, self.y1, self.z1, self.x2, self.y2, self.z2)
    
    def __len__(self) -> int:
        return self.length
    
    def __iter__(self) -> "Brick":
        self.__iter_index = 0
        return self
    def __next__(self) -> tuple[int,int,int]:
        if self.__iter_index >= self.length:
            raise StopIteration
        else:
            result = [self.x1, self.y1, self.z1]
            result[self.axis.value] += self.__iter_index
            self.__iter_index += 1
            return tuple(result)

def str_perspective(bricks:list[Brick], axis:Literal[Axis.x, Axis.y]) -> str:
    def flatten_coords(x:int, y:int, z:int) -> tuple[int,int]:
        if axis is Axis.x:
            return x, z
        else:
            return y, z
    if axis is not Axis.x and axis is not Axis.y:
        raise ValueError("`perspective` is not `Axis.x` or `Axis.y`!")
    opposite_axis = Axis.y if axis is Axis.x else Axis.x
    max_x = max(brick.x2 for brick in bricks)
    max_y = max(brick.y2 for brick in bricks)
    max_z = max(brick.z2 for brick in bricks)
    width = max_x if axis == "x" else max_y
    height = max_z

    char_list = [["." for x in range(width + 1)] for y in range(height + 1)]
    for brick in bricks:
        if brick.axis is opposite_axis:
            coords = [flatten_coords(brick.x1, brick.y1, brick.z1)]
        else:
            coords = [flatten_coords(x, y, z) for x, y, z in brick]
        for x, y in coords:
            char = char_list[y][x]
            if char == ".":
                char_list[y][x] = ALPHABET[brick.index % 26]
            elif char == "?":
                pass
            else:
                char_list[y][x] = "?"
    
    char_list[0] = "-" * (width + 1)
    x_digit_space = int(math.log10(max_x)) + 1
    y_digit_space = int(math.log10(max_y)) + 1
    vertical_digit_space = z_digit_space = int(math.log10(max_z)) + 1
    horizontal_digit_space = x_digit_space if axis is Axis.x else y_digit_space
    output = ""
    output += " " * (width // 2) + "xy"[axis.value] + "\n"
    horizontal_strings = list(map(str, range(width + 1)))
    for horizontal_space in range(horizontal_digit_space):
        for digit_string in horizontal_strings:
            if horizontal_space >= horizontal_digit_space - len(digit_string):
                output += digit_string[horizontal_space]
            else:
                output += " "
        output += "\n"
    for line_index, line in enumerate(reversed(char_list)):
        output += "".join(line) + " " + str(height - line_index)
        if line_index == (height - 1) // 2:
            output += " " * (vertical_digit_space - len(str(height - line_index))) + " z"
        if line_index != height:
            output += "\n"
    return output

def parse_bricks(document:str) -> list[Brick]:
    bricks:list[Brick] = []
    for index, line in enumerate(document.split("\n")):
        end1_str, end2_str = line.split("~")
        x1, y1, z1 = map(int, end1_str.split(","))
        x2, y2, z2 = map(int, end2_str.split(","))
        bricks.append(Brick(index, x1, y1, z1, x2, y2, z2))
    return bricks

def fall_bricks(bricks:list[Brick]) -> None:
    '''Modifies the Bricks within `bricks`.'''
    sorted_bricks = sorted(bricks)
    max_x = max(brick.x2 for brick in bricks)
    max_y = max(brick.y2 for brick in bricks)

    highest_coords = {(x, y): 0 for x in range(max_x + 1) for y in range(max_y + 1)} # highest surface for each horizontal coordinate
    for brick in sorted_bricks:
        if brick.axis is Axis.z: # The lowest coord(s) of the brick, for use in collision detection.
            lowest_coords = [(brick.x1, brick.y1)]
        else:
            lowest_coords = [(x, y) for x, y, z in brick]
        while not any(brick.z1 - 1 == highest_coords[x, y] for x, y in lowest_coords):
            brick.fall()
        for lowest_coord in lowest_coords:
            highest_coords[lowest_coord] = brick.z2

def get_bricks_that_would_fall(brick:Brick, disintegrated_bricks:set[Brick]=None) -> list[Brick]:
    if disintegrated_bricks is None: disintegrated_bricks = set()
    output:list[Brick] = []
    disintegrated_bricks.add(brick)
    for supports_brick in brick.supports:
        true_supported_by_length = sum(1 for supported_by_brick in supports_brick.supported_by if supported_by_brick not in disintegrated_bricks)
        # `true_supported_by_length` is how many bricks are remaining holding this brick up.
        if true_supported_by_length < 1:
            output.append(supports_brick)
            output.extend(get_bricks_that_would_fall(supports_brick, disintegrated_bricks))
    return output

def get_disintegratable_bricks(bricks:list[Brick], debug_mode:bool=False) -> tuple[list[Brick],dict[Brick,list[Brick]]]:
    '''Returns the Bricks that are disintegratable and how many bricks would fall for each Brick.'''
    brick_coords:dict[tuple[int,int,int],Brick] = {}
    for brick in bricks:
        brick_coords.update({(x, y, z): brick for x, y, z in brick})
    for brick in bricks:
        if brick.axis is Axis.z:
            lowest_coords = [(brick.x1, brick.y1, brick.z1)]
        else:
            lowest_coords = brick
        for x, y, z in lowest_coords:
            if (x, y, z - 1) in brick_coords:
                lower_brick = brick_coords[x, y, z - 1]
                if lower_brick not in brick.supported_by:
                    brick.supported_by.append(lower_brick)
                if brick not in lower_brick.supports:
                    lower_brick.supports.append(brick)
    
    disintegratable_bricks:list[Brick] = []
    undisintegratable_bricks:list[Brick] = []
    for brick in bricks:
        if all(len(supports_brick.supported_by) >= 2 for supports_brick in brick.supports):
            disintegratable_bricks.append(brick)
            if debug_mode:
                if len(brick.supports) == 0:
                    print("Brick %i (\"%s\") can be disintegrated because there are no bricks on top of it." % (brick.index, str(brick)))
                else:
                    print("Brick %i (\"%s\") can be disintegrated because the bricks that are on top of it (%s) are supported by %s." %\
                          (brick.index, str(brick), [supports_brick.index for supports_brick in brick.supports], [[supported_by_brick.index for supported_by_brick in supports_brick.supported_by] for supports_brick in brick.supports]))
        else:
            undisintegratable_bricks.append(brick)
            if debug_mode:
                print("Brick %i (\"%s\") can not be disintegrated because bricks %s would fall." %\
                      (brick.index, str(brick), [supports_brick.index for supports_brick in brick.supports if len(supports_brick.supported_by) == 1]))
    
    chain_reactions = {brick: [] for brick in bricks}
    for brick in undisintegratable_bricks:
        chain_reactions[brick] = get_bricks_that_would_fall(brick)

    return disintegratable_bricks, chain_reactions

def main() -> None:
    document_string = load_document("Input.txt")
    bricks = parse_bricks(document_string)
    fall_bricks(bricks)
    disintegratable_bricks, chain_reactions = get_disintegratable_bricks(bricks)
    print("Part 1: %i" % len(disintegratable_bricks))
    print("Part 2: %i" % sum(len(chain) for chain in chain_reactions.values()))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()
