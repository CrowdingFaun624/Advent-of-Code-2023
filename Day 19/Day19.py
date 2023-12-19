from pathlib2 import Path
from typing import Callable, Union

def load_document(name:str) -> str:
    if isinstance(name, str):
        name = parent_path.joinpath(name)
    path = Path(name)
    if parent_path not in path.parents:
        raise FileNotFoundError("File is not in the correct directory!")
    with open(path, "rt") as file:
        return file.read()

EXTREMELY_COOL_LOOKING = "x"
MUSICAL = "m"
AERODYNAMIC = "a"
SHINY = "s"
CATEGORIES = [EXTREMELY_COOL_LOOKING, MUSICAL, AERODYNAMIC, SHINY]

ACCEPTED = "A"
REJECTED = "R"

LESS_THAN = "<"
GREATER_THAN = ">"
COMPARISONS = [LESS_THAN, GREATER_THAN]

class Part():
    def __init__(self, extremely_cool_looking:int, musical:int, aerodynamic:int, shiny:int) -> None:
        if not isinstance(extremely_cool_looking, int):
            raise TypeError("`extremely_cool_looking` is not an int!")
        if extremely_cool_looking < 1:
            raise ValueError("`extremely_cool_looking` is less than 1!")
        if not isinstance(musical, int):
            raise TypeError("`musical` is not an int!")
        if musical < 1:
            raise ValueError("`musical` is less than 1!")
        if not isinstance(aerodynamic, int):
            raise TypeError("`aerodynamic` is not an int!")
        if aerodynamic < 1:
            raise ValueError("`aerodynamic` is less than 1!")
        if not isinstance(shiny, int):
            raise TypeError("`shiny` is not an int!")
        if shiny < 1:
            raise ValueError("`shiny` is less than 1!")
        
        self.extremely_cool_looking = extremely_cool_looking
        self.musical = musical
        self.aerodynamic = aerodynamic
        self.shiny = shiny
    
    def __str__(self) -> str:
        return "{x=%i,m=%i,a=%i,s=%i}" % (self.extremely_cool_looking, self.musical, self.aerodynamic, self.shiny)
    def __repr__(self) -> str:
        return "<Part %i, %i, %i, %i>" % (self.extremely_cool_looking, self.musical, self.aerodynamic, self.shiny)

class PartRange():
    def __init__(self, attributes:dict[str,tuple[int,int]]) -> None:
        if not isinstance(attributes, dict):
            raise TypeError("`attributes` is not a dict!")
        if len(attributes) != 4:
            raise ValueError("`attributes` is not length 4!")
        if any(not isinstance(attribute_name, str) for attribute_name in attributes):
            raise TypeError("A key of `attributes` is not a str!")
        if any(not any(category is category_option for category_option in CATEGORIES) for category in attributes):
            raise ValueError("A key of `attributes` is not a reference to an item in `CATEGORIES`!")
        if any(not isinstance(attribute_value, tuple) for attribute_value in attributes.values()):
            raise TypeError("A value of `attributes` is not a tuple!")
        if any(len(attribute_value) != 2 for attribute_value in attributes.values()):
            raise ValueError("A value of `attributes` is not length 2!")
        if any(not isinstance(attribute_value[0], int) or not isinstance(attribute_value[1], int) for attribute_value in attributes.values()):
            raise TypeError("An item of a value of `attributes` is not an int!")
        if any(attribute_value[0] < 1 or attribute_value[1] < 1 for attribute_value in attributes.values()):
            raise ValueError("`An item of a value of `attributes` is less than 1!")
        if any(attribute_value[0] > attribute_value[1] for attribute_value in attributes.values()):
            raise ValueError("`A value of `attributes` is not sorted!")
        
        self.attributes = attributes
    
    def __len__(self) -> int: # total number of combinations.
        product = 1
        for attribute_min, attribute_max in self.attributes.values():
            product *= (1 - attribute_min + attribute_max)
        return product

