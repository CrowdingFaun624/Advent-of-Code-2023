from pathlib2 import Path
from typing import Any, Generator, Union

def load_document(name:str) -> str:
    if isinstance(name, str):
        name = parent_path.joinpath(name)
    path = Path(name)
    if parent_path not in path.parents:
        raise FileNotFoundError("File is not in the correct directory!")
    with open(path, "rt") as file:
        return file.read()

class MapRange():
    def __init__(self, destination_start:int, source_start:int, length:int) -> None:
        self.destination = destination_start
        self.source = source_start
        self.length = length

        self.offset = self.destination - self.source
        self.source_end = self.source + self.length
        self.destination_end = self.destination + self.length

    def __len__(self) -> int:
        return self.length
    
    # stupid Python can't union these types itself
    def __add__(self, other_value:Union[int, "SeedRange"]) -> Union[int, "SeedRange"]: # adds if within range, else returns original
        if isinstance(other_value, int):
            if other_value in self:
                return other_value + self.offset
            else:
                return other_value
        elif isinstance(other_value, SeedRange):
            if other_value.start in self:
                assert other_value.end - 1 in self # if this errors please scream and then re-code the whole slicer
                return other_value + self.offset
            else:
                return other_value
        else:
            raise NotImplementedError("Attempted to add MapLayer + %s" % str(type(other_value)))
    
    def __contains__(self, other_int:int) -> bool: # if within destination range
        return other_int >= self.source and other_int < self.source_end
    
    def __repr__(self) -> str:
        return "<MapRange %i–%i %i len %i>" % (self.source, self.source_end, self.offset, self.length)

class MapLayer():
    def __init__(self, maps:list[MapRange]) -> None:
        self.maps = maps
    
    def __add__(self, other_value:Union[int, "SeedRange"]) -> Union[int, "SeedRange"]:
        if isinstance(other_value, int):
            for map in self.maps:
                if other_value in map:
                    return map + other_value
            else:
                return other_value
        elif isinstance(other_value, SeedRange):
            for map in self.maps:
                if other_value.start in map:
                    assert other_value.end - 1 in map # if this is errors then oh shit
                    return map + other_value
            else:
                return other_value
        else:
            raise NotImplementedError("Attempted to add MapLayer + %s" % str(type(other_value)))
    
    def __len__(self) -> int:
        return len(self.maps)
    
    def __repr__(self) -> str:
        return repr(self.maps)

    def __iter__(self) -> "MapLayer":
        self.__iter_index = 0
        return self

    def __next__(self) -> MapRange:
        if self.__iter_index < len(self.maps):
            item = self.maps[self.__iter_index]
            self.__iter_index += 1
            return item
        else:
            raise StopIteration

class SeedRange():
    def __init__(self, start:int, length:int) -> None:
        if length < 0:
            raise ValueError("Length is negative: arguments %i and %i" % (start, length))

        self.start = start
        self.length = length

        self.end = self.start + self.length
    
    def __contains__(self, other_int:int) -> bool:
        return other_int >= self.start and other_int < self.start + self.length
    
    def __add__(self, offset:int) -> "SeedRange":
        return SeedRange(self.start + offset, self.length)
    
    def __repr__(self) -> str:
        return "<SeedRange %i–%i len %i>" % (self.start, self.end, self.length)

    def slice_range(self, map_layer:MapLayer) -> list["SeedRange"]:
        start_stop:list[int] = []
        for map_range in map_layer:
            start_stop.append(map_range.source)
            start_stop.append(map_range.source_end)
        start_stop.sort() # this line took me a while to get
        start_stop_trimmed = [position for position in start_stop if position >= self.start and position < self.end]
        if len(start_stop_trimmed) == 0: return [self]
        if start_stop_trimmed[0] != self.start: start_stop_trimmed.insert(0, self.start)
        if start_stop_trimmed[-1] != self.end: start_stop_trimmed.append(self.end)
        starts:list[int] = []; stops:list[int] = []
        for index, position in enumerate(start_stop_trimmed):
            if index != len(start_stop_trimmed) - 1: # if it is not the last one
                starts.append(position)
            if index != 0: # if it is not the first one
                stops.append(position)
        continuous_ranges = [(start, stop) for start, stop in zip(starts, stops) if start != stop]
        # list of tuples such that last of one is one less than first of next.
        # In `continuous_ranges`, start is SeedRange's start; end is SeedRange's end. Items of list correspond to map_layer items.
        # when stop and start are same, no gap between ranges. Still needs to be differentiated though b.c. different offsets.
        return [SeedRange(start, stop - start) for start, stop in continuous_ranges]

