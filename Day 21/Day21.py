from pathlib2 import Path
from typing import Generator, Iterable, TypeVar
import z3

def load_document(name:str) -> str:
    if isinstance(name, str):
        name = parent_path.joinpath(name)
    path = Path(name)
    if parent_path not in path.parents:
        raise FileNotFoundError("File is not in the correct directory!")
    with open(path, "rt") as file:
        return file.read()

Flatten = TypeVar("Flatten")

def flatten(matrix:Iterable[Iterable[Flatten]]) -> Generator[Flatten, None, None]:
    return [item for row in matrix for item in row]

START = "S"
GARDEN = "."
ROCK = "#"
NODE_TYPES = (START, GARDEN, ROCK)

class Node():
    def __init__(self, x:int, y:int, node_type:str) -> None:
        if not isinstance(x, int):
            raise TypeError("`x` is not an int!")
        if x < 0:
            raise ValueError("`x` is less than 0!")
        if not isinstance(y, int):
            raise TypeError("`y` is not an int!")
        if y < 0:
            raise ValueError("`y` is less than 0!")
        if not isinstance(node_type, str):
            raise TypeError("`node_type` is not a str!")
        if not any(node_type is option for option in NODE_TYPES):
            raise ValueError("`node_type` is not a reference to an item in `NODE_TYPES`!")
        
        self.x = x
        self.y = y
        self.node_type = node_type
        self.neighbors:tuple[bool, bool, bool, bool] = None

    def set_neighbors(self, all_nodes:dict[tuple[int,int],"Node"], width:int, height:int, infinite:bool) -> None:
        neighbors:list[bool] = []
        for node_pos in ((self.x - 1, self.y), (self.x + 1, self.y), (self.x, self.y - 1), (self.x, self.y + 1)):
            if infinite:
                relative_node_pos = (node_pos[0] % width, node_pos[1] % height)
            else: relative_node_pos = node_pos
            neighbors.append(relative_node_pos in all_nodes and all_nodes[relative_node_pos].node_type is not ROCK)
        self.neighbors = tuple(neighbors)
    
    def __str__(self) -> str:
        return self.node_type
    def __repr__(self) -> str:
        return "<Node %s at %i, %i>" % (self.node_type, self.x, self.y)
    
    def __hash__(self) -> int:
        return hash((self.x, self.y))

class Map():
    def __init__(self, nodes:list[Node]) -> None:
        if not isinstance(nodes, list):
            raise TypeError("`nodes` is not a list!")
        if len(nodes) == 0:
            raise ValueError("`nodes` is empty!")
        if any(not isinstance(node, Node) for node in nodes):
            raise TypeError("An item of `nodes` is not a Node!")
        if any(node.neighbors is None for node in nodes):
            raise ValueError("An item of `nodes` has its `neighbors` attribute as None!")
        
        self.nodes = nodes
        self.node_dict = {(node.x, node.y): node for node in self.nodes}
        self.width = max(node.x for node in nodes) + 1
        self.height = max(node.y for node in nodes) + 1
    
    def stringify(self, highlighted_nodes:set[Node]) -> str:
        return "\n".join("".join((str(node) if node not in highlighted_nodes else "O") for node in self.nodes[y*self.width:(y+1)*self.width]) for y in range(self.height))
    def __str__(self) -> str:
        return self.stringify(set())
    def __repr__(self) -> str:
        return "<Map %i×%i>" % (self.width, self.height)
    def get_neighbors(self, node:Node|tuple[int,int]) -> Generator[tuple[int,int], None, None]:
        return ((node.x + x_offset, node.y + y_offset) for index, x_offset, y_offset in ((0, -1, 0), (1, 1, 0), (2, 0, -1), (3, 0, 1)) if node.neighbors[index])
    
    def get_steps_away(self, steps:int) -> set[Node]:
        '''Returns a set of Nodes that can be travelled to in exactly `steps` steps.'''
        current_nodes = {node for node in self.nodes if node.node_type is START}
        for step in range(steps):
            current_nodes = set(flatten((self.node_dict[pos] for pos in self.get_neighbors(current_node)) for current_node in current_nodes))
        return current_nodes

