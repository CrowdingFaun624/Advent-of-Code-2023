from pathlib2 import Path
from typing import Generator

def load_document(name:str) -> str:
    if isinstance(name, str):
        name = parent_path.joinpath(name)
    path = Path(name)
    if parent_path not in path.parents:
        raise FileNotFoundError("File is not in the correct directory!")
    with open(path, "rt") as file:
        return file.read()

UNKNOWN = 0
DAMAGED = 1
OPERATIONAL = 2

def stringify_condition(condition:int) -> str:
    return {UNKNOWN: "?", DAMAGED: "#", OPERATIONAL: "."}[condition]
def stringify_conditions(conditions:list[int]) -> str:
    return "".join(stringify_condition(condition) for condition in conditions)
def intify_spring(char:str) -> int:
    return {"?": UNKNOWN, "#": DAMAGED, ".": OPERATIONAL}[char]

class Record():
    def __init__(self, conditions:list[int], group_sizes:list[int]) -> None:
        if not isinstance(conditions, list):
            raise TypeError("`conditions` is not an int!")
        if not all(isinstance(item, int) for item in conditions):
            raise TypeError("`conditions` has an item that is not a int!")
        if not all(item >= 0 and item < 3 for item in conditions):
            raise ValueError("`conditions` has an item that is not within [0, 2]!")
        if len(conditions) == 0:
            raise ValueError("`conditions` is not not empty!")
        if not isinstance(group_sizes, list):
            raise TypeError("`group_sizes` is not a list!")
        if not all(isinstance(item, int) for item in group_sizes):
            raise TypeError("`group_sizes` has an item that is not an int!")
        if len(group_sizes) == 0:
            raise ValueError("`group_sizes` is not not empty!")
        
        self.conditions = conditions
        self.start_conditions = conditions.copy()
        self.group_sizes = group_sizes
    
    def __repr__(self) -> str:
        return "<Record %i, %i>" % (len(self.conditions), len(self.group_sizes))
    
    def __str__(self) -> str:
        return "".join(stringify_condition(condition) for condition in self.conditions) + " " + ",".join(str(size) for size in self.group_sizes)

    def is_valid_condition(self, conditions:list[int], sizes:list[int]) -> bool:
        '''Returns False if the conditions are not valid, and True if they are or it is uncertain.'''
        length = 0
        this_sizes:list[int] = []
        has_unknown = False
        ends_in_ambiguous_group = False
        for condition in conditions:
            if condition is DAMAGED:
                length += 1
            elif condition is OPERATIONAL:
                if length > 0:
                    this_sizes.append(length)
                length = 0
            elif condition is UNKNOWN:
                has_unknown = True
                break
        else:
            if not has_unknown and length > 0: # If it does have unknown that means that it must stop with "#?" and the ending group can have any length.
                this_sizes.append(length)
                ends_in_ambiguous_group = True
        
        if this_sizes == sizes:
            return True # it is complete
        if has_unknown:
            if len(this_sizes) > len(sizes):
                return False # too many groups
            if ends_in_ambiguous_group:
                if any(this_size != group_size for this_size, group_size in zip(this_sizes[:-1], sizes[:len(this_sizes)-1])):
                    return False # wrong group sizes
                else:
                    return True # reached an unknown
            else:
                if any(this_size != group_size for this_size, group_size in zip(this_sizes, sizes[:len(this_sizes)])):
                    return False # wrong group sizes
                else:
                    return True # reached an unknown
        else:
            if len(this_sizes) != len(sizes):
                return False # too many or not enough groups
            elif any(this_size != group_size for this_size, group_size in zip(this_sizes, sizes)):
                return False # wrong group sizes
            else:
                return True # it is complete

    def get_conditions_insert(self, conditions:list[int], sizes:list[int], index:int, size:int) -> tuple[list[int],list[int]]:
        '''Returns a copy of conditions and sizes that act as if there is a group of damaged springs
        at `index` with `size`, but it's trimmed automatically so you can't see it.'''
        assert index + size >= len(conditions) or conditions[index + size] is not DAMAGED
        new_conditions = conditions[index + size + 1:] # It trims the stuff before the group, the group, as well as the condition after the group (for isolation).
        new_sizes = sizes.copy()
        new_sizes.pop(0) # It removes the size it just filled in and trimmed.
        return new_conditions, new_sizes

    def trim_conditions(self, conditions:list[int], sizes:list[int]) -> tuple[list[int]|None,list[int]|None,bool]:
        '''Removes damaged and operational springs up to the unknown springs.
        Returns the new conditions, the new sizes, and if it had an unknown tile.
        Returns None, None, False if nothing is valid.
        Will not remove damaged groups that border the unknown springs.'''
        conditions = conditions.copy()
        sizes = sizes.copy()
        length = 0
        while len(conditions) != 0:
            condition = conditions.pop(0) # I don't care that it's slow; it's only a few items.
            if condition is DAMAGED:
                length += 1
            elif condition is OPERATIONAL:
                if length > 0:
                    if len(sizes) == 0: return None, None, False # Some invalid records can have this happen.
                    if length != sizes.pop(0): # In a valid record, this will always be equal to `length`
                        return None, None, False
                    # I don't need to re-add this size to the sizes list because it is behind an operational spring
                    # and therefore I don't need to care about it.
                    length = 0
            elif condition is UNKNOWN:
                # `[DAMAGED] * length` adds `length` number of `DAMAGE` items to the beginning of the list.
                # This is so that it doesn't remove the damaged group that borders the unknown springs.
                # Also adds `[condition]` because it just popped it and it is an unknown spring.
                return [DAMAGED] * length + [condition] + conditions, sizes, True
            else: raise RuntimeError()
        if length > 0: # Group of damaged springs that meets the end of the record.
            if len(sizes) == 0: return None, None, False
            if length != sizes.pop(0):
                return None, None, False
        if len(sizes) > 0: return None, None, False
        return conditions, sizes, False

    def get_hash(self, conditions:list[int], sizes:list[int]) -> tuple[tuple[int],tuple[int]]:
        return (tuple(conditions), tuple(sizes))

    def combinations(self, conditions:list[int]|None=None, sizes:list[int]|None=None, print_debug_messages:bool=False, indentation:int=0) -> int:
        if conditions is None: conditions = self.conditions
        if sizes is None: sizes = self.group_sizes

        this_hash = self.get_hash(conditions, sizes)
        if this_hash in memoization: # wow, it's really that simple. Wow.
            return memoization[this_hash]

        new_conditions, new_sizes, has_unknown = self.trim_conditions(conditions, sizes)
        if new_conditions is None:
            if print_debug_messages: print(" " * indentation + "Trimmed conditions \"%s\" (sizes \"%s\") are invalid." % (stringify_conditions(conditions), str(sizes)))
            memoization[this_hash] = 0
            return 0
        if new_conditions != conditions and new_sizes != sizes:
            if print_debug_messages: print(" " * indentation + "Trimmed conditions \"%s\" (sizes \"%s\") to \"%s\" (sizes \"%s\")." % (stringify_conditions(conditions), str(sizes), stringify_conditions(new_conditions), str(new_sizes)))
            return self.combinations(new_conditions, new_sizes)
        
        if len(conditions) == 0:
            if len(sizes) == 0: # There are neither any conditions nor sizes; it has been completed.
                if print_debug_messages: print(" " * indentation + "The conditions are a combination.")
                memoization[this_hash] = 1
                return 1
            else: # There are no conditions, but still sizes left; it is incomplete.
                if print_debug_messages: print(" " * indentation + "The conditions are not valid.")
                memoization[this_hash] = 0
                return 0
        elif len(sizes) == 0:
            if conditions.count(DAMAGED) == 0: # If there are no more sizes left and no more damaged springs remain, it is valid.
                if print_debug_messages: print(" " * indentation + "The conditions \"%s\" are a combination." % stringify_conditions(conditions))
                memoization[this_hash] = 1
                return 1
            else: # If there are no more sizes left and still damaged springs remaining, it is invalid.
                if print_debug_messages: print(" " * indentation + "The conditions \"%s\" are not valid." % stringify_conditions(conditions))
                memoization[this_hash] = 0
                return 0
        if not has_unknown: # If there are no unknowns, there can only be one combination. It may or may not be valid.
            if self.is_valid_condition(conditions, sizes):
                if print_debug_messages: print(" " * indentation + "The conditions \"%s\" (sizes \"%s\") are a combination." % (stringify_conditions(conditions), str(sizes)))
                memoization[this_hash] = 1
                return 1
            else:
                if print_debug_messages: print(" " * indentation + "The conditions \"%s\" (sizes \"%s\")  are not valid." % (stringify_conditions(conditions), str(sizes)))
                memoization[this_hash] = 0
                return 0
        
        total_combinations = 0
        this_size = sizes[0]
        for condition_index, condition in enumerate(conditions):
            can_place_here = True
            if this_size == len(conditions): next_group_length = conditions[condition_index:]
            else: next_group_length = conditions[condition_index:condition_index + this_size]
            if condition_index + this_size > len(conditions): # If the end of the group is not within the bounds, it cannot be placed there.
                can_place_here = False
            # `next_group_length` is a list of conditions with length `this_size`, starting at `condition_index`.
            if OPERATIONAL in next_group_length:
                # If there is an operational spring in the next group-length, a group of damaged springs cannot be placed there.
                can_place_here = False # A variable is used instead of just `continue` because the conditional after the recurse logic must run every time.
            not_damaged_before = condition_index <= 0 or conditions[condition_index - 1] is not DAMAGED
            not_damaged_after = condition_index + this_size >= len(conditions) or conditions[condition_index + this_size] is not DAMAGED
            if (not not_damaged_before) or (not not_damaged_after):
                # The group of damaged springs must be isolated from other groups by unknown or operational springs, lest it be longer than expected.
                can_place_here = False
            
            if can_place_here:
                # This is a valid space that it can place this group at. It does so.
                new_conditions, new_sizes = self.get_conditions_insert(conditions, sizes, condition_index, this_size)
                if print_debug_messages: print(" " * indentation + "Conditions \"%s\" from \"%s\" and sizes \"%s\" from \"%s\" at condition index %i with size %i." % (stringify_conditions(new_conditions), stringify_conditions(conditions), str(new_sizes), str(sizes), condition_index, this_size))
                total_combinations += self.combinations(new_conditions, new_sizes, print_debug_messages, indentation+2)

            if condition is DAMAGED and (condition_index + 1 < len(conditions) and conditions[condition_index + 1] is not DAMAGED):
                # If this condition is damaged and the next is not, then the current condition cannot be placed any further than this.
                break
        if print_debug_messages: print(" " * indentation + "\"%s\" has %i combinations." % (str(self), total_combinations))
        memoization[this_hash] = total_combinations
        return total_combinations

