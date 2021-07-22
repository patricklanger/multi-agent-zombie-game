import requests
import random
import json
import asyncio
# TODO import

STATE_SEARCHING = "SEARCHING"
STATE_HUNTING = "HUNTING"

SERVER = "http://127.0.0.1:5000"

SLEEP_TIME = 0.2


def choose_random_directions():
    n, e, s, w = ("north", "east", "south", "west")
    return random.choice([[n, e], [e, s], [s, w], [w, n]])


def decide_next_move(goal, pos):
    x_dir = pos[0] - goal[0]  # 0 -> x, 1 -> y
    y_dir = pos[1] - goal[1]
    if abs(x_dir) > abs(y_dir):
        return "west" if x_dir > 0 else "east"
    else:
        return "north" if y_dir > 0 else "south"


def distance_to(start, goal):
    x_dist = abs(start[0] - goal[0])  # 0 -> x, 1 -> y
    y_dist = abs(start[1] - goal[1])
    return x_dist + y_dist


def nearest_goal(position, goal_one, goal_two):
    if not goal_one:
        return goal_two
    elif not goal_two:
        return goal_one
    if distance_to(position, goal_one) < distance_to(position, goal_two):
        return goal_one
    return goal_two


def reset():
    requests.get(f"{SERVER}/reset")


class ZombieState(State):
    async def run(self):
        pass

    async def send_move_request(self, move_to):
        try:
            res = requests.get(f"{SERVER}/move?name={self.agent.name}&direction={move_to}&state={self.next_state}")
            if int(res.status_code) == 200:
                res = json.loads(res.text)
                if res["moved"]:
                    self.agent.position = (res["position"][0], res["position"][1])
                    if self.agent.guy:
                        if self.agent.position[0] == self.agent.guy[0] and self.agent.position[1] == self.agent.guy[1]:
                            self.agent.guy = False
                    if res["guy"]:
                        self.agent.guy = (int(res["guy"][0]), int(res["guy"][1]))
                        if self.agent.position[0] == self.agent.guy[0] and self.agent.position[1] == self.agent.guy[1]:
                            reset()
                        try:
                            await self.inform_friends(self.agent.guy)
                        except Exception:
                            pass
                else:
                    self.agent.guy = False
                    self.agent.actions = choose_random_directions()
        except Exception as e:
            print(e)


# TODO class ZombieBehaviour(FSMBehaviour)


# TODO class Searching(ZombieState)

    # TODO method inform_friends(guy_pos)


# TODO class Hunting(ZombieState)


# TODO class ReceiveMsg(CyclicBehaviour)


# TODO class ZombieAgent(Agent):

