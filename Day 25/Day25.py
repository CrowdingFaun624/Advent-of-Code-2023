from collections import deque
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

Pairs = TypeVar("Pairs")
def get_trairs(_list:Iterable[Pairs]) -> Generator[tuple[Pairs, Pairs, Pairs],None,None]: # pairs between three objects
    for index1 in range(len(_list)):
        for index2 in range(index1, len(_list)):
            yield from ((_list[index1], _list[index2], _list[index3]) for index3 in range(index2, len(_list)))
def get_pairs(_list:Iterable[Pairs]) -> Generator[tuple[Pairs, Pairs],None,None]:
    for index1, item1 in enumerate(_list):
        yield from (((item1, _list[index2]) for index2 in range(index1, len(_list))))

class Component():
    def __init__(self, name:str, index:int, connections_str:list[str]) -> None:
        if not isinstance(name, str):
            raise TypeError("`name` is not a str!")
        if len(name) == 0:
            raise ValueError("`name` is empty!")
        if not isinstance(index, int):
            raise TypeError("`index` is not an int!")
        if index < 0:
            raise ValueError("`index` is less than 0!")
        if not isinstance(connections_str, list):
            raise TypeError("`connections_str` is not a list!")
        if not all(isinstance(connection_str, str) for connection_str in connections_str):
            raise TypeError("An item of `connections_str` is not a str!")
        if any(len(connection_str) == 0 for connection_str in connections_str):
            raise ValueError("An item of `connections_str` is empty!")
        
        self.name = name
        self.index = index
        self.connections_str = connections_str
        self.connections:list[tuple[Connection,Component]] = []
    
    def __lt__(self, other:"Component") -> bool:
        return self.name < other.name
    def __repr__(self) -> str:
        return "<Component %s>" % self.name
    def __str__(self) -> str:
        return "%s: %s" % (self.name, " ".join(self.connections_str))
    def __hash__(self) -> int:
        return hash(self.name)

class Connection():
    def __init__(self, component1:Component, component2:Component, index:int) -> None:
        if not isinstance(component1, Component):
            raise TypeError("`component1` is not a Component!")
        if not isinstance(component2, Component):
            raise TypeError("`component2` is not a Component!")
        if component1 is component2:
            raise ValueError("`component1` is `component2`!")
        if not isinstance(index, int):
            raise TypeError("`index` is not an int!")
        if index < 0:
            raise ValueError("`index` is less than 0!")
        
        self.component1 = component1
        self.component2 = component2
        self.index = index
    
    def follow(self, from_component:Component) -> Component:
        '''Returns the Component in this Connection that is not `from_component`.'''
        return self.component2 if from_component is self.component1 else self.component1
    
    def __repr__(self) -> str:
        return "<Connection %s, %s>" % (self.component1.name, self.component2.name)
    def __str__(self) -> str:
        return "%s/%s" % (self.component1.name, self.component2.name)
    def __hash__(self) -> int: # This conditional is to make connections in reverse look the same.
        if self.component1.name > self.component2.name:
            return hash(self.component2, self.component1)
        else:
            return hash(self.component1, self.component2)

def parse_components(document:str) -> tuple[list[Component],list[Connection]]:
    all_components:dict[str,Component] = {} # All components, whether listed as having connections or not.
    for line in document.split("\n"):
        name, connections_str = line.split(": ")
        connections = connections_str.split(" ")
        if name not in all_components:
            all_components[name] = Component(name, len(all_components), connections)
        else:
            if len(all_components[name].connections_str) > 0:
                raise RuntimeError("Component \"%s\" was defined more than once!" % name)
            all_components[name].connections_str = connections
        for connection in connections:
            if connection not in all_components:
                all_components[connection] = Component(connection, len(all_components), [])

    all_connections:dict[tuple[str,str],Connection] = {}
    for component_name, component in all_components.items():
        if component.index > len(all_components):
            raise RuntimeError("Component \"%s\"'s index (%i) is greater than the length of `all_components` (%i)!" % (component_name, component.index, len(all_components)))
        for connected_component_name in component.connections_str:
            if component_name == connected_component_name:
                raise RuntimeError("Component \"%s\" is connected to itself!")
            if connected_component_name > component_name:
                connection_representation = (component_name, connected_component_name)
            else:
                connection_representation = (connected_component_name, component_name)
            if connection_representation in all_connections:
                raise RuntimeError("Connection between \"%s\" and \"%s\" was listed twice!" % connection_representation)
            connected_component = all_components[connected_component_name]
            connection = Connection(component, connected_component, len(all_connections))
            all_connections[connection_representation] = connection
            component.connections.append((connection, connected_component))
            connected_component.connections.append((connection, component))
    
    return list(all_components.values()), list(all_connections.values())

