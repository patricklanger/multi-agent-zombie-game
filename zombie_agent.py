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
    """
    :return: Returns two random directions as list
    """
    n, e, s, w = ("north", "east", "south", "west")
    return random.choice([[n, e], [e, s], [s, w], [w, n]])


def decide_next_move(goal, pos):
    """
    For a given pos and a goal, the function calculates the best next move.
    :param goal: (x, y)
    :param pos: (x, y)
    :return: north, east, south or west as string
    """
    x_dir = pos[0] - goal[0]  # 0 -> x, 1 -> y
    y_dir = pos[1] - goal[1]
    if abs(x_dir) > abs(y_dir):
        return "west" if x_dir > 0 else "east"
    else:
        return "north" if y_dir > 0 else "south"


def distance_to(start, goal):
    """
    Calculates the distance from start to goal.
    :param start:  (x, y)
    :param goal:  (x, y)
    :return: distance as int
    """
    x_dist = abs(start[0] - goal[0])  # 0 -> x, 1 -> y
    y_dist = abs(start[1] - goal[1])
    return x_dist + y_dist


def reset():
    """
    Send a reset-request to the server to reset the Game.
    :return:
    """
    requests.get(f"{SERVER}/reset")


class ZombieState(State):
    """
    Inherits from State() class to add the send_move_request-function. It will be needed from Searchin()-State-class
    and Hunting()-State-class
    """

    async def run(self):
        """
        Must be defined in the inheriting states.
        :return:
        """
        pass

    async def send_move_request(self, move_to):
        """
        Sends a move-request to the server and updates the following variables under the following conditions:
        if moving to move_to was possible:
            self.agent.position, self.agent.guy
        if moving to move_to was not possible:
            self.agent.actions, self.agent.guy
        :param move_to: direction as "north", "east", "south" or "west"
        :return:
        """
        try:
            res = requests.get(f"{SERVER}/move?name={self.agent.name}&direction={move_to}&state={self.next_state}")
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
            else:
                self.agent.guy = False
                self.agent.actions = choose_random_directions()
        except Exception as e:
            print(e)


class ZombieBehaviour(FSMBehaviour):
    """
    Finite State Machine Behaviour to create an automate-like behaviour.
    """
    async def on_start(self):
        """
        Before the initial-state starts the on_start method sends a create_zombie-request to the server, so it will be
        displayed on the view/world. Also initializes the actions, position and guy variables.
        :return:
        """
        self.agent.actions = choose_random_directions()
        res = requests.get(f"{SERVER}/create_zombie?name={self.agent.name}")
        self.agent.position = json.loads(res.text)["position"]  # (x, y)
        self.agent.guy = False  # if guy is not False, it is (x, y) of the guy

    class Searching(ZombieState):
        """
        Searching state. The initial state.
        """
        async def run(self):
            """
            Waits for a predefined time, choose a random direction, make a move request.
            If guy wasn't seen at the new position:
                Stay in Searching state
            If guy was seen at the new position:
                Change next_state to Hunting state and call inform_friend about the guy position
            :return:
            """
            await asyncio.sleep(SLEEP_TIME)
            move_to = random.choice(self.agent.actions)
            await self.send_move_request(move_to)
            if self.agent.guy:
                self.set_next_state(STATE_HUNTING)
                try:
                    await self.inform_friends(self.agent.guy)
                except Exception:
                    pass
            else:
                self.set_next_state(STATE_SEARCHING)

        async def inform_friends(self, guy_pos):
            """
            Makes a get_friends request to the server to get addresses of other zombies nearby and sends the guy_pos to
            all addresses.
            :param guy_pos: (x, y) as int-tuple
            :return:
            """
            try:
                res = requests.get(f"{SERVER}/get_friends?name={self.agent.name}")
                res = json.loads(res.text)
                for friend in res:
                    msg = Message(to=friend)     # Instantiate the message
                    msg.body = json.dumps(guy_pos)  # Set the message content
                    await self.send(msg)
            except Exception as e:
                print(f"{self.agent.name} cant communicate...")
                print(e)

    class Hunting(ZombieState):
        """
        Hunting state.
        """
        async def run(self):
            """
            Waits for a predefined time, choose a the best direction to reach position of the guy, make a move request.
            If guy wasn't seen at the new position:
                Change next_state to Searching state
            If guy was seen at the new position:
                Stay in Hunting state
            :return:
            """
            await asyncio.sleep(SLEEP_TIME)
            move_to = decide_next_move(self.agent.guy, self.agent.position)
            await self.send_move_request(move_to)
            if not self.agent.guy:
                self.set_next_state(STATE_SEARCHING)
            else:
                self.set_next_state(STATE_HUNTING)


class ReceiveMsg(CyclicBehaviour):
    """
    Cyclic Behaviour to receive messages. Run method repeats after its done.
    """
    async def run(self):
        """
        Wait up to 10 sec. for an incoming message.
        If a message arrives an the agent have no position of guy:
            Update guy position.
        :return:
        """
        msg = await self.receive(timeout=10)
        if msg and not self.agent.guy:
            self.agent.guy = json.loads(msg.body)


class ZombieAgent(Agent):
    """
    The Zombie agent inherits from Agent class.
    """
    async def setup(self):
        """
        Classes who inherits from Agent class must implement a setup method.
        Creates the ZombieBehavior, adds the Searching and the Hunting state to the Finite State Machine behaviour,
        adds the needed transitions to the behavior and adds the behaviour to the agent.
        Creates the cyclic ReceiveMsg behaviour and adds it to the agents behaviours.
        :return:
        """
        fsm = ZombieBehaviour()
        fsm.add_state(name=STATE_SEARCHING, state=fsm.Searching(), initial=True)
        fsm.add_state(name=STATE_HUNTING, state=fsm.Hunting())
        fsm.add_transition(source=STATE_SEARCHING, dest=STATE_SEARCHING)
        fsm.add_transition(source=STATE_SEARCHING, dest=STATE_HUNTING)
        fsm.add_transition(source=STATE_HUNTING, dest=STATE_HUNTING)
        fsm.add_transition(source=STATE_HUNTING, dest=STATE_SEARCHING)
        self.add_behaviour(fsm)

        receive = ReceiveMsg()
        self.add_behaviour(receive)