class InfiniteMap(Map):
    def stringify(self, highlighted_nodes:set[tuple[int,int]]) -> str:
        def decide_character(x:int, y:int) -> str:
            node = self.node_dict[x % self.width, y % self.height]
            if node.node_type is START:
                return START
            elif (x, y) in highlighted_nodes:
                return "O"
            else:
                return node.node_type
        min_x = min(node[0] for node in highlighted_nodes)
        max_x = max(node[0] for node in highlighted_nodes)
        min_y = min(node[1] for node in highlighted_nodes)
        max_y = max(node[1] for node in highlighted_nodes)
        return "\n".join("".join(decide_character(x, y) for x in range(min_x, max_x + 1)) for y in range(min_y, max_y + 1))
    
    def get_neighbors(self, position:tuple[int,int]) -> list[tuple[int,int]]:
        node_neighbors = self.node_dict[position[0] % self.width, position[1] % self.height].neighbors
        x, y = position
        return [(x + x_offset, y + y_offset) for index, x_offset, y_offset in ((0, -1, 0), (1, 1, 0), (2, 0, -1), (3, 0, 1)) if node_neighbors[index]]

    def get_steps_away(self, steps:list[int], start:tuple[int,int]=None, write_file:int|None=None) -> Generator[set[tuple[int,int]], None, None]:
        nodes_reachable_odd:set[tuple[int,int]] = set()
        nodes_reachable_even:set[tuple[int,int]] = set()
        if start is None:
            start = [(node.x, node.y) for node in self.nodes if node.node_type is START][0]
        current_nodes = [start]
        steps_target_index = 0
        step = 0
        while True:
            step += 1
            if (step) % 2 == 0:
                nodes_reachable = nodes_reachable_even
            else:
                nodes_reachable = nodes_reachable_odd
            new_nodes:list[tuple[int,int]] = []
            visited_new_nodes:set[tuple[int,int]] = set()
            for current_node in current_nodes:
                for neighbor in self.get_neighbors(current_node):
                    if neighbor not in visited_new_nodes and neighbor not in nodes_reachable:
                        new_nodes.append(neighbor)
                        visited_new_nodes.add(neighbor)
            current_nodes = new_nodes
            nodes_reachable.update(new_nodes)
            # print(step)
            if step >= steps[steps_target_index]:
                if write_file is not None and write_file == steps_target_index:
                    with open("./Day 21/test.txt", "wt") as f:
                        f.write(self.stringify(nodes_reachable))
                steps_target_index += 1
                yield nodes_reachable
                if steps_target_index >= len(steps): break    

    def smart_get_steps_away(self, steps:int) -> int:
        # Data can be represented perfectly with a quadratic
        cycle_length = max(node.x for node in self.nodes) + 1 # amount of steps it takes after each in-line with the empty patch it takes to be in-line again. (e.g. 61, 192, 323)
        assert max(node.y for node in self.nodes) + 1 == cycle_length

        cycle_round = None
        for cycle_round in range(0, cycle_length):
            if ((int(((steps - cycle_round) / cycle_length) * 65536)) / 65536) % 1 == 0:
                break
            cycle_repeats = int((steps - cycle_round) / cycle_length)
        else:
            raise RuntimeError("Could not find a cycle!")
        
        y_values = (len(result) for result in self.get_steps_away(list(range(cycle_round, cycle_round + cycle_length * 3, cycle_length))))

        a = z3.Const("a", sort=z3.IntSort())
        b = z3.Const("b", sort=z3.IntSort())
        c = z3.Const("c", sort=z3.IntSort())
        solver = z3.Solver()
        for x, y in enumerate(y_values):
            solver.add(y == a * x ** 2 + b * x + c)
        
        solver.check()
        model = solver.model()

        a, b, c = int(str(model[a])), int(str(model[b])), int(str(model[c]))

        result = a * cycle_repeats**2 + b * cycle_repeats + c
        return result

def parse_map(document:str, infinite:bool) -> Map|InfiniteMap:
    nodes:list[Node] = list(flatten((Node(x, y, NODE_TYPES[NODE_TYPES.index(char)]) for x, char in enumerate(line)) for y, line in enumerate(document.split("\n"))))
    nodes_dict = {(node.x, node.y): node for node in nodes}
    width = max(node.x for node in nodes) + 1
    height = max(node.y for node in nodes) + 1
    for node in nodes:
        node.set_neighbors(nodes_dict, width, height, infinite)
    if infinite:
        return InfiniteMap(nodes)
    else:
        return Map(nodes)

def main() -> None:
    document_string = load_document("Input.txt")
    map = parse_map(document_string, infinite=False)
    print("Part 1: %i" % len(map.get_steps_away(64)))
    map = parse_map(document_string, infinite=True)
    print("Part 2: %i" % map.smart_get_steps_away(26501365))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()
