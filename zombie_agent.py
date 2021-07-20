import requests
import random
import json
import asyncio
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, FSMBehaviour, State
from spade.message import Message

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


class ZombieBehaviour(FSMBehaviour):
    async def on_start(self):
        self.agent.actions = choose_random_directions()
        res = requests.get(f"{SERVER}/create_zombie?name={self.agent.name}")
        self.agent.position = json.loads(res.text)["position"]  # (x, y)
        self.agent.guy = False  # if guy is not False, it is (x, y) of the guy


class Searching(ZombieState):
    async def run(self):
        await asyncio.sleep(SLEEP_TIME)
        move_to = random.choice(self.agent.actions)
        await self.send_move_request(move_to)
        if self.agent.guy:
            self.set_next_state(STATE_HUNTING)
        else:
            self.set_next_state(STATE_SEARCHING)

    async def inform_friends(self, guy_pos):
        try:
            res = requests.get(f"{SERVER}/get_friends?name={self.agent.name}")
            if int(res.status_code) == 200:
                res = json.loads(res.text)
                for friend in res:
                    #  print(f"{self.agent.name} send to {friend}")
                    msg = Message(to=friend)     # Instantiate the message
                    msg.body = json.dumps(guy_pos)  # Set the message content
                    await self.send(msg)
        except Exception as e:
            print(f"{self.agent.name} cant communicate...")
            print(e)


class Hunting(ZombieState):
    async def run(self):
        await asyncio.sleep(SLEEP_TIME)
        move_to = decide_next_move(self.agent.guy, self.agent.position)
        await self.send_move_request(move_to)
        if not self.agent.guy:
            self.set_next_state(STATE_SEARCHING)
        else:
            self.set_next_state(STATE_HUNTING)


class ReceiveMsg(CyclicBehaviour):
    async def run(self):
        msg = await self.receive(timeout=0.1)
        if msg and not self.agent.guy:
            self.agent.guy = nearest_goal(self.agent.position, self.agent.guy, json.loads(msg.body))


class ZombieAgent(Agent):
    async def setup(self):
        fsm = ZombieBehaviour()
        fsm.add_state(name=STATE_SEARCHING, state=Searching(), initial=True)
        fsm.add_state(name=STATE_HUNTING, state=Hunting())
        fsm.add_transition(source=STATE_SEARCHING, dest=STATE_SEARCHING)
        fsm.add_transition(source=STATE_SEARCHING, dest=STATE_HUNTING)
        fsm.add_transition(source=STATE_HUNTING, dest=STATE_HUNTING)
        fsm.add_transition(source=STATE_HUNTING, dest=STATE_SEARCHING)
        self.add_behaviour(fsm)

        receive = ReceiveMsg()
        self.add_behaviour(receive)

