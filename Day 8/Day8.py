from math import lcm
from pathlib import Path

def load_document(name:str) -> str:
    if isinstance(name, str):
        name = parent_path.joinpath(name)
    path = Path(name)
    if parent_path not in path.parents:
        raise FileNotFoundError("File is not in the correct directory!")
    with open(path, "rt") as file:
        return file.read()

RIGHT = "R"
LEFT = "L"

class Node():
    def __init__(self, name:str) -> None:
        '''Sets the node's name only. The left and right are set later.'''
        self.name = name
        self.left = None
        self.right = None
    
    def set_connections(self, left:"Node", right:"Node") -> None:
        self.left = left
        self.right = right
    
    def follow(self, direction:str) -> "Node":
        if direction is RIGHT: return self.right
        elif direction is LEFT: return self.left
        else: raise ValueError("Direction is not `RIGHT` or `LEFT`!")
    
    def __repr__(self) -> str:
        return "<Node %s (%s, %s)>" % (self.name, self.left.name, self.right.name)

class Map():
    def __init__(self, instructions:list[str], nodes:list[Node], AAA_node:Node, ZZZ_node:Node, A_nodes:list[Node], Z_nodes:list[Node]) -> None:
        if not isinstance(instructions, list):
            raise TypeError("`instructions` is not a list!")
        if not isinstance(nodes, list):
            raise TypeError("`nodes` is not a list!")
        if not all(isinstance(instruction, str) for instruction in instructions):
            raise TypeError("`instructions` contains items that are not strs!")
        if not all(instruction is RIGHT or instruction is LEFT for instruction in instructions):
            raise ValueError("`instructions` contains items that are not `RIGHT` or `LEFT`!")
        if not all(isinstance(node, Node) for node in nodes):
            raise TypeError("`nodes` contains items that are not Nodes!")
        if AAA_node is not None and not isinstance(AAA_node, Node): # checking for None so that Example3.txt doesn't error
            raise TypeError("`AAA_node` is not a Node!")
        if ZZZ_node is not None and not isinstance(ZZZ_node, Node):
            raise TypeError("`ZZZ_node` is not a Node!")
        if not isinstance(A_nodes, list):
            raise TypeError("`A_nodes` is not a list!")
        if not isinstance(Z_nodes, list):
            raise TypeError("`Z_nodes` is not a list!")
        if not all(isinstance(node, Node) for node in A_nodes):
            raise TypeError("`A_nodes` contains items that are not Nodes!")
        if not all(isinstance(node, Node) for node in Z_nodes):
            raise TypeError("`Z_nodes` contains items that are not Nodes!")

        self.instructions = instructions
        self.nodes = nodes
        self.AAA_node = AAA_node
        self.ZZZ_node = ZZZ_node
        self.A_nodes = A_nodes
        self.Z_nodes = Z_nodes
    
    def __getitem__(self, index:int) -> Node:
        return self.instructions[index % len(self.instructions)]
    def get_mod_index(self, index:int) -> int:
        return index % len(self.instructions)
    
    def __repr__(self) -> str:
        return "<Map instr-len %i node-len %i>" % (len(self.instructions), len(self.nodes))

class Ghost():
    def __init__(self, start_node:Node) -> None:
        if not isinstance(start_node, Node):
            raise TypeError("`start_node` is not a Node!")
        
        self.node = start_node
        self.visited_nodes:dict[tuple[Node,int],int] = {} # the tuple is (node, instruction_index_mod)
        self.has_found_cycle = False
        self.cycle_length = None

    def follow(self, direction:str, instruction_index:int, instruction_index_mod:int) -> None:
        new_node = self.node.follow(direction)
        self.node = new_node
        if not self.has_found_cycle and (new_node, instruction_index_mod) in self.visited_nodes:
            self.has_found_cycle = True
            self.cycle_length = instruction_index - self.visited_nodes[(new_node, instruction_index_mod)]
        if not self.has_found_cycle:
            self.visited_nodes[(new_node, instruction_index_mod)] = instruction_index

def parse_map(document:str) -> Map:
    lines = document.split("\n")
    assert lines[1] == ""
    instruction_line = lines[0]
    node_lines = lines[2:]

    instructions:list[str] = []
    for char in instruction_line:
        match char:
            case "R":
                instructions.append(RIGHT)
            case "L":
                instructions.append(LEFT)
            case _:
                raise ValueError("Instructions contains a value that is not \"R\" or \"L\"!")
    
    nodes_str:dict[str,tuple[str,str,Node]] = {}
    for line in node_lines:
        node_name, node_connections = line.split(" = ")
        node_left, node_right = node_connections.split(", ")
        node_left = node_left.strip("( ")
        node_right = node_right.strip(" )")
        assert node_left.isalnum()
        assert node_right.isalnum()
        assert node_name.isalnum()
        assert node_name not in nodes_str
        nodes_str[node_name] = (node_left, node_right, Node(node_name))
    nodes:list[Node] = []
    AAA_node = None
    ZZZ_node = None
    A_nodes:list[Node] = []
    Z_nodes:list[Node] = []
    for node_name, node_properties in nodes_str.items():
        node_str_left, node_str_right, node = node_properties

        if node.name == "AAA": AAA_node = node
        elif node.name == "ZZZ": ZZZ_node = node
        if node.name.endswith("A"): A_nodes.append(node)
        elif node.name.endswith("Z"): Z_nodes.append(node)

        node_left = nodes_str[node_str_left][2]
        node_right = nodes_str[node_str_right][2]
        node.set_connections(node_left, node_right)
        nodes.append(node)
    assert len(A_nodes) == len(Z_nodes)
    
    return Map(instructions, nodes, AAA_node=AAA_node, ZZZ_node=ZZZ_node, A_nodes=A_nodes, Z_nodes=Z_nodes)

def follow_aaa(map:Map) -> int:
    '''Returns the number of steps it takes to reach ZZZ from AAA.'''
    node = map.AAA_node
    instruction_index = 0
    while node is not map.ZZZ_node:
        node = node.follow(map[instruction_index])
        instruction_index += 1
    return instruction_index

def follow_a(map:Map) -> list[int]:
    '''Returns the number of steps it takes for each ghosts to enter a cycle.'''
    ghosts = [Ghost(node) for node in map.A_nodes]
    # z_nodes = set(map.Z_nodes)

    instruction_index = 0
    while not all(ghost.has_found_cycle for ghost in ghosts):
        instruction = map[instruction_index]
        instruction_index_mod = map.get_mod_index(instruction_index)
        for ghost in ghosts:
            ghost.follow(instruction, instruction_index, instruction_index_mod)
        instruction_index += 1
    ghost_lengths = [ghost.cycle_length for ghost in ghosts]
    return ghost_lengths

def main() -> None:
    document_string = load_document("Input.txt")
    map = parse_map(document_string)
    aaa_to_zzz_length = follow_aaa(map)
    print("Part 1: %i" % aaa_to_zzz_length)
    ghost_cycle_lengths = follow_a(map)
    print("Part 2: %i" % lcm(*ghost_cycle_lengths))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()
