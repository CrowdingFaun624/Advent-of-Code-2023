from typing import Any
from pathlib2 import Path

def load_document(name:str) -> str:
    if isinstance(name, str):
        name = parent_path.joinpath(name)
    path = Path(name)
    if parent_path not in path.parents:
        raise FileNotFoundError("File is not in the correct directory!")
    with open(path, "rt") as file:
        return file.read()

CARDS_TAME = list("AKQJT98765432")
CARD_TAME_ORDER = {card: index for index, card in enumerate(reversed(CARDS_TAME))}
CARDS_WILD = list("AKQT98765432J")
CARD_WILD_ORDER = {card: index for index, card in enumerate(reversed(CARDS_WILD))}

class HandType():
    def __init__(self, name:str, value:int) -> None:
        self.name = name
        self.value = value
    
    def __gt__(self, other_type:"HandType") -> bool:
        return self.value > other_type.value
    def __lt__(self, other_type:"HandType") -> bool:
        return self.value < other_type.value
    def __eq__(self, other_type:"HandType") -> bool:
        return self.value == other_type.value
    
    def __repr__(self) -> str:
        return "<HandType %s>" % self.name
    def __str__(self) -> str:
        return self.name

FIVE_HAND = HandType("five_of_a_kind", 7)
FOUR_HAND = HandType("four_of_a_kind", 6)
FULL_HAND = HandType("full_house", 5)
THREE_HAND = HandType("three_of_a_kind", 4)
TWO_HAND = HandType("two_pair", 3)
ONE_HAND = HandType("one_pair", 2)
HIGH_HAND = HandType("high_card", 1)

class Hand():
    def __init__(self, cards:str, bid:int, is_wild:bool, possible_cards:list[str], card_order:dict[str,int]) -> None:
        if not isinstance(cards, str):
            raise TypeError("`cards` is not a str!")
        if len(cards) != 5:
            raise ValueError("`cards` is not length 5!")
        if not isinstance(bid, int):
            raise TypeError("`bid` is not an int!")
        if bid <= 0:
            raise ValueError("`bid` is less than or equal to 0!")
        
        self.cards = cards
        self.bid = bid
        self.is_wild = is_wild
        self.possible_cards = possible_cards
        self.card_order = card_order
        self.hand_type:HandType = None
        self.assign_hand_type()
    
    def manipulate_counts_wildly(self, counts:list[int]) -> list[int]:
        labeled_counts = {card: amount for card, amount in zip(self.possible_cards, counts)}
        joker_count = labeled_counts["J"]
        if joker_count == 0:
            return counts
        highest_count_card = None
        highest_count_amount = 0
        for card, amount in labeled_counts.items():
            if amount >= highest_count_amount and card != "J":
                highest_count_card = card
                highest_count_amount = amount
        new_labeled_counts = labeled_counts.copy()
        new_labeled_counts["J"] = 0
        new_labeled_counts[highest_count_card] = joker_count + highest_count_amount
        return list(new_labeled_counts.values())

    def assign_hand_type(self) -> None:
        counts = [self.cards.count(card) for card in self.possible_cards]
        if self.is_wild:
            counts = self.manipulate_counts_wildly(counts)
        if 5 in counts:
            self.hand_type = FIVE_HAND
        elif 4 in counts:
            self.hand_type = FOUR_HAND
        elif 3 in counts and 2 in counts:
            self.hand_type = FULL_HAND
        elif 3 in counts:
            self.hand_type = THREE_HAND
        elif counts.count(2) == 2:
            self.hand_type = TWO_HAND
        elif counts.count(2) == 1:
            self.hand_type = ONE_HAND
        else:
            self.hand_type = HIGH_HAND

    def __lt__(self, other_hand:"Hand") -> bool:
        if self.hand_type is other_hand.hand_type:
            for self_card, other_card in zip(self.cards, other_hand.cards):
                if self.card_order[self_card] > self.card_order[other_card]:
                    return True
                elif self.card_order[self_card] < self.card_order[other_card]:
                    return False
            else:
                return False
        if other_hand.hand_type < self.hand_type:
            return True
        elif other_hand.hand_type > self.hand_type:
            return False
        else: raise RuntimeError("Sorting error %s and %s" % (repr(self), repr(other_hand)))
    def __eq__(self, other_hand:"Hand") -> bool:
        return self.cards == other_hand.cards
        
    def __repr__(self) -> str:
        return "<Hand %s %s %i>" % (self.cards, str(self.hand_type), self.bid)
    def __str__(self) -> str:
        return self.cards

def parse_hands(document:str, joker:bool) -> list[Hand]:
    output:list[Hand] = []
    if joker:
        cards = CARDS_WILD
        order = CARD_WILD_ORDER
    else:
        cards = CARDS_TAME
        order = CARD_TAME_ORDER
    for line in document.split("\n"):
        hand_string, bid_string = line.split(" ")
        bid = int(bid_string)
        hand = Hand(hand_string, bid, joker, cards, order)
        output.append(hand)
    return output

def main() -> None:
    document_string = load_document("Input.txt")
    hands = parse_hands(document_string, joker=False)
    sorted_hands = sorted(hands, reverse=True)
    points = [hand.bid * (index + 1) for index, hand in enumerate(sorted_hands)]
    print("Part 1: %i" % sum(points))

    hands = parse_hands(document_string, joker=True)
    sorted_hands = sorted(hands, reverse=True)
    points = [hand.bid * (index + 1) for index, hand in enumerate(sorted_hands)]
    print("Part 2: %i" % sum(points))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()
