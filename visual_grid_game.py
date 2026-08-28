import random
import tkinter as tk

from agent import SearchAgent


class VisualGridHuntGame:
    """Pacman-style grid environment with partial observability."""

    def __init__(self, width=10, height=10, num_food=10,
                 num_opponents=2, custom_walls=None):

        self.width = width
        self.height = height

        self.agent_pos = [0, 0]
        self.direction = "Up"

        if custom_walls is not None:
            self.walls = set(custom_walls)
        else:
            self.walls = {
                (2, 2), (2, 3), (5, 5), (6, 5), (3, 7)
            }

        self.food_positions = set()

        while len(self.food_positions) < num_food:
            fx = random.randint(0, self.width - 1)
            fy = random.randint(0, self.height - 1)
            food = (fx, fy)

            if food != (0, 0) and food not in self.walls:
                self.food_positions.add(food)

        self.toxic_traps = set()

        while len(self.toxic_traps) < 5:
            tx = random.randint(0, self.width - 1)
            ty = random.randint(0, self.height - 1)
            trap = (tx, ty)

            if (
                trap != (0, 0)
                and trap not in self.walls
                and trap not in self.food_positions
            ):
                self.toxic_traps.add(trap)

        self.opponents = []

        while len(self.opponents) < num_opponents:
            ox = random.randint(0, self.width - 1)
            oy = random.randint(0, self.height - 1)
            opponent = [ox, oy]

            if (
                tuple(opponent) != (0, 0)
                and tuple(opponent) not in self.walls
                and tuple(opponent) not in self.food_positions
                and tuple(opponent) not in self.toxic_traps
            ):
                self.opponents.append(opponent)

        self.score = 0
        self.steps = 0
        self.collision = False
        self.trap_hit = False

    def get_percept(self):
        current_position = tuple(self.agent_pos)
        x, y = self.agent_pos

        blocked_directions = set()

        candidates = {
            "Up": (x, y + 1),
            "Down": (x, y - 1),
            "Left": (x - 1, y),
            "Right": (x + 1, y)
        }

        for direction, (nx, ny) in candidates.items():
            if (
                nx < 0
                or nx >= self.width
                or ny < 0
                or ny >= self.height
                or (nx, ny) in self.walls
            ):
                blocked_directions.add(direction)

        wall_ahead = self.direction in blocked_directions

        opponent_here = current_position in {
            tuple(opponent) for opponent in self.opponents
        }

        return {
            "agent_pos": list(self.agent_pos),
            "wall_ahead": wall_ahead,
            "food_here": current_position in self.food_positions,
            "trap_here": current_position in self.toxic_traps,
            "opponent_here": opponent_here,
            "collision": self.collision,
            "current_direction": self.direction,
            "blocked_directions": blocked_directions,
            "grid_size": (self.width, self.height),
            "walls": list(self.walls),
            "all_food": list(self.food_positions),
            "toxic_traps": list(self.toxic_traps),
            "opponents": list(self.opponents)
        }

    def execute_action(self, action):
        self.steps += 1

        if action == "Suck":
            current = tuple(self.agent_pos)

            if current in self.food_positions:
                self.food_positions.remove(current)
                self.score += 20

            return

        if action in ["Left", "Right", "Up", "Down"]:
            self.direction = action
            return

        if action == "Forward":
            new_pos = list(self.agent_pos)

            if self.direction == "Up":
                new_pos[1] += 1
            elif self.direction == "Down":
                new_pos[1] -= 1
            elif self.direction == "Left":
                new_pos[0] -= 1
            elif self.direction == "Right":
                new_pos[0] += 1

            if (
                new_pos[0] < 0
                or new_pos[0] >= self.width
                or new_pos[1] < 0
                or new_pos[1] >= self.height
            ):
                self.score -= 5
                return

            if tuple(new_pos) in self.walls:
                self.score -= 5
                return

            self.agent_pos = new_pos

            current = tuple(self.agent_pos)

            if current in self.food_positions:
                self.food_positions.remove(current)
                self.score += 20

            if current in self.toxic_traps:
                self.trap_hit = True
                self.collision = True
                self.score -= 15

            for opponent in self.opponents:
                if current == tuple(opponent):
                    self.collision = True
                    self.score -= 20
                    break

    def is_done(self):
        return (
            len(self.food_positions) == 0
            or self.steps >= 300
            or self.collision
        )


