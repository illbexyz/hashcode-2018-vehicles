from collections import namedtuple
from copy import deepcopy
from enum import Enum
from os import makedirs, path
from pprint import pprint
from random import randint, shuffle
from typing import List


class RideState(Enum):
    Unassigned = 0
    Assigned = 1
    Done = 2


class VehicleState(Enum):
    NoRide = 0
    GoingToRide = 1
    OnRide = 2


class Position(namedtuple('Position', ['x', 'y'])):
    def __str__(self):
        return "({}, {})".format(self.x, self.y)

    def __repr__(self):
        return self.__str__()


class Vehicle:
    def __init__(self):
        self.state = VehicleState.NoRide
        self.pos = Position(0, 0)
        self.remaining_turns = -1
        self.ride_ids = []

    def __str__(self):
        return "({}, Pos{}, RemTurns({}), RideIds{})".format(self.state, self.pos, self.remaining_turns, self.ride_ids)

    def __repr__(self):
        return self.__str__()


class Ride:
    def __init__(self, start_pos: Position, end_pos: Position, start_turn: int, end_turn: int):
        self.state = RideState.Unassigned
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.start_turn = start_turn
        self.end_turn = end_turn

    def __str__(self):
        return "({}, StartPos{}, EndPos{}, StartTurn({}), EndTurn({}))".format(self.state, self.start_pos, self.end_pos, self.start_turn, self.end_turn)

    def __repr__(self):
        return self.__str__()


def parse_input(filepath: str):
    with open(filepath) as file:
        content = file.read()
        lines = content.split("\n")
        first_line_tokens = lines[0].split(" ")
        rides_lines = lines[1:-1]

        rows = int(first_line_tokens[0])
        cols = int(first_line_tokens[1])
        n_vehicles = int(first_line_tokens[2])
        n_rides = int(first_line_tokens[3])
        starting_bonus = int(first_line_tokens[4])
        n_steps = int(first_line_tokens[5])

        rides = []
        for ride in rides_lines:
            ride_tokens = ride.split(" ")
            rides.append(
                Ride(
                    start_pos=Position(int(ride_tokens[0]), int(ride_tokens[1])),
                    end_pos=Position(int(ride_tokens[2]), int(ride_tokens[3])),
                    start_turn=int(ride_tokens[4]),
                    end_turn=int(ride_tokens[5])
                )
            )

        return rows, cols, n_vehicles, n_rides, starting_bonus, n_steps, rides


def build_vehicles(n_vehicles: int):
    return [Vehicle() for _ in range(n_vehicles)]


def distance(start_pos: Position, end_pos: Position):
    a, b = start_pos
    x, y = end_pos
    return abs(a - x) + abs(b - y)


def generate_output(filepath: str, vehicles: List[Vehicle]):
    last_slash_index = filepath.rfind("/")
    if not path.exists(filepath[:last_slash_index]):
        makedirs(filepath[:last_slash_index])
    with open(filepath, "w") as out_file:
        for v in vehicles:
            out_file.write(str(len(v.ride_ids)))
            for r in v.ride_ids:
                out_file.write(" {}".format(r))
            out_file.write("\n")


def choose_random(avail_ride_ids: List[int]):
    random_id = randint(0, len(avail_ride_ids)) - 1
    return random_id


def choose_first():
    return 0


def choose_nearest(vehicle: Vehicle, rides: List[Ride], avail_ride_ids: List[int], curr_turn: int):
    nearest_id = 0
    best_dist = 999999
    for r in range(len(avail_ride_ids)):
        dist = distance(vehicle.pos, rides[r].start_pos)
        if dist < best_dist and can_ride_be_made_by_vehicle(vehicle, rides[r], curr_turn):
            best_dist = dist
            nearest_id = r
    return nearest_id


def can_ride_be_made_by_vehicle(v: Vehicle, r: Ride, curr_turn: int):
    time_to_get_to_ride = distance(v.pos, r.start_pos)
    time_to_complete_ride = distance(r.start_pos, r.end_pos)
    return (curr_turn + time_to_get_to_ride + time_to_complete_ride) <= r.end_turn


def ride_score(v: Vehicle, r: Ride, curr_turn: int, bonus: int):
    score = 0
    has_bonus = False
    if can_ride_be_made_by_vehicle(v, r, curr_turn):
        score += distance(r.start_pos, r.end_pos)
        if curr_turn + distance(v.pos, r.start_pos) <= r.start_turn:
            score += bonus
            has_bonus = True
    return score