class Rule():
    def __init__(self, category:str, comparison:str, number:int, destination_str:str) -> None:
        if not isinstance(category, str):
            raise TypeError("`category` is not a str!")
        if not any(category is category_option for category_option in CATEGORIES):
            raise ValueError("`category` is not a reference to an item in `CATEGORIES`!")
        if not isinstance(comparison, str):
            raise TypeError("`comparison` is not a str!")
        if not any(comparison is comparison_option for comparison_option in COMPARISONS):
            raise ValueError("`comparison` is not a reference to an item in `COMPARISONS`!")
        if not isinstance(number, int):
            raise TypeError("`number` is not an int!")
        if number < 1:
            raise ValueError("`number` is less than 1!")
        if not isinstance(destination_str, str):
            raise TypeError("`destination_str` is not a str!")
        if len(destination_str) == 0:
            raise ValueError("`destination_str` is empty!")
        if not destination_str.isalpha():
            raise ValueError("`destination_str` is not alpha!")

        self.category = category
        self.comparison = comparison
        self.number = number
        self.destination_str = destination_str
        if destination_str is ACCEPTED:
            self.destination = ACCEPTED
        elif destination_str is REJECTED:
            self.destination = REJECTED
        else:
            self.destination:Workflow|str|None = None

        self.part_goes_through:Callable[[Part],bool]
        # Match: case made it do something completely random and unexpected, so not using that.
        if self.comparison is GREATER_THAN and self.category is EXTREMELY_COOL_LOOKING:
                self.part_goes_through = lambda part: part.extremely_cool_looking > self.number
        elif self.comparison is LESS_THAN and self.category is EXTREMELY_COOL_LOOKING:
                self.part_goes_through = lambda part: part.extremely_cool_looking < self.number
        elif self.comparison is GREATER_THAN and self.category is MUSICAL:
                self.part_goes_through = lambda part: part.musical > self.number
        elif self.comparison is LESS_THAN and self.category is MUSICAL:
                self.part_goes_through = lambda part: part.musical < self.number
        elif self.comparison is GREATER_THAN and self.category is AERODYNAMIC:
                self.part_goes_through = lambda part: part.aerodynamic > self.number
        elif self.comparison is LESS_THAN and self.category is AERODYNAMIC:
                self.part_goes_through = lambda part: part.aerodynamic < self.number
        elif self.comparison is GREATER_THAN and self.category is SHINY:
                self.part_goes_through = lambda part: part.shiny > self.number
        elif self.comparison is LESS_THAN and self.category is SHINY:
                self.part_goes_through = lambda part: part.shiny < self.number
    
    def pass_part_range(self, part_range:PartRange) -> dict[bool,PartRange]:
        part_range_min, part_range_max = part_range.attributes[self.category]
        if self.comparison is GREATER_THAN:
            number_is_within = self.number >= part_range_min and self.number < part_range_max
        else:
            number_is_within = self.number > part_range_min and self.number <= part_range_max
        if number_is_within:
            # The number is between the min and max and it must be split.
            if self.comparison is GREATER_THAN:
                false_part_range_attributes = part_range.attributes.copy()
                false_part_range_attributes[self.category] = (part_range_min, self.number)
                true_part_range_attributes = part_range.attributes.copy()
                true_part_range_attributes[self.category] = (self.number + 1, part_range_max)
                return {False: PartRange(false_part_range_attributes), True: PartRange(true_part_range_attributes)}
            else:
                false_part_range_attributes = part_range.attributes.copy()
                false_part_range_attributes[self.category] = (self.number, part_range_max)
                true_part_range_attributes = part_range.attributes.copy()
                true_part_range_attributes[self.category] = (part_range_min, self.number - 1)
                return {False: PartRange(false_part_range_attributes), True: PartRange(true_part_range_attributes)}
        else:
            if self.comparison is GREATER_THAN:
                result = part_range_min > self.number
            else:
                result = part_range_max < self.number
            return {result: part_range}
    
    def __repr__(self) -> str:
        return "<Rule %s%s%i:%s>" % (self.category, self.comparison, self.number, self.destination_str)
    def __str__(self) -> str:
        return "%s%s%i:%s" % (self.category, self.comparison, self.number, self.destination_str)

class EndingRule(Rule):
    def __init__(self, destination_str:str) -> None:
        if not isinstance(destination_str, str):
            raise TypeError("`destination_str` is not a str!")
        if len(destination_str) == 0:
            raise ValueError("`destination_str` is empty!")
        if not destination_str.isalpha():
            raise ValueError("`destination_str` is not alpha!")
        
        self.destination_str = destination_str
        if destination_str is ACCEPTED:
            self.destination = ACCEPTED
        elif destination_str is REJECTED:
            self.destination = REJECTED
        else:
            self.destination:Workflow|str|None = None
    
    def part_goes_through(self, part:Part) -> bool:
        return True
    def pass_part_range(self, part_range:PartRange) -> dict[bool,PartRange]:
        return {True: part_range}
    
    def __repr__(self) -> str:
        return "<EndingRule %s>" % self.destination_str
    def __str__(self) -> str:
        return self.destination_str

