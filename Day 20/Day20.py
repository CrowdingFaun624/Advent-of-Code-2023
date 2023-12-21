from collections import deque
from pathlib2 import Path
from math import lcm
from typing import Any, Generator, Hashable, Iterable, TypeVar

Flatten = TypeVar("Flatten")

def load_document(name:str) -> str:
    if isinstance(name, str):
        name = parent_path.joinpath(name)
    path = Path(name)
    if parent_path not in path.parents:
        raise FileNotFoundError("File is not in the correct directory!")
    with open(path, "rt") as file:
        return file.read()

def flatten(matrix:Iterable[Iterable[Flatten]]) -> Generator[Flatten, None, None]:
    return [item for row in matrix for item in row]

class Pulse():
    def __init__(self, is_high:bool) -> None:
        if not isinstance(is_high, bool):
            raise TypeError("`is_high` is not a bool!")
        
        self.is_high = is_high
        self.is_low = not is_high
    
    def copy(self) -> "Pulse":
        return Pulse(self.is_high)
    
    def copy_inverted(self) -> "Pulse":
        return Pulse(self.is_low)
    
    def __str__(self) -> str:
        return "high" if self.is_high else "low"
    def __repr__(self) -> str:
        return "<Pulse %s>" % ("high" if self.is_high else "low")

class Module():
    def __init__(self, name:str, destinations_str:list[str], debug_mode:bool) -> None:
        if not isinstance(name, str):
            raise TypeError("`name` is not a str!")
        if len(name) == 0:
            raise ValueError("`name` is empty!")
        if not isinstance(destinations_str, list):
            raise TypeError("`destinations_str` is not a list!")
        if len(destinations_str) == 0:
            raise ValueError("`destinations_str` is empty!")
        if any(not isinstance(item, str) for item in destinations_str):
            raise TypeError("An item of `destinations_str` is not a str!")
        if not isinstance(debug_mode, bool):
            raise TypeError("`debug_mode` is not a bool!")
        
        self.name = name
        self.destinations_str = destinations_str
        self.destinations:list[Module] = []
        self.sources:list[Module] = []
        self.debug_mode = debug_mode
        self.tracker:None|list[Pulse] = None # if not None, appends pulses that it receives.
    
    def init(self) -> None: # for overriding by subclasses
        pass
    
    def __repr__(self) -> str:
        return "<%s \"%s\" %i dests>" % (self.__class__.__name__, self.name, len(self.destinations))
    
    def receive_pulse(self, pulse:Pulse, received_from:"Module") -> tuple[list[tuple[Pulse,"Module","Module"]], bool]:
        '''Returns a list of pulses, destination nodes, and source nodes.'''
        raise NotImplementedError()
    def send_pulses(self, pulse:Pulse) -> list[tuple[Pulse,"Module","Module"]]:
        for destination in self.destinations:
            if self.debug_mode:
                print("%s -%s-> %s" % (self.name, str(pulse), destination.name))
            return destination.receive_pulse(pulse, self)
    
    def state(self) -> list[Hashable]:
        return []

class UntypedModule(Module):
    def __init__(self, name:str) -> None:
        if not isinstance(name, str):
            raise TypeError("`name` is not a str!")
        if len(name) == 0:
            raise ValueError("`name` is empty!")
        self.name = name
        self.destinations_str = []
        self.destinations = []
        self.sources = []
        self.tracker:None|list[Pulse] = None
    def receive_pulse(self, pulse:Pulse, received_from:Module) -> list[tuple[Pulse,Module,Module]]:
        if self.tracker is not None: self.tracker.append(pulse)
        return []

class ButtonModule(Module):
    def init(self) -> None:
        assert self.name == "button"
        assert self.destinations_str == ["broadcaster"]
    def __str__(self) -> str:
        return "button -> broadcaster"

class BroadcasterModule(Module):
    def init(self) -> None:
        assert self.name == "broadcaster"
    def __str__(self) -> str:
        return "broadcaster -> %s" % (", ".join(destination.name for destination in self.destinations))
    
    def receive_pulse(self, pulse:Pulse, received_from:Module) -> list[tuple[Pulse,"Module","Module"]]:
        if self.tracker is not None: self.tracker.append(pulse)
        return [(pulse, destination, self) for destination in self.destinations]

class FlipFlopModule(Module):
    def init(self) -> None:
        self.toggled = False
    def __repr__(self) -> str:
        return "<%s \"%s\" %i dests %s>" % (self.__class__.__name__, self.name, len(self.destinations), str(self.toggled))
    def __str__(self) -> str:
        return "%s%s -> %s" % ("%", self.name, ", ".join(destination.name for destination in self.destinations))
    
    def receive_pulse(self, pulse:Pulse, received_from:Module) -> list[tuple[Pulse,"Module","Module"]]:
        if self.tracker is not None: self.tracker.append(pulse)
        if pulse.is_high:
            return [] # nothing happens if a flip-flop module receives a high pulse. False because this is a high pulse.
        else:
            self.toggled = not self.toggled
            pulse = Pulse(self.toggled)
            return [(pulse, destination, self) for destination in self.destinations]
    
    def state(self) -> list[Hashable]:
        return [self.toggled]

