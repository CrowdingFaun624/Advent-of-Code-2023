from pathlib2 import Path

def load_document(name:str|Path) -> str:
    if isinstance(name, str):
        name = parent_path.joinpath(name)
    if parent_path not in name.parents:
        raise FileNotFoundError("File is not in the correct directory!")
    with open(name, "rt") as file:
        return file.read()

def parse_input(document:str) -> list[str]:
    lines = document.split("\n")
    if not all(line.isalnum() for line in lines):
        raise ValueError("Document does not contain only alpha-numeric characters and newlines!")
    return lines

def get_calibration_values1(lines:list[str]) -> list[int]:
    return [int((digits:=[char for char in line if char.isdigit()])[0] + digits[-1]) for line in lines]

def scan_string(string:str) -> str:
    DIGITS = [("one", "1"), ("two", "2"), ("three", "3"), ("four", "4"), ("five", "5"), ("six", "6"), ("seven", "7"), ("eight", "8"), ("nine", "9")]
    output:str = ""
    for char_index, char in enumerate(string):
        if char.isdigit(): output += char
        for old, new in DIGITS:
            if len(old) <= len(string) - char_index:
                if string[char_index:char_index + len(old)] == old:
                    output += new
                    break
    return output

def get_calibration_values2(lines:list[str]) -> list[int]:
    return [int((digits:=scan_string(line))[0] + digits[-1]) for line in lines]

def main() -> None:
    document_string = load_document("Input.txt")
    parsed_input = parse_input(document_string)
    calibration_values1 = get_calibration_values1(parsed_input)
    print("Part 1: %i" % sum(calibration_values1))
    calibration_values2 = get_calibration_values2(parsed_input)
    print("Part 2: %i" % sum(calibration_values2))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()
