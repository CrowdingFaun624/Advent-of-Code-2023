from pathlib import Path

def load_document(name:str) -> str:
    if isinstance(name, str):
        name = parent_path.joinpath(name)
    path = Path(name)
    if parent_path not in path.parents:
        raise FileNotFoundError("File is not in the correct directory!")
    with open(path, "rt") as file:
        return file.read()

class History():
    def __init__(self, values:list[int]) -> None:
        self.values:list[list[int]] = [values]
        while not all(value == 0 for value in self.values[-1]):
            self.get_differences()
    
    def __repr__(self) -> str:
        if len(self.values) > 0:    
            return "<History w: %i h: %i>" % (len(self.values[0]), len(self.values))
        else:
            return "<History (incomplete)>"
    
    def __str__(self) -> str:
        longest_value = max(max(len(str(value)) for value in line) for line in self.values) + 1
        str_lines:list[str] = []
        for line_index, line in enumerate(self.values):
            str_line = " " * int(longest_value * line_index / 2)
            for value in line:
                str_value = str(value)
                str_line += str_value
                str_line += " " * (longest_value - len(str_value))
            str_lines.append(str_line)
        return "\n".join(str_lines)
    
    def get_differences(self) -> None:
        '''Fills in the next layer down in the values.'''
        new_values:list[int] = []
        value_layer = self.values[-1]
        for current_value, next_value in zip(value_layer[:-1], value_layer[1:]):
            new_values.append(next_value - current_value)
        self.values.append(new_values)
    
    def predict_next_value(self) -> None:
        '''Appends a value to each layer of the History.'''
        self.values[-1].append(0)
        lines = self.values[-1::-1]
        for bottom_line, top_line in zip(lines[:-1], lines[1:]):
            top_value = top_line[-1]
            bottom_value = bottom_line[-1]
            top_line.append(top_value + bottom_value)
    
    def predict_previous_value(self) -> None:
        # I know that inserting at 0 is an O(n) operation, it just does not take long enough for me to care.
        self.values[-1].insert(0, 0)
        lines = self.values[-1::-1]
        for bottom_line, top_line in zip(lines[:-1], lines[1:]):
            top_value = top_line[0]
            bottom_value = bottom_line[0]
            top_line.insert(0, top_value - bottom_value)

def parse_histories(document:str) -> list[History]:
    return [History([int(value) for value in line.split(" ")]) for line in document.split("\n")]

def main() -> None:
    document_string = load_document("Input.txt")
    histories = parse_histories(document_string)
    for history in histories: history.predict_next_value()
    print("Part 1: %i" % sum(history.values[0][-1] for history in histories))
    for history in histories: history.predict_previous_value()
    print("Part 2: %i" % sum(history.values[0][0] for history in histories))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()
