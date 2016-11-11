import collections

import hlt
import networking


def reverse(direction):
    if direction == hlt.NORTH:
        return hlt.SOUTH
    elif direction == hlt.SOUTH:
        return hlt.NORTH
    elif direction == hlt.EAST:
        return hlt.WEST
    elif direction == hlt.WEST:
        return hlt.EAST


def find_edges(gameMap, start, myID):
    start = hlt.Location(*start)
    seen = {start}
    site = gameMap.getSite(start)
    queue = collections.deque([(start, site)])

    while queue:
        location, site = queue.popleft()

        if site.owner != myID:
            yield location
            continue

        for direction, loc, next_site in gameMap.neighbors(location):
            if loc not in seen:
                seen.add(loc)
                queue.append((loc, next_site))


def get_flow_map(gameMap, start, myID):
    edges = collections.deque(find_edges(gameMap, start, myID))

    seen = set(edges)
    flow_map = {}

    while edges:
        location = edges.popleft()

        for direction, loc, next_site in gameMap.neighbors(location):
            if loc not in seen and next_site.owner == myID:
                flow_map[loc] = reverse(direction)
                seen.add(loc)
                edges.append(loc)
    return flow_map


def turn(gameMap):
    flow_map = {}
    for location, site in gameMap:
        if site.owner != myID:
            continue
        # if you can take a spot, do so.
        # if you're a leading edge, wait.
        # if you're weaker than a production, wait
        # move towards the frontline
        manifest_destiny = [
            (
                sum(1 for _, _, s in gameMap.neighbors(loc) if s.owner == myID),
                direction,
                next_site.strength < site.strength,
            )
            for direction, loc, next_site in gameMap.neighbors(location)
            if next_site.owner != myID
        ]
        weak_neighbors = [
            (value, direction)
            for value, direction, weak_neighbor in manifest_destiny
            if weak_neighbor
        ]
        if weak_neighbors:
            _, direction = min(weak_neighbors)
            yield location, direction
            continue

        if manifest_destiny:
            yield location, hlt.STILL
            continue

        if min(site.production * 3, 100) > site.strength:
            yield location, hlt.STILL
            continue

        if location not in flow_map:
            flow_map.update(get_flow_map(gameMap, location, myID))
        direction = flow_map[location]
        yield location, direction
        continue


if __name__ == '__main__':
    myID, gameMap = networking.getInit()
    networking.sendInit("Orez[Adventurer]")

    while True:
        gameMap = networking.getFrame()
        moves = [
            hlt.Move(
                hlt.Location(x, y),
                direction,
            )
            for (x, y), direction in turn(gameMap)
        ]
        networking.sendFrame(moves)
