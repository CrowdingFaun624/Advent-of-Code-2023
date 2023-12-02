from pathlib2 import Path
from typing import Iterable

def load_document(name:str) -> str:
    if isinstance(name, str):
        name = parent_path.joinpath(name)
    if parent_path not in name.parents:
        raise FileNotFoundError("File is not in the correct directory!")
    with open(name, "rt") as file:
        return file.read()

class ParserState():
    def __init__(self, string:str) -> None:
        self.index = 0
        self.string = string
    
    def increment(self, amount:int=1) -> None:
        self.index += amount
    
    def current_char(self) -> str|None:
        if self.index >= 0 and self.index < len(self.string):
            return self.string[self.index]
        else: return None
    
    def offset_char(self, offset:int) -> str|None:
        if self.index + offset >= 0 and self.index + offset < len(self.string):
            return self.string[self.index + offset]
        else: return None
    
    def next_matches(self, test_string:str) -> bool:
        '''Tests if `test_string` matches the following characters, starting at the current index.'''
        return self.string[self.index:self.index + len(test_string)] == test_string

def parse_game_id(state:ParserState) -> int:
    '''Parses "Game 1: ".'''
    if not state.next_matches("Game "):
        raise ValueError("Game ID container does not start with \"Game \"!")
    id_string = ""
    complete_id_string = False
    while state.index < len(state.string):
        if complete_id_string:
            if len(id_string) == 0:
                raise ValueError("Failed to find ID for a game!")
            else:
                if state.current_char().isdigit():
                    raise ValueError("Digit characters found after ID collection ended!")
                else:
                    if state.next_matches(": "):
                        state.increment(2)
                        return int(id_string)
                    else:
                        state.increment()
                        continue
        else:
            if state.current_char().isdigit():
                id_string += state.current_char()
                state.increment()
                continue
            else:
                if len(id_string) == 0:
                    state.increment()
                    continue
                else:
                    complete_id_string = True
                    # no increment
                    continue
    raise ValueError("Failed to return game ID before end of document!")

def parse_bag_pick(state:ParserState) -> tuple[str,int]:
    '''Parses "3 blue", returns `(color, amount)`.'''
    VALID_COLORS = ["red", "green", "blue"]
    amount_string = ""
    color_string = ""
    completed_amount_string = False
    while True:
        if completed_amount_string:
            if state.current_char() in (",", ";", "\n", None):
                if color_string not in VALID_COLORS:
                    raise ValueError("Color \"%s\" is not a valid color!" % color_string)
                return color_string, int(amount_string)
            elif state.current_char().isalpha():
                color_string += state.current_char()
                state.increment()
                continue
            else:
                raise ValueError("Color string is not alpha; encountered character \"%s\" at index %i!" % (state.current_char(), state.index))
        else:
            if state.current_char().isdigit():
                amount_string += state.current_char()
                state.increment()
                continue
            elif state.current_char() == " ":
                completed_amount_string = True
                state.increment()
            else:
                raise ValueError("Amount string is not digit!")
    raise ValueError("Encountered end of loop")

# import re
# # Game 1: 3 blue, 4 red; 1 red, 2 green, 6 blue; 2 green
# def parse_line(line: str): # -> tuple[int, list[tuple[int, str]]]:
#     parser = r"Game (\d+):(?: ?(?: ?(\d+) (\w+),?)+;?)+"
#     # "1 blue, 2 green"
#     matches = re.findall(parser, line)
#     print(matches)

def parse_round(state:ParserState) -> tuple[int,int,int]:
    '''Parses "3 blue, 4 red", returns `(red_amount, green_amount, blue_amount)`.'''
    COLOR_ORDER = ["red", "green", "blue"]
    bag_picks:dict[str,int] = {} # {color: amount}
    while state.index < len(state.string):
        bag_pick_color, bag_pick_amount = parse_bag_pick(state)
        bag_picks[bag_pick_color] = bag_pick_amount
        if state.current_char() in (";", "\n", None):
            bag_picks_output:list[int] = []
            for color in COLOR_ORDER:
                if color in bag_picks:
                    bag_picks_output.append(bag_picks[color])
                else:
                    bag_picks_output.append(0)
            return tuple(bag_picks_output)
        if not state.next_matches(", "):
            raise ValueError("Bag pick separator is not \", \"!")
        state.increment(2)
    raise ValueError("Encountered end of loop")

def parse_rounds(state:ParserState) -> list[tuple[int,int,int]]:
    '''Parses "3 blue, 4 red; 1 red, 2 green, 6 blue; 2 green", returns [(r, g, b), (r, g, b), (r, g, b)]'''
    rounds:list[tuple[int,int,int]] = []
    while state.index < len(state.string):
        rounds.append(parse_round(state))
        if state.current_char() in ("\n", None):
            return rounds
        if not state.next_matches("; "):
            raise ValueError("Round separator is not \"; \"!")
        state.increment(2)
    raise ValueError("Encountered end of loop")

def parse_input(document:str) -> dict[int,list[tuple[int,int,int]]]:
    games:dict[int, list[tuple[int,int,int]]] = {}
    state = ParserState(document)
    while state.index < len(state.string):
        game_id = parse_game_id(state)
        game_content = parse_rounds(state)
        games[game_id] = game_content
        state.increment()
    return games

def get_possible_game_ids(games:dict[int,list[tuple[int,int,int]]], maximum_allowed:tuple[int,int,int]) -> list[int]:
    '''Returns a list of game ids for games which have all rounds under their maximum values.'''
    output:list[int] = []
    for game_id, game_rounds in games.items():
        game_is_possible = True
        for round_index, round in enumerate(game_rounds):
            for round_amount, max_amount in zip(round, maximum_allowed):
                if round_amount > max_amount:
                    game_is_possible = False
                    break
            if not game_is_possible: break
        if game_is_possible:
            output.append(game_id)
    return output

def get_minimum_possible_cubes(games:dict[int,list[tuple[int,int,int]]]) -> dict[int,tuple[int,int,int]]:
    '''Returns a dictionary: `{ID: (minimum_r, minimum_g, minimum_b)}`'''
    output:dict[int,tuple[int,int,int]] = {}
    for game_id, game_rounds in games.items():
        minimum_cubes = [0] * 3
        for round in game_rounds:
            minimum_cubes = [max(current_minimum, this_rounds_cubes) for current_minimum, this_rounds_cubes in zip(minimum_cubes, round)]
        output[game_id] = tuple(minimum_cubes)
    return output

def product(numbers:Iterable[int|float]) -> int:
    '''Returns the product of all numbers in the input.'''
    output = 1
    for number in numbers:
        output *= number
    return output

def main() -> None:
    document_string = load_document("Input.txt")
    parsed_input = parse_input(document_string)
    possible_game_ids = get_possible_game_ids(parsed_input, (12, 13, 14))
    print("Part 1: %i" % sum(possible_game_ids))
    minimum_cubes = get_minimum_possible_cubes(parsed_input)
    print("Part 2: %i" % sum(product(game) for game in minimum_cubes.values()))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()
