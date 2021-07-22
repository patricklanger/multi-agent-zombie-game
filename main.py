"""
MULTI AGENT ZOMBIE GAME

To run the game you will need a SPADE installation and a running XMPP server.

SPADE documentation: https://spade-mas.readthedocs.io
SPADE on GitHub: https://github.com/javipalanca/spade

SPADE recommend this XMPP server: https://prosody.im
List of other XMPP servers: https://xmpp.org/software/servers.html
"""

import json
import time
from world import World
from zombie_agent import ZombieAgent
from flask import Flask, render_template, request, Response  # Server
from pynput.keyboard import Listener  # Key listener


user_ids = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]

XMPP_SERVER = "192.168.178.22"  # IP of local xmpp-server
# If you don't want to install a xmpp-server local you can use koderoot, but just for 2 agents
#  XMPP_SERVER = "im.koderoot.net"

agents = {}

# number_of_leftover_food -> number of white blocks; size_of_leftover_food -> size of white blocks
world = World(world_width=70, world_height=40, number_of_leftover_food=20, size_of_leftover_food=5)


def produce_agent(user_id):
    #  Create agents like this: Agent("{agent_name}@{server_ip}", "password")
    agents[user_id] = ZombieAgent(f"agent-{user_id}@{XMPP_SERVER}", f"agent-{user_id}1234", verify_security=False)
    agents[user_id].start()  # Start the agent


async def stop_agents():
    for agent in agents:
        await agent.stop()


# function for the key listener
def on_release(key):
    if hasattr(key, 'char'):
        if key.char == 'w':
            print(key.char)
            world.move_guy("north")
        if key.char == 'a':
            print(key.char)
            world.move_guy("west")
        if key.char == 's':
            print(key.char)
            world.move_guy("south")
        if key.char == 'd':
            print(key.char)
            world.move_guy("east")


if __name__ == "__main__":
    for user in user_ids:
        produce_agent(user)

    app = Flask(__name__)  # Create Server

    start_time = time.time()  # if you want to stop the play-time

    @app.route("/create_zombie")
    def create_zombie():
        """
        Creates a Zombie instance in the world for given name.
        :"/create_zombie?name=name": name of the agent
        :return: dictionary like this ->
                {
                    "position": int-tuple,
                    "moved": boolean or int-tuple,
                    "guy": boolean or int-tuple
                }
        """
        return world.create_zombie(request.args.get("name")), 200

    @app.route("/get_friends")
    def return_agent_addresses():
        """
        Creates a list of agent-addresses of agents who are nearby the position of a given agent-name.
        :"/get_friends?name=name": name of the agent
        :return: list of strings
        """
        name = request.args.get("name")
        friends = world.get_reachable_friends(name)
        addresses = [f"{friend}@{XMPP_SERVER}" for friend in friends]
        return json.dumps(addresses), 200

    @app.route("/move")
    def zombie_moves():
        """
        Checks the move-request and update the zombie instance in the world.
        :"/move?name=name&direction=direction&state=state": name of the agent, direction, state of the agent (HUNTING or SEARCHING)
        :return: dictionary like this ->
                {
                    "position": int-tuple,
                    "moved": boolean or int-tuple,
                    "guy": boolean or int-tuple
                }
        """
        name = request.args.get("name")
        direction = request.args.get("direction")
        state = request.args.get("state")
        try:
            return world.move_zombie(name, direction, state), 200
        except IndexError:
            return Response(status=400)

    @app.route('/world')
    def return_world():
        """
        Route for the view.html to poll the matrix of the world.
        :return: dictionary like this ->
                {
                    "world": 2D-list with HEX-color-strings
                }
        """
        data = {"world": world.get_view()}
        return json.dumps(data)

    @app.route('/')
    def show_view():
        """
        Route for the browser.
        :return: view.html
        """
        return render_template("view.html")

    @app.route("/reset")
    def reset():
        """
        Resets the world incl positions of the zombie instances and the player
        :return:
        """
        score = time.time() - start_time
        print(score)
        world.reset()
        return "200"

    with Listener(on_release=on_release) as listener:  # Setup the listener
        app.run()  # run the server
        listener.join()  # Join the thread to the main thread


