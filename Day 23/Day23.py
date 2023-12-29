from enum import Enum
from pathlib2 import Path
from typing import Generator, Iterable, TypeVar

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
    return (item for row in matrix for item in row)

class NodeType(Enum):
    paths = "."
    forest = "#"
    up_slope = "^"
    right_slope = ">"
    down_slope = "v"
    left_slope = "<"

SLOPE_DIRECTIONS = {NodeType.up_slope: (0, -1), NodeType.right_slope: (1, 0), NodeType.down_slope: (0, 1), NodeType.left_slope: (-1, 0)}

class Node():
    def __init__(self, x:int, y:int, char:str, is_slippery:bool) -> None:
        for label, value in (("x", x), ("y", y)):
            if not isinstance(value, int):
                raise TypeError("`%s` is not an int!" % label)
            if value < 0:
                raise ValueError("`%s` is less than 0!" % label)
        if not isinstance(char, str):
            raise TypeError("`char` is not a str!")
        if len(char) != 1:
            raise ValueError("`char` is not length 1!")
        if not isinstance(is_slippery, bool):
            raise TypeError("`is_slippery` is not a bool!")
        
        self.x = x
        self.y = y
        self.node_type = [node_type for node_type in NodeType if node_type.value == char][0]
        self.is_slippery = is_slippery
        self.is_slope = self.is_slippery and self.node_type in (NodeType.up_slope, NodeType.right_slope, NodeType.down_slope, NodeType.left_slope)
        self.visitable_neighbors:list[Node] = [] # neighbors that can be traveled to in a valid move
        self.neighbors:list[Node] = [] # all non-forest Nodes that border this Node.
    
    def set_neighbors(self, nodes:dict[tuple[int,int],"Node"], is_slippery:bool) -> None:
        '''Sets the `neighbors` attribute of this Node.'''
        if self.node_type is NodeType.forest:
            return
        if self.is_slope:
            offset_x, offset_y = SLOPE_DIRECTIONS[self.node_type]
            x, y = self.x + offset_x, self.y + offset_y
            if (x, y) not in nodes:
                raise RuntimeError("Node \"%s\" points towards the edge of the map!" % repr(self))
            neighbor_node = nodes[x, y]
            if neighbor_node.node_type is NodeType.forest:
                raise RuntimeError("Node \"%s\" points towards a forest Node!" % repr(self))
            self.visitable_neighbors = [neighbor_node]
        for x, y in ((self.x - 1, self.y), (self.x + 1, self.y), (self.x, self.y - 1), (self.x, self.y + 1)):
            if (x, y) not in nodes:
                continue
            neighbor_node = nodes[x, y]
            if neighbor_node.node_type is NodeType.forest:
                continue
            if not self.is_slope:
                if neighbor_node.is_slope:
                    neighbor_x_offset, neighbor_y_offset = SLOPE_DIRECTIONS[neighbor_node.node_type]
                    if (neighbor_node.x - neighbor_x_offset, neighbor_node.y - neighbor_y_offset) == (self.x, self.y):
                        self.visitable_neighbors.append(neighbor_node)
                else:
                    self.visitable_neighbors.append(neighbor_node)
            self.neighbors.append(neighbor_node)
    
    def __str__(self) -> str:
        return self.node_type.value
    def __repr__(self) -> str:
        return "<Node %s at %i, %i>" % (self.node_type.value, self.x, self.y)
    
    def __hash__(self) -> int:
        return hash((self.x, self.y))

class Junction():
    def __init__(self, node:Node) -> None:
        if not isinstance(node, Node):
            raise TypeError("`node` is not a Node!")
        
        self.node = node
        self.trails:list[tuple[Junction,int]] = [] # [(junction, distance)]
    
    def __repr__(self) -> str:
        return "<Junction %i, %i>" % (self.node.x, self.node.y)
    def __hash__(self) -> int:
        return hash(self.node)

