import random

import hlt
import networking


if __name__ == '__main__':
    myID, gameMap = networking.getInit()
    networking.sendInit("Orez")

    while True:
        moves = []
        gameMap = networking.getFrame()
        for y in range(gameMap.height):
            for x in range(gameMap.width):
                if gameMap.getSite(hlt.Location(x, y)).owner == myID:
                    moves.append(hlt.Move(hlt.Location(x, y), int(random.random() * 5)))
        networking.sendFrame(moves)
