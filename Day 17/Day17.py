import cProfile
from pathlib2 import Path
import queue

def load_document(name:str) -> str:
    if isinstance(name, str):
        name = parent_path.joinpath(name)
    path = Path(name)
    if parent_path not in path.parents:
        raise FileNotFoundError("File is not in the correct directory!")
    with open(path, "rt") as file:
        return file.read()

NORTH = 0
SOUTH = 1
WEST = 2
EAST = 3

DIRECTION_VECTORS = {NORTH: (0, -1), SOUTH: (0, 1), WEST: (-1, 0), EAST: (1, 0)}
OPPOSITE_DIRECTIONS = {NORTH: SOUTH, SOUTH: NORTH, WEST: EAST, EAST: WEST}

class Map():
    def __init__(self, tiles:list[list[int]]) -> None:
        if not isinstance(tiles, list):
            raise TypeError("`tiles` is not a list!")
        if len(tiles) == 0:
            raise ValueError("`tiles` is empty!")
        if any(not isinstance(row, list) for row in tiles):
            raise TypeError("`tiles` has an item that is not a list!")
        if any(len(row) != len(tiles[0]) for row in tiles):
            raise ValueError("`tiles` has an item that is a different length to another!")
        if len(tiles[0]) == 0: # I already know they're all the same length.
            raise ValueError("`tiles` has an item that is empty!")
        if any(any(not isinstance(item, int) for item in row) for row in tiles):
            raise TypeError("`tiles` has an item that has an item that is not an int!")
        if any(any(item < 1 or item > 9 for item in row) for row in tiles):
            raise ValueError("`tiles` has an item that has an item that is not in [1,9]!")

        self.tiles = tiles
        self.height = len(self.tiles)
        self.width = len(self.tiles[0])

    def __repr__(self) -> str:
        return "<Map %i×%i>" % (self.width, self.height)
    def __str__(self) -> str:
        return "\n".join("".join(str(char) for char in row) for row in self.tiles)
    
    def __getitem__(self, position:tuple[int,int]) -> int:
        return self.tiles[position[1]][position[0]]
    
    def stringify_path(self, path:list[tuple[int,int,int,int]]) -> str:
        path_set = set((x, y) for x, y, _, _ in path)
        return "\n".join("".join("#" if (x, y) in path_set else "." for x, char in enumerate(row)) for y, row in enumerate(self.tiles))

def parse_map(document:str) -> Map:
    return Map([[int(char) for char in row] for row in document.split("\n")])

def get_node_neighbors(node:tuple[int,int,int,int], map:Map, min_speed:int, max_speed:int) -> list[tuple[int,int,int,int]]:
    '''Returns all of the neighbors of the given position, except for those that are out of bounds.
    Returns `[(x, y, direction, speed)]`.'''
    x, y, direction, speed = node
    opposite_direction = OPPOSITE_DIRECTIONS[direction]
    output:list[tuple[int,int,int,int]] = []
    for neighbor_direction, neighbor_vector in DIRECTION_VECTORS.items():
        if neighbor_direction is opposite_direction: continue # can't go backwards.
        if speed >= max_speed and neighbor_direction is direction: continue # can't go more than 3 (or 10) in a row.
        if speed < min_speed and neighbor_direction is not direction: continue # can't turn for 4 tiles (ultra crucibles.)
        neighbor_position = (x + neighbor_vector[0], y + neighbor_vector[1])
        if neighbor_position[0] < 0 or neighbor_position[0] >= map.width or neighbor_position[1] < 0 or neighbor_position[1] >= map.height:
            continue # out of bounds
        if neighbor_direction is direction:
            neighbor_speed = speed + 1
        else:
            neighbor_speed = 0
        output.append((neighbor_position[0], neighbor_position[1], neighbor_direction, neighbor_speed))
    return output