class SimpleReflexAgent:
    """Simple Reflex Agent using condition-action rules."""

    def sense_and_act(self, percept):

        if percept["food_here"]:
            return "Suck"

        if percept["trap_here"]:
            blocked = percept.get("blocked_directions", set())

            safe_directions = [
                direction
                for direction in ["Up", "Down", "Left", "Right"]
                if direction not in blocked
            ]

            if safe_directions:
                return random.choice(safe_directions)

        if percept["opponent_here"]:
            blocked = percept.get("blocked_directions", set())

            safe_directions = [
                direction
                for direction in ["Up", "Down", "Left", "Right"]
                if direction not in blocked
            ]

            if safe_directions:
                return random.choice(safe_directions)

        if percept["wall_ahead"]:
            all_directions = ["Up", "Down", "Left", "Right"]

            blocked = percept.get("blocked_directions", set())

            open_directions = [
                direction
                for direction in all_directions
                if direction not in blocked
            ]

            if open_directions:
                return random.choice(open_directions)

            return random.choice(all_directions)

        return "Forward"


class ModelBasedAgent:
    """Model-Based Agent with internal memory of visited cells."""

    def __init__(self):

        self.visited_cells = set()
        self.last_action = None
        self.position = (0, 0)
        self.direction = "Up"

    def sense_and_act(self, percept):

        self.position = tuple(percept["agent_pos"])
        self.direction = percept["current_direction"]

        self.visited_cells.add(self.position)

        if percept["food_here"]:
            action = "Suck"
            self.last_action = action
            return action

        blocked = percept.get("blocked_directions", set())

        safe_directions = [
            direction
            for direction in ["Up", "Down", "Left", "Right"]
            if direction not in blocked
        ]

        if percept["trap_here"] or percept["opponent_here"]:

            if safe_directions:
                unvisited = [
                    direction
                    for direction in safe_directions
                    if self.get_next_position(direction)
                    not in self.visited_cells
                ]

                if unvisited:
                    action = random.choice(unvisited)
                else:
                    action = random.choice(safe_directions)

                self.last_action = action
                return action

        if percept["wall_ahead"]:

            unvisited = [
                direction
                for direction in safe_directions
                if self.get_next_position(direction)
                not in self.visited_cells
            ]

            if unvisited:
                action = random.choice(unvisited)
            elif safe_directions:
                action = random.choice(safe_directions)
            else:
                action = "Forward"

            self.last_action = action
            return action

        next_position = self.get_next_position(self.direction)

        if next_position in self.visited_cells:

            unvisited = [
                direction
                for direction in safe_directions
                if self.get_next_position(direction)
                not in self.visited_cells
            ]

            if unvisited:
                action = random.choice(unvisited)
            elif safe_directions:
                action = random.choice(safe_directions)
            else:
                action = "Forward"

            self.last_action = action
            return action

        action = "Forward"

        self.last_action = action

        return action

    def get_next_position(self, direction):

        x, y = self.position

        if direction == "Up":
            return x, y + 1

        if direction == "Down":
            return x, y - 1

        if direction == "Left":
            return x - 1, y

        if direction == "Right":
            return x + 1, y

        return self.position


