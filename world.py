import random as r
from zombie import Zombie
from guy import Guy


def modify_part_of_world(world, color, center_xcor, center_ycor, size):
    """
    Fills a square in a 2D list with the given color-string.
    :param world: list of lists of strings
    :param color: color as string
    :param center_xcor: x coordinates of the center of the square
    :param center_ycor: y coordinates of the center of the square
    :param size: side length of the square
    :return: the colored 2d list (world)
    """
    radius = int(size / 2)
    top = int(center_xcor + radius)
    bottom = int(center_xcor - radius)
    left = int(center_ycor - radius)
    right = int(center_ycor + radius)
    for column in range(left, right):
        world[column] = [color if bottom < ind < top else x for ind, x in enumerate(world[column])]
    return world


def distance_to(x_one, y_one, x_two, y_two):
    """
    Calculates the distance from (x_one, y_one) to (x_two, y_two)
    :param x_one:
    :param y_one:
    :param x_two:
    :param y_two:
    :return: the distance
    """
    x_dist = abs(x_one - x_two)
    y_dist = abs(y_one - y_two)
    return x_dist + y_dist


def calc_new_position(direction, xcor, ycor):
    """
    Calculates the new position after a step in the given direction.
    :param direction:
    :param xcor: starting point x coordinates
    :param ycor: starting point y coordinates
    :return: new coordinates (x, y)
    """
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
    """
    The world where the zombies and the player will move.
    """
    def __init__(self, world_width, world_height, number_of_leftover_food, size_of_leftover_food):
        """
        Initializes the world.
        :param world_width:
        :param world_height:
        :param number_of_leftover_food: number of white blocks / walls where no one can get through
        :param size_of_leftover_food: size of white blocks / walls where no one can get through
        """
        self.width = world_width
        self.height = world_height

        self.center_xcor = int(self.width / 2)
        self.center_ycor = int(self.height / 2)

        self.empty_field = "#171717"
        self.home_field = "#444444"
        self.food_field = "#EDEDED"

        self.zombies = {}  # Reference to the zombies
        self.guy = Guy((0, 0))  # Reference to the guy-figure of the player

        #  Create an empty world.
        empty_world = [[self.empty_field for i in range(self.width)] for j in range(self.height)]

        # Create zombiehome
        world_with_zombiehome = modify_part_of_world(world=empty_world,
                                                     color=self.home_field,
                                                     center_xcor=self.center_xcor,
                                                     center_ycor=self.center_ycor,
                                                     size=10)

        # Create Food (It isn't food anymore.... Here we create the white blocks or walls where no one can get through)
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

        # Hold reference to a world without zombies.
        self.world_without_zombies = world_with_food

    def create_zombie(self, name):
        """
        Creates a zombie.
        :param name: name will be the key to find the zombie.
        :return: dictionary -> {"position": (x, y)}
        """
        self.zombies[name] = Zombie((self.center_xcor, self.center_ycor))
        answer = {"position": (self.zombies[name].xcor, self.zombies[name].ycor)}
        return answer

    def get_view(self):
        """
        Colors all fields in a copy of world_without_zombies where a zombie or the guy is.
        :return: 2D list world_with_zombies
        """
        world_with_zombies = [row.copy() for row in self.world_without_zombies]
        for zombie in self.zombies.values():
            world_with_zombies[zombie.ycor][zombie.xcor] = zombie.color
        world_with_zombies[self.guy.ycor][self.guy.xcor] = self.guy.color
        return world_with_zombies

    def move_zombie(self, name, direction, state):
        """
        Decides if a move is possible and return the new position and maybe the guy position if given zombie is nearby.
        :param name: name of the zombie that want to move.
        :param direction:
        :param state: state of the zombie (SEARCHING or HUNTING)
        :return: dictionary like this ->
            {
            "position": (zombie.xcor, zombie.ycor),
            "moved": True or False,
            "guy": False or (guy.xcor, guy.ycor)
        }
        """
        distance_to_see_the_guy = 20

        zombie = self.zombies[name]
        x, y = calc_new_position(direction, zombie.xcor, zombie.ycor)

        answer = {
            "position": (zombie.xcor, zombie.ycor),
            "moved": False,
            "guy": False
        }

        if 0 > x or x > self.width - 1 or 0 > y or y > self.height - 1:  # Outside of the world
            answer["moved"] = False
        elif self.world_without_zombies[y][x] == self.food_field:  # Gegen die Wand
            answer["moved"] = False
        else:
            answer["moved"] = True
            answer["position"] = zombie.xcor, zombie.ycor = (x, y)

        if distance_to(zombie.xcor, zombie.ycor, self.guy.xcor, self.guy.ycor) < distance_to_see_the_guy:
            answer["guy"] = (self.guy.xcor, self.guy.ycor)

        zombie.hunt_mode() if state == "HUNTING" else zombie.search_mode()

        return answer

    def get_reachable_friends(self, name):
        """
        Returns zombie names nearby the requesting zombie.
        :param name:
        :return: list of zombie names
        """
        distance_to_be_reachable = 30
        zombie = self.zombies[name]
        reachable_friends = [friend for friend in self.zombies
                             if 7 < distance_to(self.zombies[friend].xcor,
                                                self.zombies[friend].ycor,
                                                zombie.xcor, zombie.ycor) < distance_to_be_reachable]
        return reachable_friends

    def move_guy(self, direction):
        """
        Decides if a move of the player is possible.
        :param direction:
        :return: the new position. (x, y)
        """
        x, y = calc_new_position(direction, self.guy.xcor, self.guy.ycor)
        if 0 > x or x > self.width - 1 or 0 > y or y > self.height - 1:  # Outside of the world
            pass
        elif self.world_without_zombies[y][x] == self.food_field:  # Gegen die Wand
            pass
        else:
            self.guy.xcor, self.guy.ycor = x, y

    def reset(self):
        """
        Reset the world. Moves all zombies to center of world. Moves guy to (0, 0).
        :return:
        """
        for zombie in self.zombies.values():
            zombie.reset((self.center_xcor, self.center_ycor))
        self.guy = Guy((0, 0))
