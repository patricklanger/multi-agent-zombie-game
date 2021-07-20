import random as r
from zombie import Zombie
from guy import Guy


def modify_part_of_world(world, color, center_xcor, center_ycor, size):
    radius = int(size / 2)
    top = int(center_xcor + radius)
    bottom = int(center_xcor - radius)
    left = int(center_ycor - radius)
    right = int(center_ycor + radius)
    for column in range(left, right):
        world[column] = [color if bottom < ind < top else x for ind, x in enumerate(world[column])]
    return world


def distance_to(x_one, y_one, x_two, y_two):
    x_dist = abs(x_one - x_two)
    y_dist = abs(y_one - y_two)
    return x_dist + y_dist


def calc_new_position(direction, xcor, ycor):
    if direction == "north":
        x = xcor
        y = ycor - 1
    elif direction == "east":
        x = xcor + 1
        y = ycor
    elif direction == "south":
        x = xcor
        y = ycor + 1
    elif direction == "west":
        x = xcor - 1
        y = ycor
    return x, y


class World:
    def __init__(self, world_width, world_height, number_of_leftover_food, size_of_leftover_food):
        self.width = world_width
        self.height = world_height
        self.center_xcor = int(self.width / 2)
        self.center_ycor = int(self.height / 2)
        self.empty_field = "#171717"
        self.home_field = "#444444"
        self.food_field = "#EDEDED"
        self.zombies = {}
        self.guy = Guy((0, 0))

        empty_world = [[self.empty_field for i in range(self.width)] for j in range(self.height)]

        # Create zombiehome
        world_with_zombiehome = modify_part_of_world(world=empty_world,
                                                     color=self.home_field,
                                                     center_xcor=self.center_xcor,
                                                     center_ycor=self.center_ycor,
                                                     size=10)

        # Create Food
        world_with_food = world_with_zombiehome
        food_radius = int(size_of_leftover_food / 2)
        distance_to_center = food_radius + 10
        distance_to_wall = food_radius + 2
        coordinates = [(x, y) for x in range(self.width) for y in range(self.height)]
        not_possible_coordinates = []
        for (x, y) in coordinates:
            if x < distance_to_wall or x > (self.width - distance_to_wall) or y < distance_to_wall or y > (
                    self.height - distance_to_wall):
                not_possible_coordinates.append((x, y))
            elif x in list(
                    range(self.center_xcor - distance_to_center, self.center_xcor + distance_to_center)) and y in list(
                range(self.center_ycor - distance_to_center, self.center_ycor + distance_to_center)):
                not_possible_coordinates.append((x, y))
        possible_coordinates = [(x, y) for (x, y) in coordinates if (x, y) not in not_possible_coordinates]
        for i in range(number_of_leftover_food):
            xcor, ycor = r.choice(possible_coordinates)
            try:
                world_with_food = modify_part_of_world(world=world_with_food,
                                                       color=self.food_field,
                                                       center_xcor=xcor,
                                                       center_ycor=ycor,
                                                       size=size_of_leftover_food)
                # print(f"Build food at: {xcor}, {ycor}")
            except IndexError:
                print(f"Czombie build food at: {xcor}, {ycor}")

        # World with an zombiehome and foodplaces is generated
        self.world_without_zombies = world_with_food
        self.world_with_zombies = [row.copy() for row in world_with_food]  # copy to get a new reference

    def create_zombie(self, name):
        self.zombies[name] = Zombie((self.center_xcor, self.center_ycor))
        answer = {"position": (self.zombies[name].xcor, self.zombies[name].ycor)}
        return answer

    def get_view(self):
        world_with_zombies = [row.copy() for row in self.world_without_zombies]
        for zombie in self.zombies.values():
            world_with_zombies[zombie.ycor][zombie.xcor] = zombie.color
        world_with_zombies[self.guy.ycor][self.guy.xcor] = self.guy.color
        return world_with_zombies

    def move_zombie(self, name, direction, state):
        zombie = self.zombies[name]
        x, y = calc_new_position(direction, zombie.xcor, zombie.ycor)

        answer = {
            "position": (zombie.xcor, zombie.ycor),
            "moved": False,
            "guy": False
        }

        if 0 > x or x > self.width - 1 or 0 > y or y > self.height - 1:  # Gegen die Wand
            answer["moved"] = False
        elif self.world_without_zombies[y][x] == self.food_field:
            answer["moved"] = False
        else:
            answer["moved"] = True
            answer["position"] = zombie.xcor, zombie.ycor = (x, y)

        if distance_to(zombie.xcor, zombie.ycor, self.guy.xcor, self.guy.ycor) < 20:
            answer["guy"] = (self.guy.xcor, self.guy.ycor)

        zombie.hunt_mode() if state == "HUNTING" else zombie.search_mode()

        return answer

    def get_reachable_friends(self, name):
        zombie = self.zombies[name]
        reachable_friends = [friend for friend in self.zombies
                             if 7 < distance_to(self.zombies[friend].xcor, self.zombies[friend].ycor, zombie.xcor, zombie.ycor) < 30]
        return reachable_friends

    def move_guy(self, direction):
        x, y = calc_new_position(direction, self.guy.xcor, self.guy.ycor)
        if 0 > x or x > self.width - 1 or 0 > y or y > self.height - 1:  # Gegen die Wand
            pass
        elif self.world_without_zombies[y][x] == self.food_field:
            pass
        else:
            self.guy.xcor, self.guy.ycor = x, y

    def reset(self):
        for zombie in self.zombies.values():
            zombie.reset((self.center_xcor, self.center_ycor))
        self.guy = Guy((0, 0))
