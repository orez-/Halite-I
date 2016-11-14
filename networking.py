from hlt import *
import socket
import traceback
import struct
from ctypes import *
import sys

_productions = []
_width = -1
_height = -1

def serializeMoveSet(moves):
    return ''.join(
        '{} {} {} '.format(move.loc.x, move.loc.y, move.direction)
        for move in moves
    )


def deserializeMapSize(inputString):
    splitString = inputString.split(" ")

    global _width, _height
    _width = int(splitString.pop(0))
    _height = int(splitString.pop(0))


def deserializeProductions(inputString):
    splitString = iter(map(int, inputString.split(" ")))

    global _productions
    _productions = [
        [next(splitString) for _ in range(_width)]
        for _ in range(_height)
    ]

def deserializeMap(inputString):
    splitString = iter(map(int, inputString.split(" ")))

    m = GameMap(_width, _height)

    # We actualize the owners list so we can join it with the strength
    # list from the same stream, but we leave it in its compressed format
    remaining = _width * _height
    owners = []
    while remaining:
        counter = next(splitString)
        owner = next(splitString)
        owners.append((counter, owner))
        remaining -= counter

    owners_iter = (
        owner
        for counter, owner in owners
        for _ in range(counter)
    )

    m.contents = [
        [
            Site(
                owner=next(owners_iter),
                strength=next(splitString),
                production=production,
            ) for production in production_row
        ] for production_row in _productions
    ]

    return m


def sendString(toBeSent):
    toBeSent += '\n'

    sys.stdout.write(toBeSent)
    sys.stdout.flush()


def getString():
    return sys.stdin.readline().rstrip('\n')


def getInit():
    playerTag = int(getString())
    deserializeMapSize(getString())
    deserializeProductions(getString())
    m = deserializeMap(getString())

    return (playerTag, m)


def sendInit(name):
    sendString(name)


def getFrame():
    return deserializeMap(getString())


def sendFrame(moves):
    sendString(serializeMoveSet(moves))