def adjacent_pairs(_list:list[Any]) -> Generator[Any, None, None]:
    return zip(_list[:-1:2], _list[1::2])

def parse_seed_individuals(seed_strings:list[str]) -> list[int]:
    return [int(seed_string) for seed_string in seed_strings]

def parse_seed_ranges(seed_strings:list[str]) -> list[SeedRange]:
    assert len(seed_strings) % 2 == 0
    output:list[SeedRange] = []
    for seed1, seed2 in adjacent_pairs(seed_strings):
        output.append(SeedRange(int(seed1), int(seed2)))
    return output

def parse_almanac(document:str, parse_seeds_as_ranges:bool) -> tuple[list[int],list[MapLayer]]:
    '''([seed_id1, seed_id2...], [[MapRange(dest_start, source_start, range_length)...]])'''
    line_groupings = document.split("\n\n")
    
    # seeds
    seed_line = line_groupings[0]
    assert seed_line.count("\n") == 0
    assert seed_line.startswith("seeds: ")
    seed_strings = seed_line.replace("seeds: ", "").split(" ")
    seeds = parse_seed_ranges(seed_strings) if parse_seeds_as_ranges else parse_seed_individuals(seed_strings)

    # maps
    map_layers:list[MapLayer] = []
    map_lists = line_groupings[1:]
    for map_list in map_lists:
        maps:list[MapRange] = []
        map_list_lines = map_list.split("\n")
        maps_lines = map_list_lines[1:]
        for map_line in maps_lines:
            map_dest_start, map_source_start, map_range_length = map_line.split(" ")
            map_dest_start, map_source_start, map_range_length = int(map_dest_start), int(map_source_start), int(map_range_length)
            maps.append(MapRange(map_dest_start, map_source_start, map_range_length))
        map_layers.append(MapLayer(maps))
    
    return seeds, map_layers

def check_for_overlap(seed_ranges:list[SeedRange]) -> None:
    for seed_layer1 in seed_ranges:
        for seed_layer2 in seed_ranges:
            if seed_layer1 is seed_layer2: continue
            if seed_layer1.start in seed_layer2 or seed_layer1.end in seed_layer2:
                raise RuntimeError("%s and %s overlap!" % (repr(seed_layer1), repr(seed_layer2)))

def flatten(_list:list[list[Any]]) -> list[Any]:
    return [item for sublist in _list for item in sublist]

def get_locations_individual(seeds:list[int], map_layers:list[MapLayer]) -> Generator[int, None, None]:
    for seed in seeds:
        location = seed
        for map_layer in map_layers:
            location = map_layer + location
        yield location

def get_locations_range(seed_ranges:list[SeedRange], map_layers:list[MapLayer]) -> list[SeedRange]:
    for map_layer in map_layers:
        seed_ranges = flatten(seed_range.slice_range(map_layer) for seed_range in seed_ranges)
        seed_ranges = [map_layer + seed_range for seed_range in seed_ranges]
    return seed_ranges

def main() -> None:
    document_string = load_document("Input.txt")
    seeds, maps = parse_almanac(document_string, False)
    lowest_seed_number = min(get_locations_individual(seeds, maps))
    print("Part 1: %i" % lowest_seed_number)
    seeds, maps = parse_almanac(document_string, True)
    lowest_seed_number = min(seed_range.start for seed_range in get_locations_range(seeds, maps))
    print("Part 2: %i" % lowest_seed_number)

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()