def choose_greedy(vehicle: Vehicle, rides: List[Ride], avail_ride_ids: List[int], curr_turn: int, bonus: int):
    best = (0, 0)
    for r in range(len(avail_ride_ids)):
        time_to_arrive = distance(vehicle.pos, rides[r].start_pos)
        score = ride_score(vehicle, rides[r], curr_turn, bonus) - (rides[r].start_turn - (time_to_arrive + curr_turn))
        if score > best[1]:
            best = (r, score)
    return best[0]


def choose_ride(vehicle: Vehicle, rides: List[Ride], avail_ride_ids: List[int], curr_turn: int, bonus: int):
    ride_id = choose_greedy(vehicle, rides, avail_ride_ids, curr_turn, bonus)
    return avail_ride_ids.pop(ride_id)


def simulate(sim_id: int, turns: int, rides: List[Ride], vehicles: List[Vehicle], bonus: int):
    ride_ids = [i for i in range(len(rides))]
    print("Simulation {} begins".format(sim_id))
    score = 0
    for t in range(turns):
        percentage = 100 - ((turns - t) / turns) * 100
        if percentage == 25 or percentage == 50 or percentage == 75:
            print("{}%...".format(percentage))
        for v in vehicles:
            if len(ride_ids) > 0:
                # Sta andando alla partenza della ride
                # Se deve ancora arrivare
                #     decremento i turni rimanenti
                # Altrimenti
                #     controllo che il turno corrente sia >= dell'inizio della ride
                #         faccio partire il veicolo
                if v.state == VehicleState.GoingToRide:
                    if v.remaining_turns > 0:
                        v.remaining_turns -= 1
                    else:
                        assigned_ride = rides[v.ride_ids[-1]]
                        if t >= assigned_ride.start_turn:
                            v.state = VehicleState.OnRide
                            v.remaining_turns = distance(v.pos, assigned_ride.end_pos)

                # Sta eseguendo la ride
                # Decremento i turni rimanenti
                # Se e' arrivato
                #
                if v.state == VehicleState.OnRide:
                    v.remaining_turns -= 1
                    if v.remaining_turns == 0:
                        v.state = VehicleState.NoRide
                        satisfied_ride = rides[v.ride_ids[-1]]
                        v.pos = satisfied_ride.end_pos
                        satisfied_ride.state = RideState.Done
                # Il veicolo e' fermo, devo assegnargli una ride
                if v.state == VehicleState.NoRide:
                    if len(ride_ids) > 0:
                        ride_id = choose_ride(v, rides, ride_ids, t, bonus)
                        assigned_ride = rides[ride_id]
                        r_score = ride_score(v, assigned_ride, t, bonus)
                        score += r_score
                        v.ride_ids.append(ride_id)
                        v.state = VehicleState.GoingToRide
                        v.remaining_turns = distance(v.pos, assigned_ride.start_pos)
                        assigned_ride.state = RideState.Assigned
    return score


debug = True
# filename = "a_example.in"
filename = "b_should_be_easy.in"
# filename = "c_no_hurry.in"
# filename = "d_metropolis.in"
# filename = "e_high_bonus.in"
in_filepath = "../inputs/" + filename
out_filepath = "../outputs/{}.out".format(filename[:-3])
rows, cols, n_vehicles, n_rides, m_bonus, m_turns, m_rides = parse_input(in_filepath)
m_vehicles = build_vehicles(n_vehicles)

m_rides.sort(key=lambda ride: ride.start_turn)

if debug:
    print("-----PARAMS-----")
    print("Rows\t\t", rows)
    print("Columns\t\t", cols)
    print("N. Vehicles\t", n_vehicles)
    print("N. Rides\t", len(m_rides))
    print("Bonus\t\t", m_bonus)
    print("Turns\t\t", m_turns)
    print("----------------")
    print()
    # print("------RIDES-----")
    # pprint(rides)
    # print("----------------")
    # print()
    # print("----VEHICLES----")
    # pprint(vehicles)
    # print("----------------")

sim_score = simulate(0, m_turns, m_rides, m_vehicles, m_bonus)
print("Score: {}".format(sim_score))
generate_output(out_filepath, m_vehicles)

# best_score = 0
# sim_iteration = 1
# while True:
#     sim_rides = deepcopy(m_rides)
#     sim_vehicles = deepcopy(m_vehicles)
#     sim_score = simulate(sim_iteration, m_turns, sim_rides, sim_vehicles, m_bonus)
#     print("Score: {}".format(sim_score))
#     sim_iteration += 1
#     if sim_score > best_score:
#         best_score = sim_score
#         print("!!! Record beaten !!!", best_score)
#         generate_output(out_filepath, sim_vehicles)
