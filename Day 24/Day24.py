from fractions import Fraction
from pathlib2 import Path
from typing import Any, Generator, Iterable, TypeVar
import z3

def load_document(name:str) -> str:
    if isinstance(name, str):
        name = parent_path.joinpath(name)
    path = Path(name)
    if parent_path not in path.parents:
        raise FileNotFoundError("File is not in the correct directory!")
    with open(path, "rt") as file:
        return file.read()

Pair=TypeVar("Pair")
def get_pairs(_list:Iterable[Pair]) -> Generator[tuple[Pair,Pair],None,None]:
    for index, item in enumerate(_list):
        yield from ((item, _list[sub_index]) for sub_index in range(index + 1, len(_list)))

class Linear():
    def __init__(self, m:Fraction, b:Fraction) -> None:
        if not isinstance(m, Fraction):
            raise TypeError("`m` is not a Fraction!")
        if not isinstance(b, Fraction):
            raise TypeError("`b` is not a Fraction!")

        self.m = m
        self.b = b
    
    def __str__(self) -> str:
        return "%sx+%s" % (self.m, self.b)
    def __repr__(self) -> str:
        return "<Linear %s>" % str(self)
    def __call__(self, x:int|Fraction) -> Fraction:
        return self.m * x + self.b

    def solve_system(self, other:"Linear") -> "Linear":
        '''solves for y in y=self, x=other'''
        return Linear(self.m / other.m, self.b - self.m * other.b / other.m)
    
    def get_intersection(self, other:"Linear") -> tuple[Fraction,Fraction]|bool:
        '''Returns (x, y) where self=other, True if they are parallel and touching, and False if they are parallel and not touching.'''
        if self.m == other.m:
            return self.b == other.b
        sum_linear = Linear(self.m - other.m, self.b - other.b)
        # solve for sum_linear=0
        intersect_x = -sum_linear.b / sum_linear.m
        intersect_y1 = self(intersect_x)
        intersect_y2 = other(intersect_x)
        assert intersect_y1 == intersect_y2
        return intersect_x, intersect_y1

class Hailstone():
    def __init__(self, px:Fraction, py:Fraction, pz:Fraction, vx:Fraction, vy:Fraction, vz:Fraction) -> None:
        for label, value, is_position in (("x", px, True), ("y", py, True), ("z", pz, True), ("vx", vx, False), ("vy", vy, False), ("vz", vz, False)):
            if not isinstance(value, Fraction):
                raise TypeError("`%s` is not a Fraction!" % label)
            if is_position and value < 0:
                raise ValueError("`%s` is less than 0!" % label)

        self.px = px
        self.py = py
        self.pz = pz
        self.vx = vx
        self.vy = vy
        self.vz = vz

        self.line_x = Linear(vx, px)
        self.line_y = Linear(vy, py)
        self.line_z = Linear(vz, pz)
        self.line_yx = self.line_y.solve_system(self.line_x)
    
    def get_intersection(self, other:"Hailstone") -> tuple[Fraction,Fraction,Fraction,Fraction]|bool:
        '''Returns (x, y, t_self, t_other) where self.lineyx=other.lineyx, True if they are parallel and touching, and False if they are parallel and not touching.'''
        intersection = self.line_yx.get_intersection(other.line_yx)
        if isinstance(intersection, bool): return intersection
        else:
            intersect_x, intersect_y = intersection
            t_self = self.line_y.get_intersection(Linear(Fraction(), intersect_y))[0]
            t_other = other.line_y.get_intersection(Linear(Fraction(), intersect_y))[0]
            return intersection[0], intersection[1], t_self, t_other

    def __call__(self, t:int) -> tuple[int,int,int]:
        '''Returns the x, y, z coords for this hailstone when t=t.'''
        return self.line_x(t), self.line_y(t), self.line_z(t)

    def __str__(self) -> str:
        return "%i, %i, %i @ %i, %i, %i" % (self.px, self.py, self.pz, self.vx, self.vy, self.vz)
    def __repr__(self) -> str:
        return "<%s>" % str(self)
    def __hash__(self) -> int:
        return hash((self.px, self.py, self.pz, self.vx, self.vy, self.vz))

def parse_hailstones(document:str) -> tuple[list[Hailstone],int,int]:
    '''Returns a list of Hailstones, the test area min, and the test area max.'''
    hailstones:list[Hailstone] = []
    for line_index, line in enumerate(document.split("\n")):
        if line_index == 0:
            test_area_min, test_area_max = map(int, line.split(", "))
            continue
        positions_str, velocities_str = line.split(" @ ")
        px, py, pz = map(Fraction, map(int, positions_str.split(", ")))
        vx, vy, vz = map(Fraction, map(int, velocities_str.split(", ")))
        hailstones.append(Hailstone(px, py, pz, vx, vy, vz))
    return hailstones, test_area_min, test_area_max