def parse_records(document:str, unfold:bool) -> list[Record]:
    output:list[Record] = []
    for row in document.split("\n"):
        conditions_str, group_sizes_str = row.split(" ")
        if unfold:
            conditions_str = "?".join([conditions_str] * 5)
            group_sizes_str = ",".join([group_sizes_str] * 5)
        conditions = [intify_spring(condition) for condition in conditions_str]
        group_sizes = [int(size) for size in group_sizes_str.split(",")]
        output.append(Record(conditions, group_sizes))
    return output

memoization:dict[tuple[tuple[int],tuple[int]],int] = {}

def test(unfold:bool) -> None:
    document_string = load_document("Example1.txt")
    if unfold:
        required_values = [1, 16384, 1, 16, 2500, 506250]
    else:
        required_values = [1, 4, 1, 1, 4, 10]
    records = parse_records(document_string, unfold=unfold)
    for record, required_value in zip(records, required_values):
        try:
            combinations = record.combinations()
        except Exception:
            combinations = -1
        if combinations != required_value:
            record.combinations(print_debug_messages=True) # just to get the debug messages.
            raise AssertionError("Record %s should have been %i, but is instead %i!" % (str(record), required_value, combinations))

def main() -> None:
    document_string = load_document("Input.txt")
    records = parse_records(document_string, unfold=False)
    print("Part 1: %i" % sum(record.combinations() for record in records))
    records = parse_records(document_string, unfold=True)
    print("Part 2: %i" % sum(record.combinations() for record in records))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    # test(False)
    # test(True)
    main()