class GridGameGUI:
    """Tkinter visualization for the grid agents."""

    def __init__(
        self,
        root,
        width=12,
        height=12,
        num_food=15,
        num_opponents=0,
        walls=None,
        agent_type="simple"
    ):

        self.root = root

        self.root.title(
            "IT3012 - Grid Hunt Agent Simulation"
        )

        self.env = VisualGridHuntGame(
            width=width,
            height=height,
            num_food=num_food,
            num_opponents=num_opponents,
            custom_walls=walls
        )

        if agent_type == "search":
            self.agent = SearchAgent()
            self.agent_name = "Search Agent"
        elif agent_type == "model":
            self.agent = ModelBasedAgent()
            self.agent_name = "Model-Based Agent"
        else:
            self.agent = SimpleReflexAgent()
            self.agent_name = "Simple Reflex Agent"

        self.cell_size = 50

        self.canvas = tk.Canvas(
            root,
            width=self.env.width * self.cell_size,
            height=self.env.height * self.cell_size,
            bg="white"
        )

        self.canvas.pack()

        self.label = tk.Label(
            root,
            text=f"{self.agent_name} | Score: 0 | Steps: 0",
            font=("Arial", 14)
        )

        self.label.pack(pady=10)

        self.button = tk.Button(
            root,
            text="Start Simulation",
            command=self.run_loop,
            font=("Arial", 12),
            bg="#000066",
            fg="white"
        )

        self.button.pack(pady=5)

        self.draw_grid()

    def draw_grid(self):

        self.canvas.delete("all")

        for x in range(self.env.width):

            for y in range(self.env.height):

                x1 = x * self.cell_size
                y1 = (
                    self.env.height - y - 1
                ) * self.cell_size

                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                if (x, y) in self.env.walls:
                    color = "#64748b"
                else:
                    color = "#f1f5f9"

                self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=color,
                    outline="#cbd5e1"
                )

        for fx, fy in self.env.food_positions:

            x1 = fx * self.cell_size + 15
            y1 = (
                self.env.height - fy - 1
            ) * self.cell_size + 15

            self.canvas.create_oval(
                x1,
                y1,
                x1 + 20,
                y1 + 20,
                fill="#f59e0b",
                outline="#d97706"
            )

        for tx, ty in self.env.toxic_traps:

            x1 = tx * self.cell_size
            y1 = (
                self.env.height - ty - 1
            ) * self.cell_size

            self.canvas.create_polygon(
                x1 + 25,
                y1 + 5,
                x1 + 5,
                y1 + 45,
                x1 + 45,
                y1 + 45,
                fill="purple",
                outline="black"
            )

        for ox, oy in self.env.opponents:

            x1 = ox * self.cell_size + 10
            y1 = (
                self.env.height - oy - 1
            ) * self.cell_size + 10

            self.canvas.create_rectangle(
                x1,
                y1,
                x1 + 30,
                y1 + 30,
                fill="red"
            )

        ax, ay = self.env.agent_pos

        x1 = ax * self.cell_size + 10
        y1 = (
            self.env.height - ay - 1
        ) * self.cell_size + 10

        self.canvas.create_oval(
            x1,
            y1,
            x1 + 30,
            y1 + 30,
            fill="blue"
        )

    def run_loop(self):

        self.button.config(state="disabled")

        def step():

            if not self.env.is_done():

                percept = self.env.get_percept()

                action = self.agent.sense_and_act(percept)

                self.env.execute_action(action)

                self.draw_grid()

                self.label.config(
                    text=(
                        f"{self.agent_name} | "
                        f"Action: {action} | "
                        f"Score: {self.env.score} | "
                        f"Steps: {self.env.steps}"
                    )
                )

                self.root.after(500, step)

            else:

                if self.env.trap_hit:
                    result = "Toxic Trap Hit"

                elif self.env.collision:
                    result = "Collision"

                elif len(self.env.food_positions) == 0:
                    result = "All Food Collected"

                elif self.env.steps >= 60:
                    result = "Maximum Steps Reached"

                else:
                    result = "Simulation Finished"

                self.label.config(
                    text=(
                        f"{self.agent_name} | "
                        f"{result} | "
                        f"Final Score: {self.env.score} | "
                        f"Steps: {self.env.steps}"
                    )
                )

                self.button.config(state="normal")

        step()


if __name__ == "__main__":

    root = tk.Tk()

    app = GridGameGUI(
        root,
        width=12,
        height=12,
        num_food=15,
        num_opponents=0,
        agent_type="search"
    )

    root.mainloop()
