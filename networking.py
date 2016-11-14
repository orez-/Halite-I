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

    y = 0
    x = 0
    owners = []
    row = []
    while y != m.height:
        counter = next(splitString)
        owner = next(splitString)

        left_in_row = m.width - x
        if left_in_row <= counter:
            counter -= left_in_row
            owners.append(row + [owner] * left_in_row)
            num_rows, x = divmod(counter, m.width)
            # as a temp read-only structure, same-reference is fine
            owners += [[owner] * m.width] * num_rows
            row = [owner] * x
            y += num_rows + 1
        else:
            x += counter
            row += [owner] * counter

    m.contents = [
        [
            Site(owner=owner, strength=next(splitString), production=_productions[a][b])
            for b, owner in enumerate(owner_row)
        ] for a, owner_row in enumerate(owners)
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
