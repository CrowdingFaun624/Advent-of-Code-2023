from pathlib2 import Path

def load_document(name:str) -> str:
    if isinstance(name, str):
        name = parent_path.joinpath(name)
    path = Path(name)
    if parent_path not in path.parents:
        raise FileNotFoundError("File is not in the correct directory!")
    with open(path, "rt") as file:
        return file.read()

NORTH = 0
WEST = 1
SOUTH = 2
EAST = 3

class PositionedObject():
    def __init__(self, x:int, y:int) -> None:
        if not isinstance(x, int):
            raise TypeError("`x` is not an int!")
        if x < 0:
            raise ValueError("`x` is less than 0!")
        if not isinstance(y, int):
            raise TypeError("`y` is not an int!")
        if y < 0:
            raise ValueError("`y` is less than 0!")
        
        self.x = x
        self.y = y
    
    def __repr__(self) -> str:
        return "<%s at (%i, %i)>" % (self.__class__.__name__, self.x, self.y)

class RoundedRock(PositionedObject):
    def __str__(self) -> str:
        return "O"

class CubicRock(PositionedObject):
    def __str__(self) -> str:
        return "#"

class Platform():
    def __init__(self, rounded_rocks:list[RoundedRock], cubic_rocks:list[CubicRock], width:int, height:int) -> None:
        if not isinstance(rounded_rocks, list):
            raise TypeError("`rounded_rocks` is not a list!")
        if any(not isinstance(rounded_rock, RoundedRock) for rounded_rock in rounded_rocks):
            raise TypeError("`rounded_rocks` has an item that is not a RoundedRock!")
        if len(rounded_rocks) == 0:
            raise ValueError("`rounded_rocks` is empty!")
        if not isinstance(cubic_rocks, list):
            raise TypeError("`cubic_rocks` is not a list!")
        if any(not isinstance(cubic_rock, CubicRock) for cubic_rock in cubic_rocks):
            raise TypeError("`cubic_rocks` has an item that is not a CubicRock!")
        if len(cubic_rocks) == 0:
            raise ValueError("`cubic_rocks` is empty!")
        if not isinstance(width, int):
            raise TypeError("`width` is not an int!")
        if width <= 0:
            raise ValueError("`width` is less than or equal to 0!")
        if not isinstance(height, int):
            raise TypeError("`height` is not an int!")
        if height <= 0:
            raise ValueError("`height` is less than or equal to 0!")
        if len(rounded_rocks) + len(cubic_rocks) > width * height:
            raise ValueError("The length of `rounded_rocks` and `cubic_rocks` combined is greater than `width * height`!")
        
        self.rounded_rocks = rounded_rocks
        self.cubic_rocks = cubic_rocks
        self.width = width
        self.height = height
    
    def get_bitmap_grid(self) -> list[list[None|CubicRock|RoundedRock]]:
        position_dict:dict[tuple[int,int],CubicRock|RoundedRock] = {(rock.x, rock.y): rock for rock in self.cubic_rocks}
        position_dict.update({(rock.x, rock.y): rock for rock in self.rounded_rocks})
        output:list[list[None|CubicRock|RoundedRock]] = []
        for y in range(self.height):
            row:list[None|CubicRock|RoundedRock] = []
            for x in range(self.width):
                if (x, y) in position_dict:
                    row.append(position_dict[(x, y)])
                else:
                    row.append(None)
            output.append(row)
        return output
    
    def __repr__(self) -> str:
        return "<Platform %i×%i>" % (self.width, self.height)
    
    def __str__(self) -> str:
        return "\n".join("".join("." if rock is None else str(rock) for rock in row) for row in self.get_bitmap_grid())
    
    def shift_content(self, direction:int) -> "Platform":
        '''Moves all of the rounded rocks in the direction. Returns the Platform object.'''
        if direction is NORTH:
            rock_order = ((x, y) for x in range(self.width) for y in range(self.height))
            change_vector = (0, -1)
        elif direction is WEST:
            rock_order = ((x, y) for y in range(self.height) for x in range(self.width))
            change_vector = (-1, 0)
        elif direction is SOUTH:
            rock_order = ((x, y) for x in range(self.width) for y in range(self.height - 1, -1, -1))
            change_vector = (0, 1)
        elif direction is EAST:
            rock_order = ((x, y) for y in range(self.height) for x in range(self.width - 1, -1, -1))
            change_vector = (1, 0)
        else: raise RuntimeError()
        
        rounded_rock_dict = {(rock.x, rock.y): rock for rock in self.rounded_rocks}
        cubic_rock_dict = {(rock.x, rock.y): rock for rock in self.cubic_rocks}
        for rounded_rock_position in rock_order:
            # print(rounded_rock_position)
            if rounded_rock_position not in rounded_rock_dict: continue
            rounded_rock = rounded_rock_dict[rounded_rock_position]
            position = rounded_rock_position
            while True:
                new_position = (position[0] + change_vector[0], position[1] + change_vector[1])
                if new_position in cubic_rock_dict or new_position in rounded_rock_dict: break
                if new_position[0] < 0 or new_position[0] >= self.width or new_position[1] < 0 or new_position[1] >= self.height: break
                position = new_position
            del rounded_rock_dict[(rounded_rock.x, rounded_rock.y)]
            rounded_rock.x, rounded_rock.y = position
            rounded_rock_dict[(rounded_rock.x, rounded_rock.y)] = rounded_rock
        return self
    
    def get_north_load(self) -> None:
        load = 0
        for rounded_rock in self.rounded_rocks:
            load += self.height - rounded_rock.y
        return load
    
    def spin_cycle(self, count:int) -> int:
        '''Returns the north load after `count` number of spin cycles.'''
        indexes:dict[int,tuple[int,int]] = {} # {hash of platform: (cycle index, north load)}
        destinations:dict[int, int] = {} # {hash of current: hash of next}
        index = 0
        platform_hash = None
        while True:
            index += 1
            previous_hash = platform_hash
            self.shift_content(NORTH).shift_content(WEST).shift_content(SOUTH).shift_content(EAST)
            platform_hash = hash(str(self))
            if previous_hash is not None:
                destinations[previous_hash] = platform_hash
            if index == count: # This will never happen obviously but it will be faster if the count is very low.
                return self.get_north_load()
            if platform_hash in indexes:
                cycle_length = index - indexes[platform_hash][0]
                cycle_offset = (count - index) % cycle_length
                for i in range(cycle_offset):
                    platform_hash = destinations[platform_hash]
                return indexes[platform_hash][1]
            else:
                indexes[platform_hash] = (index, self.get_north_load())

def parse_platform(document:str) -> Platform:
    cubic_rocks:list[CubicRock] = []
    rounded_rocks:list[RoundedRock] = []
    for y, line in enumerate(document.split("\n")):
        for x, char in enumerate(line):
            if char == ".": continue
            elif char == "O": rounded_rocks.append(RoundedRock(x, y))
            elif char == "#": cubic_rocks.append(CubicRock(x, y))
    return Platform(rounded_rocks, cubic_rocks, x + 1, y + 1)

def main() -> None:
    document_string = load_document("Input.txt")
    platform = parse_platform(document_string)
    platform.shift_content(NORTH)
    print("Part 1: %i" % platform.get_north_load())
    print("Part 2: %i" % platform.spin_cycle(1000000000))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()
