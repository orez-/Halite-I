import collections
import heapq
import itertools
import logging

import hlt
import networking


def init_logger():
    _log = logging.getLogger('mybot')
    _handler = logging.FileHandler('bot.log')
    _log.addHandler(_handler)
    _log.setLevel(logging.INFO)
    _log.info("=" * 80)
    return _log


_log = init_logger()

def reverse(direction):
    if direction == hlt.NORTH:
        return hlt.SOUTH
    elif direction == hlt.SOUTH:
        return hlt.NORTH
    elif direction == hlt.EAST:
        return hlt.WEST
    elif direction == hlt.WEST:
        return hlt.EAST


def find_edges(gameMap, start, myID, seen=()):
    start = hlt.Location(*start)
    seen = {start} | set(seen)
    site = gameMap.getSite(start)
    queue = collections.deque([(start, site)])

    while queue:
        location, site = queue.popleft()

        if site.owner != myID:
            yield location, site
            continue

        for direction, loc, next_site in gameMap.neighbors(location):
            if loc not in seen:
                seen.add(loc)
                queue.append((loc, next_site))


def get_flow_map(gameMap, start, myID):
    edges = collections.deque(loc for loc, _ in find_edges(gameMap, start, myID))

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


def strength_to_first_contact(gameMap, start, myID):
    start = hlt.Location(*start)
    seen = {start}
    site = gameMap.getSite(start)

    pqueue = [(0, start, site)]

    while pqueue:
        strength, location, site = heapq.heappop(pqueue)

        if site.owner and site.owner != myID:
            return strength

        for direction, loc, next_site in gameMap.neighbors(location):
            if loc not in seen:
                heapq.heappush(pqueue, (strength + next_site.strength, loc, next_site))
                seen.add(loc)

    raise Exception("no opponents?")


def successors(gameMap, myID):
    units = gameMap.units(myID)
    for dirs in itertools.product(hlt.DIRECTIONS, repeat=len(units)):
        moves = [
            hlt.Move(location, direction)
            for (location, _), direction in zip(units, dirs)
        ]
        yield moves, gameMap.enactMoves(myID, moves)


def troops_to_mobilize(gameMap, target, myID, seen=()):
    def _best_neighbors(dir_loc_site):
        _, _, site = dir_loc_site
        return -site.strength

    loc, site = target
    target_strength = site.strength
    troops = collections.defaultdict(dict)
    seen = {loc} | set(seen)

    queue = collections.deque([(None, loc, 0, 0)])

    while queue:
        # TODO: YOU CAN IMPROVE THIS BY DEALING A PRODUCTION'S WORTH OF
        # STRENGTH DAMAGE WHEN YOU EXPAND A BATTALION
        direction, location, strength, distance = queue.popleft()
        target_strength -= strength
        troops[distance][location] = direction

        if target_strength < 0:
            _log.info("the troops: %s", troops)
            del troops[0]
            return troops

        neighbors = sorted((
            (direction, loc, next_site)
            for direction, loc, next_site in gameMap.neighbors(location)
            if next_site.owner == myID and loc not in seen
        ), key=_best_neighbors)


        for direction, loc, next_site in neighbors:
            queue.append((reverse(direction), loc, next_site.strength, distance + 1))
            seen.add(loc)
    return None  # Everyone just take a minute.


def turn(gameMap, myID):
    return starting_turn(gameMap, myID)
    # return std_turn(gameMap, myID)


def starting_turn(gameMap, myID):
    def _edge_score(loc_site):
        loc, site = loc_site
        return site.production / (site.strength or 0.1)

    # This function sort of makes the assumption that your units are contiguous.
    # If you're small enough to trigger this and you have two groups
    # of units, you have bigger problems.
    units = dict(gameMap.units(myID))
    moved_troops = []

    while units:
        # if none of your edges are weak, send reinforcements
        any_unit_loc = next(iter(units))
        edges = list(find_edges(gameMap, any_unit_loc, myID, moved_troops))

        if not edges:
            break

        # pick the spot that will pay for itself the soonest.
        target = max(edges, key=_edge_score)
        troop_waves = troops_to_mobilize(gameMap, target, myID, moved_troops)
        if not troop_waves:
            break

        # The team who should move
        mobile_battalion = max(troop_waves)

        for i, wave in troop_waves.items():
            for loc, direction in wave.items():
                yield loc, direction if mobile_battalion == i else hlt.STILL
                moved_troops.append(loc)
                del units[loc]

    for loc in units:
        yield loc, hlt.STILL


def std_turn(gameMap, myID):
    flow_map = {}
    for location, site in gameMap.units(myID):
        # if you can cleanly take a spot, do so.
        # if you're a leading edge, wait.
        # if you're weaker than 3x your production, wait
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


def main():
    myID, gameMap = networking.getInit()
    networking.sendInit("Orez[Miner]")

    while True:
        gameMap = networking.getFrame()
        moves = [
            hlt.Move(
                hlt.Location(x, y),
                direction,
            )
            for (x, y), direction in turn(gameMap, myID)
        ]
        networking.sendFrame(moves)


if __name__ == '__main__':
    main()