class Map():
    def __init__(self, nodes:list[Node], width:int, height:int, is_slippery:bool) -> None:
        if not isinstance(nodes, list):
            raise TypeError("`nodes` is not a list!")
        if len(nodes) == 0:
            raise ValueError("`nodes` is empty!")
        if any(not isinstance(node, Node) for node in nodes):
            raise TypeError("An item of `nodes` is not a Node")
        for label, value in (("width", width), ("height", height)):
            if not isinstance(value, int):
                raise TypeError("`%s` is not an int!" % label)
            if value < 1:
                raise ValueError("`%s` is less than 1!" % label)
        if not isinstance(is_slippery, bool):
            raise TypeError("`is_slippery` is not a bool!")
        
        self.nodes = nodes
        self.width = width
        self.height = height
        self.start_node = [node for node in self.nodes if node.y == 0 and node.node_type is not NodeType.forest][0]
        self.end_node = [node for node in self.nodes if node.y == height - 1 and node.node_type is not NodeType.forest][0]
        self.get_junctions()

    def get_junctions(self) -> None:
        self.junctions:dict[Node,Junction] = {node: Junction(node) for node in self.nodes if len(node.neighbors) > 2}
        self.junctions[self.start_node] = Junction(self.start_node)
        self.junctions[self.end_node] = Junction(self.end_node)
        for junction_node, junction in self.junctions.items():
            for start_neighbor in junction_node.visitable_neighbors: #junction_remaining_neighbors[junction]:
                # print(repr(start_neighbor), "from", repr(junction_node))
                current_node = start_neighbor
                previous_node = junction_node
                steps = 0
                while True:
                    steps += 1
                    if current_node in self.junctions:
                        junction.trails.append((self.junctions[current_node], steps))
                        break
                    else:
                        next_nodes = [neighbor for neighbor in current_node.visitable_neighbors if neighbor is not previous_node]
                        if len(next_nodes) == 0:
                            assert sum(1 for neighbor in current_node.neighbors if neighbor is not previous_node) != 0 # There are no true dead-ends; only unclimable slopes.
                            break
                        previous_node, current_node = current_node, next_nodes[0]
                        # I do this switcharoo thing because it will update previous_node too early otherwise, allowing an infinite loop.

    def stringify(self, highlighted_nodes:set[Node]) -> str:
        return "\n".join(
            "".join(
                str(node) if (node := self.nodes[x + y * self.width]) not in highlighted_nodes
                else "O"
                for x in range(self.width)) for y in range(self.height)
            )

    def __str__(self) -> str:
        return self.stringify(set())
    def __repr__(self) -> str:
        return "<Map %i×%i>" % (self.width, self.height)

def parse_map(document:str, is_slippery:bool) -> Map:
    nodes = list(flatten((Node(x, y, char, is_slippery) for x, char in enumerate(line)) for y, line in enumerate(document.split("\n"))))
    width = max(node.x for node in nodes) + 1
    height = max(node.y for node in nodes) + 1
    nodes_dict:dict[tuple[int,int],Node] = {(node.x, node.y): node for node in nodes}
    for node in nodes:
        node.set_neighbors(nodes_dict, is_slippery)
    return Map(nodes, width, height, is_slippery)

def find_hikes_recursive(start_junction:Junction, previous_junction:Junction|None, goal_junction:Junction, already_visited:set[Junction]) -> list[int]:
    output:list[int] = []
    for trail, trail_length in start_junction.trails:
        if trail is previous_junction: continue
        if trail in already_visited: continue
        new_already_visited = already_visited.copy()
        new_already_visited.add(start_junction)
        if trail is goal_junction:
            output.append(trail_length)
        else:
            output.extend(trail_length + next_trail for next_trail in find_hikes_recursive(trail, start_junction, goal_junction, new_already_visited))
    return output

def find_all_hikes(junctions:list[Junction], start_node:Node, end_node:Node) -> int:
    '''Returns the longest path from the given junctions.'''
    start_junction = [junction for junction in junctions if junction.node is start_node][0]
    end_junction = [junction for junction in junctions if junction.node is end_node][0]
    return find_hikes_recursive(start_junction, None, end_junction, set())

def main() -> None:
    document_string = load_document("Input.txt")
    map = parse_map(document_string, is_slippery=True)
    junctions = list(map.junctions.values())
    print("Part 1: %i" % max(find_all_hikes(junctions, map.start_node, map.end_node)))
    map = parse_map(document_string, is_slippery=False)
    junctions = list(map.junctions.values())
    print("Part 2: %i" % max(find_all_hikes(junctions, map.start_node, map.end_node))) # Only takes a minute or so

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()
