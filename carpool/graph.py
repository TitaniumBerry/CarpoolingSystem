from collections import deque
from .models import Edge
from itertools import permutations

def bfs(start_node, end_node):

    if start_node == end_node:
        return [start_node]

    queue = deque()
    queue.append((start_node, [start_node]))

    visited = set()
    visited.add(start_node.id)

    while queue:
        current_node, path = queue.popleft()

        outgoing_edges = Edge.objects.filter(from_node=current_node).select_related('to_node')

        for edge in outgoing_edges:
            neighbour = edge.to_node

            if neighbour.id in visited:
                continue

            new_path = path + [neighbour]

            if neighbour == end_node:
                return new_path
            
            visited.add(neighbour.id)
            queue.append((neighbour, new_path))
    
    return None


def nodes_within_distance(start_node, max_distance):
    visited = {start_node.id}

    queue = deque()
    queue.append([start_node, 0])

    result = set()
    result.add(start_node.id)

    while queue:
        item = queue.popleft()
        current_node = item[0]
        distance = item[1]

        if distance >= max_distance:
            continue

        outgoing_edges = Edge.objects.filter(from_node=current_node).select_related('to_node')

        for edge in outgoing_edges:
            neighbour = edge.to_node

            if neighbour.id not in visited:
                visited.add(neighbour.id)
                result.add(neighbour.id)
                queue.append([neighbour, distance+1])
    
    return result

def is_within_2_nodes_of_route(node, remaining_route_nodes):

    for route_node in remaining_route_nodes:
        reachable = nodes_within_distance(route_node, 2)
        if node.id in reachable:
            return True
    
    return False


def calculate_fare(original_route, new_route, pickup_node, dropoff_node, base_fee = 2.0, unit_price = 1.0):
    detour = len(new_route) - len(original_route)

    total = 0.0
    in_ride = False

    for i in range(len(new_route) - 1):
        current = new_route[i]
        next_node = new_route[i + 1]

        if current == pickup_node:
            in_ride = True
        if current == dropoff_node:
            in_ride = False

        if in_ride:
            n_i = 1
            total += 1.0 / n_i

    fare = unit_price * total + base_fee
    return round(fare, 2), detour

def insert_passenger_into_route(route, pickup_node, dropoff_node):
    best_route = None
    best_length = float('inf')

    for i in range(len(route)):
        for j in range(i+1, len(route)+1):
            new_route  = route[:i] + [pickup_node] + route[i:j] + [dropoff_node] + route[j:]

            if len(new_route) < best_length:
                best_length = len(new_route)
                best_route = new_route
    
    return best_route


def bfs_distance(start_node, end_node):
    if start_node == end_node:
        return 0    


    queue = deque()
    queue.append((start_node, 0))
    visited = {start_node.id}

    while queue:
        current, dist = queue.popleft()
        for edge in Edge.objects.filter(from_node=current).select_related('to_node'):
            neighbour = edge.to_node
            if neighbour.id in visited:
                continue
            if neighbour == end_node:
                return dist + 1
            
            visited.add(neighbour.id)
            queue.append((neighbour, dist + 1))

    return None

def optimize_route_for_passengers(start_node, end_node, passenger_stops):
    if not passenger_stops:
        return bfs(start_node, end_node), []
    
    pickups = [(ps[0], i, 'pickup') for i, ps in enumerate(passenger_stops)]
    dropoffs = [(ps[1], i, 'dropoffs') for i, ps in enumerate(passenger_stops)]
    all_stops = pickups + dropoffs

    best_route = None
    best_length = float('inf')
    best_order = None

    for perm in permutations(all_stops):
        valid = True
        pickup_seen = set()
        
        for node, passenger_idx, stop_type in perm:
            if stop_type == 'pickup':
                pickup_seen.add(passenger_idx)
            elif stop_type == 'dropoff':
                if passenger_idx not in pickup_seen:
                    valid = False
                    break

        if not valid:
            continue


        waypoints = [start_node] + [s[0] for s in perm] + [end_node]
        full_route = []
        route_valid = True


        for k in range(len(waypoints) - 1):
            segment = bfs(waypoints[k], waypoints[k+1])
            if segment is None:
                route_valid = False
                break
            if full_route:
                full_route.extend(segment[1:])
            else:
                full_route = segment

        if not route_valid:
            continue
        
        if len(full_route) < best_length:
            best_length = len(full_route)
            best_route = full_route
            best_order = list(perm)
        
    return best_route, best_order



