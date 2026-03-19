from collections import deque
from .models import Edge

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

    


