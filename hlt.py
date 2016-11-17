import collections
import math
import random

STILL = 0
NORTH = 1
EAST = 2
SOUTH = 3
WEST = 4

DIRECTIONS = list(range(0, 5))
CARDINALS = list(range(1, 5))

ATTACK = 0
STOP_ATTACK = 1


Location = collections.namedtuple('Location', 'x y')
Move = collections.namedtuple('Move', 'loc direction')
Site = collections.namedtuple('Site', 'owner strength production')


class GameMap:
    def __init__(self, width=0, height=0, numberOfPlayers=0):
        self.width = width
        self.height = height

        # self.contents = [
        #     [Site(0, 0, 0) for _ in range(self.width)]
        #     for _ in range(self.height)
        # ]
        self._units = {}

    def __iter__(self):
        for y, row in enumerate(self.contents):
            for x, elem in enumerate(row):
                yield Location(x, y), elem

    def units(self, myID):
        if myID not in self._units:
            self._units[myID] = [
                (location, site)
                for location, site in self
                if site.owner == myID
            ]
        return self._units[myID]

    def enactMoves(self, myID, moves):
        # doesn't handle combat
        gm = GameMap(self.width, self.height)

        # location: amt
        difference = collections.defaultdict(int)

        for loc, direction in moves:
            site = self.getSite(loc)
            if direction == STILL:
                difference[loc] += site.production
            else:
                difference[loc] -= site.strength
                next_loc = self.getLocation(loc, direction)
                difference[next_loc] += site.strength

        def apply_diff(site, amt):
            strength = 0
            owner = myID
            if site.owner == myID:
                strength = site.strength + amt
            else:
                strength = site.strength - amt
                if strength > 0:
                    owner = 0
            return Site(owner=owner, strength=min(abs(strength), 255), production=site.production)

        gm.contents = [
            [
                site if Location(x, y) not in difference else
                apply_diff(site, difference[Location(x, y)])
                for x, site in enumerate(row)
            ]
            for y, row in enumerate(self.contents)
        ]
        return gm

    def neighbors(self, loc):
        gen = (
            (direction, self.getLocation(Location(*loc), direction))
            for direction in random.sample(CARDINALS, len(CARDINALS))
        )
        return (
            (direction, location, self.getSite(location))
            for direction, location in gen
        )

    def inBounds(self, l):
        return l.x >= 0 and l.x < self.width and l.y >= 0 and l.y < self.height

    def getDistance(self, l1, l2):
        dx = abs(l1.x - l2.x)
        dy = abs(l1.y - l2.y)
        if dx > self.width / 2:
            dx = self.width - dx
        if dy > self.height / 2:
            dy = self.height - dy
        return dx + dy

    def getAngle(self, l1, l2):
        dx = l2.x - l1.x
        dy = l2.y - l1.y

        if dx > self.width - dx:
            dx -= self.width
        elif -dx > self.width + dx:
            dx += self.width

        if dy > self.height - dy:
            dy -= self.height
        elif -dy > self.height + dy:
            dy += self.height
        return math.atan2(dy, dx)

    def getLocation(self, loc, direction):
        x, y = loc
        if direction != STILL:
            if direction == NORTH:
                if y == 0:
                    y = self.height - 1
                else:
                    y -= 1
            elif direction == EAST:
                if x == self.width - 1:
                    x = 0
                else:
                    x += 1
            elif direction == SOUTH:
                if y == self.height - 1:
                    y = 0
                else:
                    y += 1
            elif direction == WEST:
                if x == 0:
                    x = self.width - 1
                else:
                    x -= 1
        return Location(x, y)

    def getSite(self, l, direction=STILL):
        l = self.getLocation(l, direction)
        return self.contents[l.y][l.x]
