import json
import time
from world import World
from flask import Flask, render_template, request, Response
from zombie_agent import ZombieAgent
from pynput.keyboard import Listener


user_ids = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
XMPP_SERVER = "192.168.178.22"  # "im.koderoot.net"#
agents = {}

world = World(world_width=70, world_height=40, number_of_leftover_food=20, size_of_leftover_food=5)


def produce_agent(user_id):
    agents[user_id] = ZombieAgent(f"agent-{user_id}@{XMPP_SERVER}", f"agent-{user_id}1234", verify_security=False)
    agents[user_id].start()


async def stop_agents():
    for agent in agents:
        await agent.stop()


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

    app = Flask(__name__)

    start_time = time.time()

    @app.route("/create_zombie")
    def create_zombie():
        return world.create_zombie(request.args.get("name")), 200

    @app.route("/get_friends")
    def return_agent_addresses():
        name = request.args.get("name")
        friends = world.get_reachable_friends(name)
        addresses = [f"{friend}@{XMPP_SERVER}" for friend in friends]
        return json.dumps(addresses), 200

    @app.route("/move")
    def zombie_moves():
        name = request.args.get("name")
        direction = request.args.get("direction")
        state = request.args.get("state")
        try:
            return world.move_zombie(name, direction, state), 200
        except IndexError:
            return Response(status=400)

    @app.route('/world')
    def return_world():
        data = {"world": world.get_view()}
        return json.dumps(data)

    @app.route('/')
    def show_view():
        return render_template("view.html")

    @app.route("/reset")
    def reset():
        score = time.time() - start_time
        print(score)
        world.reset()
        return "200"

    with Listener(on_release=on_release) as listener:  # Setup the listener
        app.run()
        listener.join()  # Join the thread to the main thread


