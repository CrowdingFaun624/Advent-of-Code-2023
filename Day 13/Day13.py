from pathlib2 import Path
from typing import Any, Generator, Iterable, TypeVar

def load_document(name:str) -> str:
    if isinstance(name, str):
        name = parent_path.joinpath(name)
    path = Path(name)
    if parent_path not in path.parents:
        raise FileNotFoundError("File is not in the correct directory!")
    with open(path, "rt") as file:
        return file.read()

Flatten = TypeVar('Flatten')

def flatten(matrix:Iterable[Iterable[Flatten]]) -> Generator[Flatten, None, None]:
    return [item for row in matrix for item in row]

ASH = "."
ROCK = "#"

class Feature():
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
        if char not in (".", "#"):
            raise ValueError("`char` is not \".\" or \"#\"!")

        self.x = x
        self.y = y
        self.type = ASH if char == ASH else ROCK

    def __repr__(self) -> str:
        return "<Feature \"%s\" at %i, %i>" % (self.type, self.x, self.y)
    def __str__(self) -> str:
        return self.type
    def __eq__(self, __value:Any) -> bool:
        if isinstance(__value, Feature):
            return self.type is __value.type
        else:
            return NotImplemented

class Pattern():
    def __init__(self, width:int, height:int, features:list[Feature]) -> None:
        if not isinstance(width, int):
            raise TypeError("`width` is not an int!")
        if width <= 0:
            raise ValueError("`width` is less than or equal to 0!")
        if not isinstance(height, int):
            raise TypeError("`height` is not an int!")
        if height <= 0:
            raise ValueError("`height` is less than or equal to 0!")
        if not isinstance(features, list):
            raise TypeError("`features` is not a list!")
        if len(features) != width * height:
            raise ValueError("`features` is not length %i (width * height), but instead %i!!" % (width * height, len(features)))
        if any(not isinstance(feature, Feature) for feature in features):
            raise TypeError("`features` has an item that is not a Feature!")
        
        self.width = width
        self.height = height
        self.features = features
        self.feature_lines = self.get_lines()
        self.feature_positions = {(feature.x, feature.y): feature for feature in self.features}
    
    def get_lines(self) -> list[list[Feature]]:
        '''Separates the Features list into a list of rows.'''
        return [[self.features[index] for index in range(self.width * y, self.width * (y + 1))] for y in range(self.height)]

    def __repr__(self) -> str:
        return "<Pattern %i×%i>" % (self.width, self.height)
    def __str__(self) -> str:
        return "\n".join("".join(str(feature) for feature in line) for line in self.feature_lines)
    
    def get_mirror_position(self, position:tuple[int,int], axis:int, is_vertical:bool) -> tuple[int,int]|None:
        '''Returns the position mirrored across the given axis, or None if it is out of bounds.'''
        if is_vertical:
            new_position = (2 * axis - position[0] - 1, position[1])
        else:
            new_position = (position[0], 2 * axis - position[1] - 1)
        if new_position[0] < 0 or new_position[0] >= self.width or new_position[1] < 0 or new_position[1] >= self.height:
            return None
        else:
            return new_position
    
    def is_mirror_image(self, axis:int, is_vertical:int, smudges:bool) -> bool:
        if is_vertical: lower_side_is_smaller = axis <= (self.width // 2)
        else: lower_side_is_smaller = axis <= (self.height // 2)
        match is_vertical, lower_side_is_smaller:
            case True, True:
                test_features:Generator[Feature,None,None] = flatten((feature for feature in row[:axis]) for row in self.feature_lines)
            case True, False:
                test_features:Generator[Feature,None,None] = flatten((feature for feature in row[axis:]) for row in self.feature_lines)
            case False, True:
                test_features:Generator[Feature,None,None] = flatten(self.feature_lines[:axis])
            case False, False:
                test_features:Generator[Feature,None,None] = flatten(self.feature_lines[axis:])
            case _: raise RuntimeError # I need to do this or the type hinting doesn't work.
        smudge_count = 0
        for test_feature in test_features:
            mirror_position = self.get_mirror_position((test_feature.x, test_feature.y), axis, is_vertical)
            if mirror_position is None:
                raise RuntimeError("Attempted to reflect position (%i, %i) across %s axis %i on mirror:\n%s\n" %\
                                   (test_feature.x, test_feature.y, ("vertical" if is_vertical else "horizontal"), axis, str(self)))
            if test_feature != self.feature_positions[mirror_position]:
                if smudges:
                    smudge_count += 1
                    if smudge_count > 1: return False
                else:
                    return False
        if smudges:
            return smudge_count == 1
        else:
            return True
    
    def get_mirror_summary(self, smudges:bool) -> int:
        for vertical_axis in range(1, self.width):
            if self.is_mirror_image(vertical_axis, True, smudges):
                return vertical_axis
        for horizontal_axis in range(1, self.height):
            if self.is_mirror_image(horizontal_axis, False, smudges):
                return 100 * horizontal_axis
        raise RuntimeError("No mirror detected on the following mirror:\n%s\n" % str(self))

def parse_patterns(document:str) -> list[Pattern]:
    patterns:list[Pattern] = []
    for pattern_str in document.split("\n\n"):
        features:list[Feature] = []
        for y, line in enumerate(pattern_str.split("\n")):
            for x, char in enumerate(line):
                features.append(Feature(x, y, char))
        patterns.append(Pattern(x + 1, y + 1, features))
    return patterns

def main() -> None:
    document_string = load_document("Input.txt")
    patterns = parse_patterns(document_string)
    print("Part 1: %i" % sum(pattern.get_mirror_summary(smudges=False) for pattern in patterns))
    print("Part 2: %i" % sum(pattern.get_mirror_summary(smudges=True) for pattern in patterns))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()
