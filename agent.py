from collections import deque
import heapq
import math
from operator import pos
import random
import tkinter as tk

class SearchAgent:
    """Search-based agent supporting BFS, DFS, and UCS."""

    def __init__(self):
        # Current position of the agent
        self.position = (0, 0)

        # Complete offline action plan
        self.plan = []

        # Change this to BFS, DFS, or UCS
        self.active_algo = "BFS"

    def manhattan_distance(self, pos, goal):
     x1, y1 = pos
     x2, y2 = goal

     return abs(x1 - x2) + abs(y1 - y2)


    def euclidean_distance(self, pos, goal):
        x1, y1 = pos
        x2, y2 = goal

        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)   

    # ---------------------------------------------------------
    # Get valid neighboring cells
    # ---------------------------------------------------------

    def get_neighbors(self, position, grid_size, walls):
        x, y = position

        width, height = grid_size

        candidates = [
            ((x, y + 1), "Up"),
            ((x, y - 1), "Down"),
            ((x - 1, y), "Left"),
            ((x + 1, y), "Right")
        ]

        neighbors = []

        for new_position, action in candidates:

            nx, ny = new_position

            if (
                0 <= nx < width
                and 0 <= ny < height
                and new_position not in walls
            ):
                neighbors.append(
                    (new_position, action)
                )

        return neighbors

    # ---------------------------------------------------------
    # BFS
    # ---------------------------------------------------------

    def bfs_search(self, start, goal, grid_size, walls):

        frontier = deque()

        frontier.append(
            (start, [])
        )

        reached = {start}

        while frontier:

            current, path = frontier.popleft()

            if current == goal:
                return path

            for neighbor, action in self.get_neighbors(
                current,
                grid_size,
                walls
            ):

                if neighbor not in reached:

                    reached.add(neighbor)

                    frontier.append(
                        (
                            neighbor,
                            path + [action]
                        )
                    )

        return []

    # ---------------------------------------------------------
    # DFS
    # ---------------------------------------------------------

    def dfs_search(self, start, goal, grid_size, walls):

        frontier = []

        frontier.append(
            (start, [])
        )

        reached = {start}

        while frontier:

            current, path = frontier.pop()

            if current == goal:
                return path

            for neighbor, action in self.get_neighbors(
                current,
                grid_size,
                walls
            ):

                if neighbor not in reached:

                    reached.add(neighbor)

                    frontier.append(
                        (
                            neighbor,
                            path + [action]
                        )
                    )

        return []

    # ---------------------------------------------------------
    # UCS
    # ---------------------------------------------------------

    def ucs_search(self, start, goal, grid_size, walls):

        frontier = []

        counter = 0

        heapq.heappush(
            frontier,
            (
                0,
                counter,
                start,
                []
            )
        )

        reached = {
            start: 0
        }

        while frontier:

            cost, _, current, path = heapq.heappop(
                frontier
            )

            if current == goal:
                return path

            for neighbor, action in self.get_neighbors(
                current,
                grid_size,
                walls
            ):

                new_cost = cost + 1

                if (
                    neighbor not in reached
                    or new_cost < reached[neighbor]
                ):

                    reached[neighbor] = new_cost

                    counter += 1

                    heapq.heappush(
                        frontier,
                        (
                            new_cost,
                            counter,
                            neighbor,
                            path + [action]
                        )
                    )

        return []

    # ---------------------------------------------------------
    # A*
    # ---------------------------------------------------------

    def astar_search(
        self,
        start_pos,
        goal_pos,
        walls,
        grid_size,
        heuristic_type="manhattan"
    ):

        priority_queue = []
        reached_states = set()

        if heuristic_type == "euclidean":
            heuristic_cost = self.euclidean_distance(start_pos, goal_pos)
        else:
            heuristic_cost = self.manhattan_distance(start_pos, goal_pos)

        heapq.heappush(
            priority_queue,
            (heuristic_cost, 0, start_pos, [])
        )

        while priority_queue:

            _, g_cost, current_pos, path_taken = heapq.heappop(
                priority_queue
            )

            if current_pos == goal_pos:
                return path_taken

            if current_pos in reached_states:
                continue

            reached_states.add(current_pos)

            for neighbor, action in self.get_neighbors(
                current_pos,
                grid_size,
                walls
            ):

                if neighbor in reached_states:
                    continue

                new_g_cost = g_cost + 1

                if heuristic_type == "euclidean":
                    new_h_cost = self.euclidean_distance(
                        neighbor,
                        goal_pos
                    )
                else:
                    new_h_cost = self.manhattan_distance(
                        neighbor,
                        goal_pos
                    )

                heapq.heappush(
                    priority_queue,
                    (
                        new_g_cost + new_h_cost,
                        new_g_cost,
                        neighbor,
                        path_taken + [action]
                    )
                )

        return None

    

    def find_closest_food(
        self,
        start,
        food_positions,
        grid_size,
        walls
    ):
        """Find the closest reachable food pellet."""

        closest_food = None
        closest_path = None

        for food in food_positions:

            # Select search algorithm
            if self.active_algo == "BFS":

                path = self.bfs_search(
                    start,
                    food,
                    grid_size,
                    walls
                )

            elif self.active_algo == "DFS":

                path = self.dfs_search(
                    start,
                    food,
                    grid_size,
                    walls
                )

            elif self.active_algo == "UCS":

                path = self.ucs_search(
                    start,
                    food,
                    grid_size,
                    walls
                )

            elif self.active_algo == "AStar":

                path = self.astar_search(
                    start,
                    food,
                    walls,
                    grid_size
                )

            else:

                raise ValueError(
                    "Invalid algorithm. "
                    "Use BFS, DFS, UCS, or AStar."
                )

            # Ignore unreachable food
            if not path and start != food:
                continue

            # Select shortest available path
            if (
                closest_path is None
                or len(path) < len(closest_path)
            ):

                closest_path = path
                closest_food = food

        return closest_food, closest_path

    

    def sense_and_act(self, percept: dict) -> str:

        

        if percept["food_here"]:

            return "Suck"

        
        if "agent_pos" in percept:
            self.position = tuple(
                percept["agent_pos"]
            )

        
        if not self.plan:

            grid_size = percept["grid_size"]

            walls = set(
                percept["walls"]
            )

            food_positions = set(
                percept["all_food"]
            )

            # Find closest food
            _, path = self.find_closest_food(
                self.position,
                food_positions,
                grid_size,
                walls
            )

            # Store complete offline plan
            if path:
                self.plan = path

       
        if self.plan:

            action = self.plan.pop(0)

            return action

        

        return "Forward"

if __name__ == "__main__":
    agent = SearchAgent()

    start = (0, 0)
    goal = (3, 4)

    print("Manhattan Distance:", agent.manhattan_distance(start, goal))
    print("Euclidean Distance:", agent.euclidean_distance(start, goal))