def get_valid_intersections(hailstones:list[Hailstone], test_area_min:int, test_area_max:int, debug_mode:bool=False) -> list[tuple[Hailstone,Hailstone]]:
    '''Returns the list of pairs of Hailstones that collide within the test area.'''
    output:list[tuple[Hailstone, Hailstone]] = []
    for hailstone1, hailstone2 in get_pairs(hailstones):
        if debug_mode:
            print("Hailstone A: %s" % hailstone1)
            print("Hailstone B: %s" % hailstone2)
        intersection = hailstone1.get_intersection(hailstone2)
        if intersection is True: raise RuntimeError("Hailstones \"%s\" and \"%s\" are equal!\n")
        if intersection is False:
            if debug_mode: print("Hailstones' paths are parallel; they never intersect.\n")
            continue # Parallel and not equal
        intersect_x, intersect_y, t_a, t_b = intersection
        if debug_mode:
            if t_a < 0 and t_b < 0:
                print("Hailstones' paths crossed in the past for both hailstones.\n")
            elif t_a < 0:
                print("Hailstones' paths crossed in the past for hailstone A.\n")
            elif t_b < 0:
                print("Hailstones' paths crossed in the past for hailstone B.\n")
            elif intersect_x > test_area_min and intersect_x < test_area_max and intersect_y > test_area_min and intersect_y < test_area_max:
                print("Hailstones' paths will cross inside the test area (at x=%.3f, y=%.3f).\n" % (intersect_x, intersect_y))
            else:
                print("Hailstones' paths will cross outside the test area (at x=%.3f, y=%.3f).\n" % (intersect_x, intersect_y))
        if t_a == 0 or t_b == 0:
            raise RuntimeError("Hailstones' paths crossed at t=0!")
        if intersect_x == test_area_min or intersect_x == test_area_max or intersect_y == test_area_min or intersect_y == test_area_max:
            raise RuntimeError("Hailstones' paths crossed on the border of the test area!")
        if intersect_x > test_area_min and intersect_x < test_area_max and intersect_y > test_area_min and intersect_y < test_area_max and t_a > 0 and t_b > 0:
            output.append((hailstone1, hailstone2))
    return output

def get_rock_intersections(hailstones:list[Hailstone], rock_px:int, rock_py:int, rock_pz:int, rock_vx:int, rock_vy:int, rock_vz:int, max_steps:int) -> dict[int,Hailstone]:
    '''Returns the times and hailstones that the rock intersects hailstones at.'''
    output:dict[int,Hailstone] = {}
    hailstone_positions = {hailstone: (hailstone.px, hailstone.py, hailstone.pz) for hailstone in hailstones}
    for step in range(max_steps):
        rock_px += rock_vx
        rock_py += rock_vy
        rock_pz += rock_vz
        for hailstone, position in hailstone_positions.items():
            hailstone_px, hailstone_py, hailstone_pz = position
            hailstone_px += hailstone.vx
            hailstone_py += hailstone.vy
            hailstone_pz += hailstone.vz
            hailstone_positions[hailstone] = (hailstone_px, hailstone_py, hailstone_pz)
            if (hailstone_px, hailstone_py, hailstone_pz) == (rock_px, rock_py, rock_pz):
                assert step + 1 not in output
                output[step + 1] = hailstone
    return output

def get_common_line(hailstones:list[Hailstone]) -> tuple[int,int,int]:
    # Select the four hailstones with the least positions.
    selected_hailstones = [item[1] for item in sorted((hailstone.px * hailstone.py * hailstone.pz, hailstone, ) for hailstone in hailstones)[0:4]]
    # Unfortunately, I have not learned linear algebra yet.
    rock_px = z3.Const("rock_px", sort=z3.IntSort())
    rock_py = z3.Const("rock_py", sort=z3.IntSort())
    rock_pz = z3.Const("rock_pz", sort=z3.IntSort())
    rock_vx = z3.Const("rock_vx", sort=z3.IntSort())
    rock_vy = z3.Const("rock_vy", sort=z3.IntSort())
    rock_vz = z3.Const("rock_vz", sort=z3.IntSort())

    hailstone_variables = [(z3.Const("t%i" % index, sort=z3.IntSort()), hailstone) for index, hailstone in enumerate(selected_hailstones)] # time that rock hits each hailstone

    solver = z3.Solver()
    for t, hailstone in hailstone_variables:
        solver.add(
            rock_px + t * rock_vx == int(hailstone.px) + t * int(hailstone.vx),
            rock_py + t * rock_vy == int(hailstone.py) + t * int(hailstone.vy),
            rock_pz + t * rock_vz == int(hailstone.pz) + t * int(hailstone.vz),
            t > 0
            )
    solver.check()
    model = solver.model()
    return int(str(model[rock_px])), int(str(model[rock_py])), int(str(model[rock_pz]))

def main() -> None:
    document_string = load_document("Input.txt")
    hailstones, test_area_min, test_area_max = parse_hailstones(document_string)
    intersections = get_valid_intersections(hailstones, test_area_min, test_area_max, debug_mode=False)
    print("Part 1: %i" % len(intersections))
    print("Part 2: %i" % sum(get_common_line(hailstones)))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()
