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
    splitString = inputString.split(" ")

    for a in range(0, _height):
        row = []
        for b in range(0, _width):
            row.append(int(splitString.pop(0)))
        _productions.append(row)


def deserializeMap(inputString):
    splitString = iter(map(int, inputString.split(" ")))

    m = GameMap(_width, _height)

    y = 0
    x = 0
    counter = 0
    owner = 0
    while y != m.height:
        counter = next(splitString)
        owner = next(splitString)
        for a in range(counter):
            m.contents[y][x].owner = owner
            x += 1
            if x == m.width:
                x = 0
                y += 1

    for a in range(_height):
        for b in range(_width):
            m.contents[a][b].strength = next(splitString)
            m.contents[a][b].production = _productions[a][b]

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