def get_initial_conditions(map:Map, initial_nodes:list[tuple[int,int,int,int]], destination_node:tuple[int,int], ultra_crucibles:bool) ->\
    tuple[set[tuple[int,int,int,int]], dict[tuple[int,int,int,int],int|float], dict[tuple[int,int,int,int],tuple[int,int,int,int]], list[tuple[int,int,int,int]], int, int]:
    '''Returns the initial values of `unvisited nodes`, `distances`, `path_from`, `destination_nodes`, `min_speed`, and `max_speed`.'''
    max_speed = {False: 2, True: 9}[ultra_crucibles]
    min_speed = {False: 0, True: 3}[ultra_crucibles]
    unvisited_nodes = {(x, y, direction, speed) for x in range(map.width) for y in range(map.height) for direction in DIRECTION_VECTORS for speed in range(max_speed + 1)}
    infinity = float("Infinity")
    distances = {(x, y, direction, speed): infinity for x in range(map.width) for y in range(map.height) for direction in DIRECTION_VECTORS for speed in range(max_speed + 1)}
    for initial_node in initial_nodes: distances[initial_node] = 0
    path_from = {(x, y, direction, speed): None for x in range(map.width) for y in range(map.height) for direction in DIRECTION_VECTORS for speed in range(max_speed + 1)}
    # Direction and speed are also very important to which nodes can be visited.
    # Inlcuding the direction and speed in each node makes this much more fluid.
    destination_nodes = [(destination_node[0], destination_node[1], direction, speed) for direction in DIRECTION_VECTORS for speed in range(min_speed, max_speed + 1)]
    # The destination node is actually twelve/forty (directions * speeds) different nodes. I must find the one with the least distance.
    # The range is (min_speed, max_speed+1) instead of just (max_speed+1) because it must be going at least min_speed in order to stop at the end.
    return unvisited_nodes, distances, path_from, destination_nodes, min_speed, max_speed

def get_node_path(initial_nodes:list[tuple[int,int,int,int]], destination_node:tuple[int,int,int,int], path_from:dict[tuple[int,int,int,int],tuple[int,int,int,int]]) -> list[tuple[int,int,int,int]]:
    '''Returns the path, in reverse, to get from the initial node to the destination node.'''
    current_node = destination_node
    path:list[tuple[int,int,int,int]] = [destination_node]
    while True:
        current_node = path_from[current_node]
        path.append(current_node)
        if current_node in initial_nodes:
            break
        if current_node is None:
            raise RuntimeError("No path exists from %s to %s!" % (str(initial_nodes), str(destination_node)))
    return path

def dijkstra(map:Map, initial_nodes:list[tuple[int,int,int,int]], destination_node:tuple[int,int], ultra_crucibles:bool) -> int:
    '''Returns the minimum possible heat loss when traversing this map.'''
    unvisited_nodes, distances, path_from, destination_nodes, min_speed, max_speed = get_initial_conditions(map, initial_nodes, destination_node, ultra_crucibles)
    infinity = float("Infinity")
    nodes_to_visit = queue.PriorityQueue()
    for initial_node in initial_nodes: nodes_to_visit.put((0, initial_node))

    current_node = initial_nodes[0]
    while True:
        if current_node not in initial_nodes and current_node not in unvisited_nodes:
            current_node = nodes_to_visit.get_nowait()[1]
            continue # The node has been visited between when it was put on the queue and now.
        if all(distances[destination] != infinity for destination in destination_nodes): break # All destination nodes have a distance.

        neighbors = get_node_neighbors(current_node, map, min_speed, max_speed)
        for neighbor in neighbors:
            neighbor_x, neighbor_y, _, _ = neighbor
            this_distance = distances[current_node] + map[neighbor_x, neighbor_y]
            if this_distance < distances[neighbor]:
                distances[neighbor] = this_distance
                path_from[neighbor] = current_node
            if neighbor in unvisited_nodes:
                nodes_to_visit.put_nowait((distances[neighbor], neighbor))
        if current_node not in initial_nodes: unvisited_nodes.remove(current_node)
        try:
            current_node = nodes_to_visit.get_nowait()[1]
        except queue.Empty: # The queue is empty and there are no more nodes that are possible to visit.
            break

    # destination_node = None # This commented code causes it to display the path it took.
    # for node in destination_nodes:
    #     if destination_node is None or distances[node] < distances[destination_node]:
    #         destination_node = node
    # print(map.stringify_path(get_node_path(initial_nodes, destination_node, path_from)))
    # return distances[destination_node]
    return min(distances[destination] for destination in destination_nodes)

def main() -> None:
    document_string = load_document("Input.txt")
    map = parse_map(document_string)
    print("Part 1: %i" % dijkstra(map, [(0,0,SOUTH,-1)], (map.width - 1, map.height - 1), ultra_crucibles=False))
    print("Part 2: %i" % dijkstra(map, [(0,0,SOUTH,-1), (0,0,EAST,-1)], (map.width - 1, map.height - 1), ultra_crucibles=True))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    # cProfile.run('main()')
    main()