class Workflow():
    def __init__(self, name:str, rules:list[Rule]) -> None:
        self.name = name
        self.rules = rules
    
    def part_goes_through(self, part:Part) -> Union[str,"Workflow"]:
        '''Returns `ACCEPTED`, `REJECTED`, or another Workflow.'''
        for rule in self.rules:
            rule_success = rule.part_goes_through(part)
            if rule_success:
                return rule.destination
            else: continue
        else:
            raise RuntimeError("The last rule of workflow \"%s\" returned False!" % self.name)
    
    def part_all_the_way_through(self, part:Part) -> str:
        '''Returns `ACCEPTED` or `REJECTED` and the workflows the part went through.'''
        workflow = self
        while True:
            part_destination = workflow.part_goes_through(part)
            if isinstance(part_destination, Workflow):
                workflow = part_destination
                continue
            else:
                return part_destination
    
    def __repr__(self) -> str:
        return "<Workflow %s len %i>" % (self.name, len(self.rules))
    def __str__(self) -> str:
        return "%s{%s}" % (self.name, ",".join(str(rule) for rule in self.rules))

def parse_input(document:str) -> tuple[dict[str,Workflow],list[Part]]:
    workflows_str, parts_str = document.split("\n\n")
    workflows:dict[str,Workflow] = {}
    for workflow_str in workflows_str.split("\n"):
        name, rules_str = workflow_str.split("{")
        rules_str = rules_str.rstrip("}")
        rules:list[Rule] = []
        rules_count = rules_str.count(",")
        for rule_index, rule_str in enumerate(rules_str.split(",")):
            if rule_index == rules_count:
                rules.append(EndingRule(rule_str))
            else:
                destination_str = rule_str.split(":")[1]
                if destination_str == ACCEPTED: destination_str = ACCEPTED # make it a reference yay
                elif destination_str == REJECTED: destination_str = REJECTED
                category = rule_str[0]
                comparison = rule_str[1]
                number = rule_str.split(comparison)[1].split(":")[0]
                rules.append(Rule(category, comparison, int(number), destination_str))
        workflows[name] = Workflow(name, rules)
    for name, workflow in workflows.items():
        for rule in workflow.rules:
            if rule.destination is ACCEPTED or rule.destination is REJECTED:
                continue
            else:
                rule.destination = workflows[rule.destination_str]

    parts:list[Part] = []
    for part_str in parts_str.split("\n"):
        part_str = part_str.strip("{}")
        extremely_cool_looking, musical, aerodynamic, shiny = None, None, None, None
        for category in part_str.split(","):
            category_name, number = category.split("=")
            number = int(number)
            # match: case doesn't work for some reason
            if category_name == EXTREMELY_COOL_LOOKING: extremely_cool_looking = number
            elif category_name == MUSICAL: musical = number
            elif category_name == AERODYNAMIC: aerodynamic = number
            elif category_name == SHINY: shiny = number
        parts.append(Part(extremely_cool_looking, musical, aerodynamic, shiny))
    return workflows, parts

def pass_all_parts(workflows:dict[str,Workflow], parts:list[Part], first_workflow:Workflow|None=None) -> list[Part]:
    '''Returns the list of accepted Parts.'''
    first_workflow = workflows["in"] if first_workflow is None else first_workflow
    accepted_parts:list[Part] = []
    for part in parts:
        workflow = first_workflow
        part_result = workflow.part_all_the_way_through(part)
        if part_result is ACCEPTED:
            accepted_parts.append(part)
        elif part_result is REJECTED:
            continue
        else: raise RuntimeError("Part is neither accepted nor rejected, but \"%s\"!" % str(part_result))
    return accepted_parts

def pass_all_part_ranges(workflows:dict[str,Workflow], part_range:list[PartRange]|None=None, workflow:Workflow|None=None) -> int:
    '''Returns the number of accepted parts.'''
    workflow = workflows["in"] if workflow is None else workflow
    part_range = PartRange({EXTREMELY_COOL_LOOKING: (1,4000), MUSICAL: (1,4000), AERODYNAMIC: (1,4000), SHINY: (1,4000)}) if part_range is None else part_range
    # `part_range` will be the part range that stays in this workflow.
    total = 0
    for rule in workflow.rules:
        split_part_range = rule.pass_part_range(part_range)
        for rule_result, new_part_range in split_part_range.items():
            if rule_result is True:
                if rule.destination is ACCEPTED:
                    total += len(new_part_range)
                elif rule.destination is REJECTED:
                    continue # This effectively deletes this range, since nothing about it counts towards the total.
                else:
                    total += pass_all_part_ranges(workflows, new_part_range, rule.destination)
            else:
                part_range = new_part_range # This will be looked at in the next rule. Since it is False, it goes to the next rule.
    return total

def main() -> None:
    document_string = load_document("Input.txt")
    workflows, parts = parse_input(document_string)
    accepted_parts = pass_all_parts(workflows, parts)
    print("Part 1: %i" % sum(part.extremely_cool_looking + part.musical + part.aerodynamic + part.shiny for part in accepted_parts))
    print("Part 2: %i" % pass_all_part_ranges(workflows))

if __name__ == "__main__":
    parent_path:Path = Path(__file__).parent
    main()
