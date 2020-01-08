import codecs
from collections import defaultdict
import curses
import itertools
import random

import pdb
dbg = False

SHAPE = 0
COLOR = 1



class Vec2:

    def __init__(self, x, y):
        self.val = (x, y)

    @property
    def x(self):
        return self.val[0]
    @property
    def y(self):
        return self.val[1]

    def __add__(self, other):
        return (self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return (self.x - other.x, self.y - other.y)

    def __hash__(self):
        return self.val.__hash__()

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


class Board:

    DIRS = [Vec2(0, -1), Vec2(0, 1), Vec2(1, 0), Vec2(-1, 0)]

    def __init__(self, w, h, num_colors):
        self.w = w
        self.h = h
        self.num_colors = num_colors
        self._open = [Vec2(0, 0)]
        self.open_tiles = set()
        self.open_tiles.add((self.w // 2, self.h // 2))
        self.tiles = defaultdict(lambda: None)
        self.grid = [[None for i in range(h)] for j in range(w)]

    def get_open_tiles(self):
        return self.open_tiles

    def test_move(self, loc, tile):
        x, y = loc

        #get horizontal and vertical contiguous tiles
        horz = []
        vert = []

        if dbg:
            debug()

        for i in range(1, self.num_colors):
            xx = (x + i) % self.w
            if self.grid[xx][y]:
                horz.append(self.grid[xx][y])
            else:
                break

        for i in range(1, self.num_colors):
            xx = (x - i) % self.w
            if self.grid[xx][y]:
                horz.append(self.grid[xx][y])
            else:
                break

        for i in range(1, self.num_colors):
            yy = (y + i) % self.h
            if self.grid[x][yy]:
                vert.append(self.grid[x][yy])
            else:
                break

        for i in range(1, self.num_colors):
            yy = (y - i) % self.h
            if self.grid[x][yy]:
                vert.append(self.grid[x][yy])
            else:
                break

        vert.append(tile)
        horz.append(tile)

        score_h = self._test_group(horz)
        score_v = self._test_group(vert)
        if score_h == 0 or score_v == 0:
            return 0

        return score_h + score_v

    def _test_group(self, tiles):
        '''Tests if a group of tiles is valid assuming they
           were to be placed contiguously in a line.

           Returns the score that placing those tiles would generate (0 for invalid)
        '''
        lt = len(tiles)
        if lt > self.num_colors:
            return 0
        elif lt == 1:
            return 1

        colors = [tile[COLOR] for tile in tiles]
        shapes = [tile[SHAPE] for tile in tiles]

        lc = len(set(colors)) # all equal if == 1, all unique if == lt
        ls = len(set(shapes))

        if lc == ls == 1:
            return 0

        debug()

        if lc == lt:
            # all colors are unique - shapes must be identical
            if ls != 1:
                return 0
        else:
            # duplicate colors - all colors must be identical and shapes must be unique
            if lc != 1 and ls != lt:
                return 0

        if ls == lt:
            # all shapes are unique - colors must be identical
            if lc != 1:
                return 0
        else:
            # duplicate shapes - all shapes must be identical and all colors must be unique
            if ls != 1 and lc != lt:
                return 0


        if lt == self.num_colors:
            return self.num_colors * 2
        return lt

    def move(self, loc, tile):
        '''Places a tile at a location'''
        score = self.test_move(loc, tile)
        if score > 0:
            x, y = loc
            self.grid[x][y] = tile
            self.open_tiles.remove((x, y))
            for i, j in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                xx = (x + i) % self.w
                yy = (y + j) % self.h
                if not self.grid[xx][yy]:
                    self.open_tiles.add((xx, yy))
        return score

class Bag:

    def __init__(self, num_colors=6, num_sets=3):
        self.num_colors = num_colors
        self.infinite   = num_sets < 1
        if num_sets < 1:
            num_sets = 1
        self.tiles = [tile for tile in itertools.product(range(num_colors), repeat=2)] * num_sets
        random.shuffle(self.tiles)

    def draw(self, n):
        tiles = []
        for i in range(n):
            if self.tiles:
                if self.infinite:
                    tiles.append(self.tiles[random.randint(0, len(self.tiles) - 1)])
                else:
                    tiles.append(self.tiles.pop())
        return tiles

def debug():
    curses.nocbreak()
    curses.echo()
    curses.endwin()
    import pdb
    pdb.set_trace()

class Player:

    def __init__(self, board, bag, hand_size=6):
        self.board = board
        self.bag   = bag
        self.hand_size = hand_size
        self.score = 0
        self.hand  = []
        self.pickup_tiles()

    def play(self):
        self.play_one()
        self.pickup_tiles()
        if len(self.hand) == 0:
            # game is done
            return False
        return True

    def brute_force(self):
        open_tiles = self.board.get_open_tiles()

    def play_one(self):
        open_tiles = list(self.board.get_open_tiles())
        random.shuffle(open_tiles)
        for x, y in open_tiles:
            for tile in self.hand:
                if self.board.test_move((x, y), tile):
                    score = self.board.move((x, y), tile)
                    if score:
                        self.hand.remove(tile)
                        self.score += score
                        return True
        return False

    def pickup_tiles(self):
        num_to_pickup = self.hand_size - len(self.hand)
        self.hand.extend(self.bag.draw(num_to_pickup))

    def hand_to_str(self):
        s = ""
        for tile in self.hand:
            r = 255 * (tile[1] in [5, 0, 1])
            #g = 255 * (tile[1] in [1, 2, 3])
            #b = 255 * (tile[1] in [3, 4, 5])
            #s += codecs.decode(r"\033[48;2;{};{};{}m".format(r, g, b), 'unicode_escape') + self.SYMBOLS[tile[0]] + "\033[0m"
        return s

class Game:

    SYMBOLS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self, screen, num_players, num_colors, hand_size):
        self.h, self.w = screen.getmaxyx()

        self.num_players = num_players
        self.num_colors = num_colors
        self.hand_size = hand_size
        self.tile_bag = Bag(num_colors=num_colors)
        self.board = Board(self.w, self.h - self.num_players - 1, num_colors=num_colors)
        self.players = [Player(self.board, self.tile_bag, hand_size) for i in range(num_players)]
        self.current_player = 0

        self.header = curses.newwin(num_players + 1, self.w, 0, 0)
        self.screen = curses.newwin(self.h - num_players - 1, self.w, num_players + 1, 0)
        for i in range(num_colors):
            print(curses.color_content(i))

        curses.init_color(0, 0, 0, 0)
        curses.init_color(1, 1000, 1000, 1000)
        curses.init_color(2, 1000, 0, 0)
        curses.init_color(3, 1000, 1000, 0)
        curses.init_color(4, 0, 1000, 0)
        curses.init_color(5, 0, 1000, 1000)
        curses.init_color(6, 0, 0, 1000)
        curses.init_color(7, 1000, 0, 1000)

        for i in range(6):
            curses.init_pair(i+1, i+2, 0)

    def play(self):

        if not self.players[self.current_player].play():
            return True

        self.current_player = (self.current_player + 1) % self.num_players
        return False

    def stop(self):
        import time
        time.sleep(10)
        pass

    def draw(self):
        '''Draw the game board on screen'''

        # draw header
        self.header.addstr(0, self.w // 2 - 3, "Quirkle")

        # draw players and their hands
        for i in range(self.num_players):
            self.header.addstr(i + 1, 0, "Player {:> 3d} | {:> 4d} | ".format(
                i + 1,
                self.players[i].score
            ))
            for tile in self.players[i].hand:
                self.header.addch(self.SYMBOLS[tile[SHAPE]], curses.color_pair(tile[COLOR] + 1))
            if len(self.players[i].hand) < self.hand_size:
                for i in range(self.hand_size - len(self.players[i].hand)):
                    self.header.addch(" ")

            #self.header.addstr(i + 1, 0, "Player {}: {}".format(i + 1, self.players[i].hand_to_str()))

        self.header.refresh()

        #self.screen.addstr(str([curses.color_content(i) for i in range(self.num_colors)]))
        for x in range(self.board.w):
            for y in range(self.board.h):
                tile = self.board.grid[x][y]
                if tile:
                    sym = self.SYMBOLS[tile[SHAPE]]
                    self.screen.addch(y, x, sym, curses.color_pair(tile[COLOR] + 1))
        self.screen.refresh()

def main(screen):
    global dbg
    game = Game(screen, num_players=3, num_colors=6, hand_size=6)

    assert game.board._test_group([(0, 0), (0, 0)]) == 0
    assert game.board._test_group([(0, 0), (0, 1)]) == 1
    assert game.board._test_group([(0, 0), (1, 1)]) == 0

    exit()

    done = False
    while not done:
        game.draw()
        a = screen.getch()
        if a == ord('d'):
            dbg = True
        elif a == ord('q'):
            break
        done = game.play()

    game.stop()

if __name__ == "__main__":

    curses.wrapper(main)