class ConjunctionModule(Module):
    def init(self) -> None:
        self.recent_sources = {source: Pulse(False) for source in self.sources}
    def __str__(self) -> str:
        return "&%s -> %s" % (self.name, ", ".join(destination.name for destination in self.destinations))
    
    def receive_pulse(self, pulse:Pulse, received_from:Module) -> list[tuple[Pulse,"Module","Module"]]:
        if self.tracker is not None: self.tracker.append(pulse)
        self.recent_sources[received_from] = pulse
        pulse = Pulse(not all(pulse.is_high for pulse in self.recent_sources.values()))
        return [(pulse, destination, self) for destination in self.destinations]
    
    def state(self) -> list[Hashable]:
        return [pulse.is_high for pulse in self.recent_sources.values()]

def parse_modules(document:str, debug_mode:bool=False) -> dict[str,Module]:
    modules:dict[str,Module] = {}
    for line in document.split("\n"):
        name_type, destinations_str = line.split(" -> ")
        if name_type == "broadcaster":
            module_type = BroadcasterModule
            name = "broadcaster"
        elif name_type.startswith("%"):
            module_type = FlipFlopModule
            name = name_type[1:]
        elif name_type.startswith("&"):
            module_type = ConjunctionModule
            name = name_type[1:]
        else:
            raise RuntimeError("A module has a weird name-type: \"%s\"!" % name_type)
        destinations_strs = destinations_str.split(", ")
        modules[name] = module_type(name, destinations_strs, debug_mode=debug_mode)
    modules["button"] = ButtonModule("button", ["broadcaster"], debug_mode=debug_mode)
    # Set references in modules to other modules
    untyped_modules:dict[str,UntypedModule] = {}
    for module in modules.values():
        module.destinations = []
        for destination_str in module.destinations_str:
            if destination_str in modules:
                module.destinations.append(modules[destination_str])
                modules[destination_str].sources.append(module)
            else:
                if destination_str not in untyped_modules:
                    untyped_modules[destination_str] = UntypedModule(destination_str)
                module.destinations.append(untyped_modules[destination_str])
                untyped_modules[destination_str].sources.append(module)
    modules.update(untyped_modules)
    for module in modules.values():
        module.init()
    return modules

def hash_modules(modules:Iterable[Module]) -> int:
    big_hashable:list[Hashable] = []
    for module in modules:
        module_hashable = module.state()
        big_hashable.extend(module_hashable)
    return sum(2**index * state for index, state in enumerate(big_hashable))

def button_push(all_modules:dict[str,Module]) -> tuple[Hashable, int, int]:
    '''Returns the state at the end of the button push and how many low and high pulses were sent.'''
    planned_sends:deque[tuple[Pulse,Module,Module]] = deque(all_modules["button"].send_pulses(Pulse(False)))
    total_low_pulses = 1
    total_high_pulses = 0
    while len(planned_sends) > 0:
        pulse, destination, source = planned_sends.popleft()
        if pulse.is_high:
            total_high_pulses += 1
        else:
            total_low_pulses += 1
        if source.debug_mode:
            print("%s -%s-> %s" % (source.name, str(pulse), destination.name))
        planned_sends.extend(destination.receive_pulse(pulse, source))
    return hash_modules(all_modules.values()), total_low_pulses, total_high_pulses

