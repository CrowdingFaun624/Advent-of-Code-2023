from pathlib2 import Path

def load_document(name:str) -> str:
    if isinstance(name, str):
        name = parent_path.joinpath(name)
    path = Path(name)
    if parent_path not in path.parents:
        raise FileNotFoundError("File is not in the correct directory!")
    with open(path, "rt") as file:
        return file.read()

class Number():
    def __init__(self, amount:int, positions:list[tuple[int,int]]) -> None:
        if not isinstance(amount, int):
            raise TypeError("`amount` is not an int!")
        if amount <= 0:
            raise ValueError("`amount` is less than or equal to 0!")
        if not isinstance(positions, list):
            raise TypeError("`positions` is not a list1")
        if not all(isinstance(position, tuple) for position in positions):
            raise TypeError("A position in `positions` is not a tuple!")
        if len(positions) == 0:
            raise ValueError("`positions` is length 0!")
        if not all(len(position) == 2 for position in positions):
            raise ValueError("A position in `positions` is not length 2!")
        
        self.amount = amount
        self.positions = positions
        self.adjacent_symbols:list[Symbol] = []
    
    def get_adjacent_spaces(self, dimensions:tuple[int,int]) -> list[tuple[int,int]]:
        adjacent_positions:set[tuple[int,int]] = set()
        for x, y in self.positions:
            adjacent_positions.update([(x+1,y+1),(x+1,y),(x+1,y-1),(x,y+1),(x,y-1),(x-1,y+1),(x-1,y),(x-1,y-1)])
        return sorted(position for position in adjacent_positions if position[0] >= 0 and position[0] < dimensions[0] and position[1] >= 0 and position[1] < dimensions[1])
    
    def __repr__(self) -> str:
        return "<Number %i at %s-%s>" % (self.amount, self.positions[0], self.positions[-1])

class Symbol():
    def __init__(self, symbol:str, position:tuple[int,int]) -> None:
        self.symbol = symbol
        self.position = position
        self.adjacent_numbers:list[Number] = []
    
    def __repr__(self) -> str:
        return "<Symbol \"%s\" at %s>" % (self.symbol, self.position)

class Schematic():
    def __init__(self, document_string:str) -> None:
        self.document_string = document_string
        self.numbers:list[Number] = []
        self.symbols:list[Symbol] = []
        self.dimensions:tuple[int,int] = None
    
    def parse(self) -> None:
        '''Sets this Schematic's numbers and symbols.'''
        current_digits = ""
        current_digit_positions:list[tuple[int,int]] = []
        for y, line in enumerate(self.document_string.split("\n")):
            for x, char in enumerate(line):
                if char == ".":
                    if len(current_digits) > 0:
                        self.numbers.append(Number(int(current_digits), current_digit_positions))
                        current_digits = ""
                        current_digit_positions = []
                elif char.isdigit():
                    current_digits += char
                    current_digit_positions.append((x, y))
                else:
                    if len(current_digits) > 0:
                        self.numbers.append(Number(int(current_digits), current_digit_positions))
                        current_digits = ""
                        current_digit_positions = []
                    self.symbols.append(Symbol(char, (x, y)))
            if len(current_digits) > 0:
                self.numbers.append(Number(int(current_digits), current_digit_positions))
                current_digits = ""
                current_digit_positions = []
        self.dimensions = (x+1, y+1)
    
    def get_symbol_adjacent_numbers(self) -> list[Number]:
        output:list[Number] = []
        for number in self.numbers:
            adjacent_positions = number.get_adjacent_spaces(self.dimensions)
            for symbol in self.symbols:
                if symbol.position in adjacent_positions:
                    output.append(number)
                    number.adjacent_symbols.append(symbol)
                    symbol.adjacent_numbers.append(number)
        return output
    
    def get_gear_ratios(self) -> list[int]:
        GEAR_SYMBOL = "*"
        output:list[int] = []
        for symbol in self.symbols:
            if symbol.symbol == GEAR_SYMBOL and len(symbol.adjacent_numbers) == 2:
                output.append(symbol.adjacent_numbers[0].amount * symbol.adjacent_numbers[1].amount)
            else:
                continue
        return output

def get_debug_report(numbers:list[Number], store_in_file:bool=True) -> False:
    report = ""
    for number in numbers:
        if len(number.adjacent_symbols) == 0:
            report += "%i is not adjacent to a symbol.\n" % number.amount
        else:
            report += "%i is adjacent to \"%s\"\n" % (number.amount, number.adjacent_symbols)
    if store_in_file:
        with open("./Day 3/debug_report.txt", "wt") as f:
            f.write(report)

def main() -> None:
    document_string = load_document("Input.txt")
    schematic = Schematic(document_string)
    schematic.parse()
    symbol_adjacent_numbers = schematic.get_symbol_adjacent_numbers()
    # get_debug_report(schematic.numbers)
    print("Part 1: %i" % sum(number.amount for number in symbol_adjacent_numbers))
    gear_ratios = schematic.get_gear_ratios()
    print("Part 2: %i" % sum(gear_ratios))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()