def create_graph_editor_input(connections:list[Connection]) -> None: # I used https://csacademy.com/app/graph_editor/ to look at the example.
    '''Writes to `./Day 25/GraphEditor.txt`.'''
    output = ""
    for connection in connections:
        output += "%s %s\n" % (connection.component1.name, connection.component2.name)
    with open("./Day 25/GraphEditor.txt", "wt") as f:
        f.write(output)

def solve_maze(start_component:Component, goal_component:Component, all_components:list[Component], ignore_connection:Connection) -> int:
    '''Returns the length from `start_component` to `goal_component` when ignoring `ignore_connection`.'''
    visited_nodes = [False] * len(all_components)
    distances:list[float|int] = [float("Infinity") for component in all_components]
    distances[start_component.index] = 0
    current_node = start_component
    while True:
        for connection, neighbor in current_node.connections:
            if connection is ignore_connection: continue
            if visited_nodes[neighbor.index]: continue
            new_distance = 1 + distances[current_node.index]
            distances[neighbor.index] = min(distances[neighbor.index], new_distance)
        visited_nodes[current_node.index] = True
        if distances[goal_component.index] != float("Infinity"):
            return distances[goal_component.index]
        minimum_distance_component = None
        minimum_distance = None
        for index, component in enumerate(all_components):
            if visited_nodes[index]: continue
            if minimum_distance is None or distances[component.index] < minimum_distance:
                minimum_distance_component = component
                minimum_distance = distances[component.index]
        current_node = minimum_distance_component

def get_three_connections(components:list[Component]) -> tuple[Connection,Connection,Connection]:
    distances:dict[tuple[Component,Component],int] = {}
    index = 0
    for component1 in components:
        for connection, component2 in component1.connections:
            if (component2, component1) in distances: continue
            index += 1
            distances[component1, component2] = solve_maze(component2, component1, components, connection)
    sorted_distances = [component_pair for distance, component_pair in sorted([(distance, component_pair) for component_pair, distance in distances.items()], reverse=True)]
    assert distances[sorted_distances[3]] != distances[sorted_distances[2]]
    remove_component_pairs = sorted_distances[:3]

    remove_connections:list[Connection] = []
    for remove_component_pair in remove_component_pairs:
        for connection, neighbor in remove_component_pair[0].connections:
            if neighbor is remove_component_pair[1]:
                remove_connections.append(connection)
                break
        else:
            raise RuntimeError("Connection between \"%s\" and \"%s\" does not exist!" % remove_component_pair)

    return tuple(remove_connections)

def get_separate_groups(components:list[Component], remove_connections:tuple[Connection]) -> tuple[set[Component],set[Component]]:
    output:list[set[Component]] = []
    for start_component in (remove_connections[0].component1, remove_connections[0].component2):
        will_visit_nodes:deque[Component] = deque([start_component])
        will_visit_nodes_set:set[Component] = set([start_component])
        visited_nodes:set[Component] = set()
        while len(will_visit_nodes) > 0:
            current_node = will_visit_nodes.popleft()
            will_visit_nodes_set.remove(current_node)
            visited_nodes.add(current_node)
            for connection, neighbor in current_node.connections:
                if connection in remove_connections: continue
                if neighbor in will_visit_nodes_set or neighbor in visited_nodes: continue
                will_visit_nodes.append(neighbor)
                will_visit_nodes_set.add(neighbor)
        output.append(visited_nodes)
    return tuple(output)


def main() -> None:
    document_string = load_document("Input.txt")
    components, connections = parse_components(document_string)
    remove_connections = get_three_connections(components)
    separate_groups = get_separate_groups(components, remove_connections)
    print("Part 1: %i" % (len(separate_groups[0]) * len(separate_groups[1])))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()
