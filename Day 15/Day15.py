from pathlib2 import Path
from typing import Any, Generator

def load_document(name:str) -> str:
    if isinstance(name, str):
        name = parent_path.joinpath(name)
    path = Path(name)
    if parent_path not in path.parents:
        raise FileNotFoundError("File is not in the correct directory!")
    with open(path, "rt") as file:
        return file.read()

def holiday_hash(init_sequence:str) -> int:
    current_value = 0
    for char in init_sequence:
        current_value += ord(char)
        current_value *= 17
        current_value %= 256
    return current_value

REMOVAL = 0
INSERTION = 1

class Lens():
    def __init__(self, focal_length:int, label:str) -> None:
        if not isinstance(focal_length, int):
            raise TypeError("`focal_length` is not an int!")
        if focal_length < 1 or focal_length > 9:
            raise ValueError("`focal_length` is less than 0 or greater than 9!")
        if not isinstance(label, str):
            raise TypeError("`label` is not an int!")
        if len(label) == 0:
            raise ValueError("`label` is empty!")
        if not label.isalpha():
            raise ValueError("`label` is not alpha!")

        self.focal_length = focal_length
        self.label = label
    
    def __repr__(self) -> str:
        return "<Lens %s %i>" % (self.label, self.focal_length)
    def __str__(self) -> str:
        return "[%s %i]" % (self.label, self.focal_length)

class Box():
    def __init__(self, id:int) -> None:
        self.id = id
        self.lenses:list[Lens] = []
    
    def __repr__(self) -> str:
        return "<Box %i count %i>" % (self.id, len(self.lenses))
    def __str__(self) -> str:
        return "Box %i: %s" % (self.id, " ".join(str(lens) for lens in self.lenses))
    
    def __contains__(self, __value:Any) -> bool:
        if isinstance(__value, str):
            return any(__value == lens.label for lens in self.lenses)
        else:
            raise NotImplementedError
    def index(self, __value:str) -> int:
        for index, lens in enumerate(self.lenses):
            if lens.label == __value: return index
        raise IndexError("Failed to find %s in %s!" % (__value, repr(self)))

class Instruction():
    def __init__(self, label:str, instruction_type:int, focal_length:int|None) -> None:
        if not isinstance(label, str):
            raise TypeError("`label` is not a str!")
        if len(label) == 0:
            raise ValueError("`label` is empty!")
        if not label.isalpha():
            raise ValueError("`label` is not alpha!")
        if not isinstance(instruction_type, int):
            raise TypeError("`instruction_type` is not an int!")
        if instruction_type not in (INSERTION, REMOVAL):
            raise ValueError("`instruction_type` is not an insertion or removal!")
        if instruction_type is REMOVAL:
            if focal_length is not None:
                raise TypeError("`focal_length` is not None while `instruction_type` is removal!")
        else:
            if not isinstance(focal_length, int):
                raise TypeError("`focal_length` is not an int while `instruction_type` is insertion!")
            if focal_length < 1 or focal_length > 9:
                raise ValueError("`focal_length` is less than 1 or greater than 9!")
        
        self.label = label
        self.type = instruction_type
        self.focal_length = focal_length

        self.label_hash = holiday_hash(self.label)
    
    def __repr__(self) -> str:
        return "<Instruction %s>" % str(self)
    def __str__(self) -> str:
        if self.type is REMOVAL:
            return "%s-" % self.label
        else:
            return "%s=%i" % (self.label, self.focal_length)

def parse_sequence(document:str) -> list[str]:
    return [item.replace("\n", "") for item in document.split(",")]

def parse_instructions(document:str) -> list[Instruction]:
    instructions:list[Instruction] = []
    for instruction_str in document.split(","):
        instruction_str = instruction_str.replace("\n", "")
        label = instruction_str.split("-")[0].split("=")[0]
        instruction_type = REMOVAL if "-" in instruction_str else INSERTION
        if instruction_type is REMOVAL:
            focal_length = None
        else:
            focal_length = int(instruction_str.split("=")[1])
        instructions.append(Instruction(label, instruction_type, focal_length))
    return instructions

def print_relevant_boxes(boxes:list[Box]) -> None:
    '''Prints boxes that have at least one lens.'''
    for box in boxes:
        if len(box.lenses) > 0:
            print(str(box))

def initialize_boxes(instructions:list[Instruction], print_debug_messages:bool=False) -> list[Box]:
    '''Executes the Instructions on a new list of Boxes.'''
    boxes = [Box(index) for index in range(256)]
    for instruction in instructions:
        box = boxes[instruction.label_hash]
        if instruction.type is INSERTION:
            lens = Lens(instruction.focal_length, instruction.label)
            if instruction.label in box:
                box.lenses[box.index(instruction.label)] = lens
            else:
                box.lenses.append(lens)
        elif instruction.type is REMOVAL:
            if instruction.label in box:
                del box.lenses[box.index(instruction.label)]
            else:
                pass
        else: raise RuntimeError()
        if print_debug_messages:
            print("After \"%s\":" % str(instruction))
            print_relevant_boxes(boxes)
    return boxes

def get_focusing_powers(boxes:list[Box]) -> Generator[int,None,None]:
    for box in boxes:
        for lense_index, lens in enumerate(box.lenses):
            yield (box.id + 1) * (lense_index + 1) * lens.focal_length

def main() -> None:
    document_string = load_document("Input.txt")
    sequences = parse_sequence(document_string)
    print("Part 1: %i" % sum(holiday_hash(sequence) for sequence in sequences))
    instructions = parse_instructions(document_string)
    boxes = initialize_boxes(instructions)
    print("Part 2: %i" % sum(get_focusing_powers(boxes)))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()
# I totally know how to spell lens
