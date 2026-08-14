import random
import tkinter as tk


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

    def get_percept(self):
        current_position = tuple(self.agent_pos)
        x, y = self.agent_pos

        # Determine which of the 4 cardinal directions are currently blocked by walls/edges
        blocked_directions = set()
        candidates = {
            "Up": (x, y + 1),
            "Down": (x, y - 1),
            "Left": (x - 1, y),
            "Right": (x + 1, y)
        }

        for d, (nx, ny) in candidates.items():
            if nx < 0 or nx >= self.width or ny < 0 or ny >= self.height or (nx, ny) in self.walls:
                blocked_directions.add(d)

        wall_ahead = self.direction in blocked_directions

        return {
            "wall_ahead": wall_ahead,
            "food_here": current_position in self.food_positions,
            "trap_here": current_position in self.toxic_traps,
            "collision": self.collision,
            "current_direction": self.direction,
            "blocked_directions": blocked_directions,

            "grid_size": (self.width, self.height),
            "walls": list(self.walls),
            "all_food": list(self.food_positions)
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

            # Check boundary collision
            if (
                new_pos[0] < 0
                or new_pos[0] >= self.width
                or new_pos[1] < 0
                or new_pos[1] >= self.height
            ):
                self.score -= 5
                return

            # Check wall collision
            if tuple(new_pos) in self.walls:
                self.score -= 5
            else:
                self.agent_pos = new_pos

            current = tuple(self.agent_pos)

            if current in self.food_positions:
                self.food_positions.remove(current)
                self.score += 20

            if current in self.toxic_traps:
                self.toxic_traps.remove(current)
                self.score -= 15

    def is_done(self):
        return (
            len(self.food_positions) == 0
            or self.steps >= 60
            or self.collision
        )


class SimpleReflexAgent:
    """Reflex Agent that turns to a random open direction when encountering a wall or edge."""

    def sense_and_act(self, percept):
        if percept["food_here"]:
            return "Suck"

        if percept["wall_ahead"]:
            all_directions = {"Up", "Down", "Left", "Right"}
            blocked = percept.get("blocked_directions", set())
            open_directions = list(all_directions - blocked)

            # Pick randomly among available open directions
            if open_directions:
                return random.choice(open_directions)
            else:
                # Fallback if somehow completely surrounded
                return random.choice(list(all_directions))

        return "Forward"


class GridGameGUI:
    """Tkinter visualization for Simple Reflex Agent."""

    def __init__(self, root, width=12, height=12,
                 num_food=15, num_opponents=0, walls=None):

        self.root = root
        self.root.title("IT3012 - Simple Reflex Agent Grid Hunt")

        self.env = VisualGridHuntGame(
            width=width,
            height=height,
            num_food=num_food,
            num_opponents=num_opponents,
            custom_walls=walls
        )

        self.agent = SimpleReflexAgent()
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
            text="Score: 0 | Steps: 0",
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

        # Draw grid cells & walls
        for x in range(self.env.width):
            for y in range(self.env.height):
                x1 = x * self.cell_size
                y1 = (self.env.height - y - 1) * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                color = "#64748b" if (x, y) in self.env.walls else "#f1f5f9"

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline="#cbd5e1"
                )

        # Draw food
        for fx, fy in self.env.food_positions:
            x1 = fx * self.cell_size + 15
            y1 = (self.env.height - fy - 1) * self.cell_size + 15
            self.canvas.create_oval(
                x1, y1, x1 + 20, y1 + 20,
                fill="#f59e0b", outline="#d97706"
            )

        # Draw toxic traps
        for tx, ty in self.env.toxic_traps:
            x1 = tx * self.cell_size
            y1 = (self.env.height - ty - 1) * self.cell_size
            self.canvas.create_polygon(
                x1 + 25, y1 + 5,
                x1 + 5, y1 + 45,
                x1 + 45, y1 + 45,
                fill="purple", outline="black"
            )

        # Draw opponents
        for ox, oy in self.env.opponents:
            x1 = ox * self.cell_size + 10
            y1 = (self.env.height - oy - 1) * self.cell_size + 10
            self.canvas.create_rectangle(
                x1, y1, x1 + 30, y1 + 30,
                fill="red"
            )

        # Draw agent
        ax, ay = self.env.agent_pos
        x1 = ax * self.cell_size + 10
        y1 = (self.env.height - ay - 1) * self.cell_size + 10
        self.canvas.create_oval(
            x1, y1, x1 + 30, y1 + 30,
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
                        f"Action: {action} | "
                        f"Percept: {percept} | "
                        f"Score: {self.env.score} | "
                        f"Steps: {self.env.steps}"
                    )
                )

                self.root.after(500, step)
            else:
                self.label.config(
                    text=(
                        f"Simulation Finished | "
                        f"Final Score: {self.env.score}"
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
        num_opponents=0
    )
    root.mainloop()



class ModelBasedAgent:

    def __init__(self):

        self.visited_cells = set()

        self.last_action = None

        self.position = (0, 0)

        self.direction = "Up"



    def sense_and_act(self, percept):

        # Update internal state
        self.visited_cells.add(self.position)


        # Rule 1: Collect food
        if percept["food_here"]:

            action = "Suck"



        # Rule 2: Avoid loops by changing direction
        elif percept["wall_ahead"]:

            if self.position in self.visited_cells:

                action = "Right"

            else:

                action = "Left"



        # Rule 3: Avoid previously visited areas
        elif self.position in self.visited_cells:

            action = "Right"



        # Rule 4: Move forward normally
        else:

            action = "Forward"



        # Store last action
        self.last_action = action


        return action