def button_pushes(all_modules:dict[str,Module], times:int) -> tuple[int,int]:
    states:dict[Hashable,int] = {} # {state: push index}
    pulse_history:list[tuple[int,int]] = []
    for step in range(times):
        state, low_pulses, high_pulses = button_push(all_modules)
        pulse_history.append((low_pulses, high_pulses))
        if state in states:
            break
        else:
            states[state] = step
    else: # If it did not find a cycle.
        return sum(pulses[0] for pulses in pulse_history), sum(pulses[1] for pulses in pulse_history)
    cycle_start_step = states[state]
    cycle_length = step - cycle_start_step
    steps_left = times - cycle_start_step
    relevant_history = pulse_history[cycle_start_step:-1]
    assert len(relevant_history) == cycle_length

    # pulses for part before it started cycling (if any)
    low_pulses, high_pulses = sum(pulses[0] for pulses in pulse_history[:cycle_start_step]), sum(pulses[1] for pulses in pulse_history[:cycle_start_step])

    # quick multiplication through the repeating cycles
    relevant_history_low_sum, relevant_history_high_sum = sum(pulses[0] for pulses in relevant_history), sum(pulses[1] for pulses in relevant_history)
    low_pulses += relevant_history_low_sum * (steps_left // cycle_length)
    high_pulses += relevant_history_high_sum * (steps_left // cycle_length)

    # remainder of cycle after end of quick multiplication
    remainder_cycles = steps_left % cycle_length
    low_pulses += sum(pulses[0] for pulses in relevant_history[:remainder_cycles])
    high_pulses += sum(pulses[1] for pulses in relevant_history[:remainder_cycles])

    return low_pulses, high_pulses

def get_tree(module:Module) -> list[Module]: # This is slow but there aren't that many nodes
    visited_modules:list[Module] = []
    unvisited_modules:deque[Module] = deque(module.destinations)
    while len(unvisited_modules) > 0:
        current_module = unvisited_modules.popleft()
        if current_module in visited_modules: continue
        for neighbor in current_module.destinations:
            if neighbor not in unvisited_modules:
                unvisited_modules.append(neighbor)
        if current_module not in visited_modules:
            visited_modules.append(current_module)
    return visited_modules

def get_flat_trees(broadcaster_destinations:list[Module], rx:Module) -> dict[str,list[Module]]:
    flat_trees:dict[str,list[Module]] = {}
    for broadcaster_destination in broadcaster_destinations:
        flat_trees[broadcaster_destination.name] = get_tree(broadcaster_destination)
        flat_trees[broadcaster_destination.name].remove(rx)
        flat_trees[broadcaster_destination.name].remove(rx.sources[0])
    return flat_trees

def assert_trees_dont_touch(trees:dict[str,list[Module]]):
    for tree_base_name, tree in trees.items():
        other_trees = list(flatten(trees[other_broadcaster_destination] for other_broadcaster_destination in trees if other_broadcaster_destination is not tree_base_name))
        if any(tree_item in other_trees for tree_item in tree):
            return True
    return False

def get_cycle_rx(tree:dict[str,Module], tree_ending:Module) -> tuple[int, int]:
    '''Returns the cycle length and the offset within the cycle'''
    states:dict[Hashable,int] = {} # {state: push index}
    pulse_history:list[list[Pulse]] = []
    step = 0
    while True:
        tree_ending.tracker = []
        state, _, _ = button_push(tree)
        pulse_history.append(tree_ending.tracker)
        if state in states:
            break
        else:
            states[state] = step
        step += 1
    cycle_start_step = states[state]
    cycle_length = step - cycle_start_step
    assert cycle_start_step == 0
    relevant_history = {index: tracker for index, tracker in enumerate(pulse_history) if any(pulse.is_low for pulse in tracker)}
    assert len(relevant_history) == 1
    assert all(tracker[0].is_low for tracker in relevant_history.values())
    offset = list(relevant_history.keys())[0]
    return cycle_length, offset

def find_rx(all_modules:dict[str,Module]) -> int:
    rx = all_modules["rx"]
    assert len(rx.sources) == 1 and isinstance(rx.sources[0], ConjunctionModule)
    rx_only_source = rx.sources[0]
    rx_sources = rx_only_source.sources
    assert all(isinstance(source, ConjunctionModule) for source in rx_sources)
    # `rx_children` are the ConjunctionModules that point to the node that points to rx.

    broadcaster = all_modules["broadcaster"]
    broadcaster_destinations = broadcaster.destinations
    # This part asserts that all of the trees from broadcaster_destinations to rx_sources are isolated.
    trees = get_flat_trees(broadcaster_destinations, rx)
    if assert_trees_dont_touch(trees):
        raise RuntimeError("A trees has an overlap with another tree!")
    
    # Analyzing the cycles of the individual trees
    cycle_data:list[tuple[int,int]] = []
    for tree_name, tree in trees.items():
        tree_ending = [tree_item for tree_item in tree if tree_item in rx_sources][0]
        artificial_tree = tree.copy()
        assert broadcaster not in tree
        artificial_broadcaster = BroadcasterModule("broadcaster", [tree_name], False) # Only points to this tree so it doesn't mess with the other trees.
        artificial_broadcaster.destinations = [all_modules[tree_name]]
        artificial_tree.append(artificial_broadcaster)
        artificial_tree.append(all_modules["button"])
        artificial_modules = {module.name: module for module in artificial_tree}
        # artificial modules is a regular modules dict, except that it only has one branch.
        cycle_data.append(get_cycle_rx(artificial_modules, tree_ending))

    # Find when they all intersect
    cycle_lengths = [cycle_length for cycle_length, cycle_offset in cycle_data]
    return lcm(*cycle_lengths)

def main() -> None:
    document_string = load_document("Input.txt")
    modules = parse_modules(document_string, debug_mode=False)
    low_pulses, high_pulses = button_pushes(modules, 1000)
    print("Part 1: %i" % (low_pulses * high_pulses))
    print("Part 2: %i" % find_rx(modules))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()
