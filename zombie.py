class Zombie:
    def __init__(self, position):
        self.xcor, self.ycor = position
        self.color = "#444444"

    def hunt_mode(self):
        self.color = "#DA0037"

    def search_mode(self):
        self.color = "#444444"

    def reset(self, position):
        self.xcor, self.ycor = position
        self.color = "#444444"
