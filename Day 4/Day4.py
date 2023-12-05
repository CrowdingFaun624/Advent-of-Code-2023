from pathlib2 import Path

def load_document(name:str) -> str:
    if isinstance(name, str):
        name = parent_path.joinpath(name)
    path = Path(name)
    if parent_path not in path.parents:
        raise FileNotFoundError("File is not in the correct directory!")
    with open(path, "rt") as file:
        return file.read()

def parse_cards(document:str) -> list[tuple[set[int],set[int]]]:
    output:list[tuple[set[int],set[int]]] = []
    for line in document.split("\n"):
        card_number, data = line.split(": ")
        set1_string, set2_string = data.split(" | ")
        set1 = {int(item.strip()) for item in set1_string.split(" ") if len(item) > 0}
        set2 = {int(item.strip()) for item in set2_string.split(" ") if len(item) > 0}
        output.append((set1, set2))
    return output

def get_points(cards:list[tuple[set[int],set[int]]]) -> list[int]:
    return [2**(len(intersection) - 1) if len(intersection := winning_numbers.intersection(my_numbers)) > 0 else 0 for winning_numbers, my_numbers in cards]

def get_card_copies(cards:list[tuple[set[int],set[int]]]) -> list[int]:
    '''Returns list of how many copies of each card are had (including first ones).'''
    copies = [1] * len(cards)
    for card_index, card in enumerate(cards):
        winning_numbers, my_numbers = card
        matching_amount = len(winning_numbers.intersection(my_numbers))
        for card_to_copy_index in range(card_index + 1, card_index + matching_amount + 1):
            copies[card_to_copy_index] += copies[card_index]
    return copies

def main() -> None:
    document_string = load_document("Input.txt")
    cards = parse_cards(document_string)
    card_points = get_points(cards)
    print("Part 1: %i" % sum(card_points))
    card_copies = get_card_copies(cards)
    print("Part 2: %i" % sum(card_copies))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()