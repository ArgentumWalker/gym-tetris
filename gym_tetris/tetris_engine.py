# Modified from Tetromino by lusob luis@sobrecueva.com
# http://lusob.com
# Released under a "Simplified BSD" license

import copy
import numpy as np
from random import Random

# Game
BOARDWIDTH = 10
BOARDHEIGHT = 20

# Render
BOXSIZE = 20
WINDOWWIDTH = BOXSIZE * BOARDWIDTH + 10
WINDOWHEIGHT = BOXSIZE * BOARDHEIGHT + 10

BLANK = '.'

#               R    G    B
WHITE = (255, 255, 255)
GRAY = (185, 185, 185)
BLACK = (0, 0, 0)
RED = (155, 0, 0)
LIGHTRED = (175, 20, 20)
GREEN = (0, 155, 0)
LIGHTGREEN = (20, 175, 20)
BLUE = (0, 0, 155)
LIGHTBLUE = (20, 20, 175)
YELLOW = (155, 155, 0)
LIGHTYELLOW = (175, 175, 20)

BORDERCOLOR = BLUE
BGCOLOR = BLACK
TEXTCOLOR = WHITE
TEXTSHADOWCOLOR = GRAY
COLORS = (BLUE, GREEN, RED, YELLOW)
LIGHTCOLORS = (LIGHTBLUE, LIGHTGREEN, LIGHTRED, LIGHTYELLOW)
assert len(COLORS) == len(LIGHTCOLORS)  # each color must have light color

TEMPLATEWIDTH = 5
TEMPLATEHEIGHT = 5

S_SHAPE_TEMPLATE = [['..OO.',
                     '.OO..',
                     '.....',
                     '.....',
                     '.....'],
                    ['..O..',
                     '..OO.',
                     '...O.',
                     '.....',
                     '.....']]

Z_SHAPE_TEMPLATE = [['.OO..',
                     '..OO.',
                     '.....',
                     '.....',
                     '.....'],
                    ['..O..',
                     '.OO..',
                     '.O...',
                     '.....',
                     '.....']]

I_SHAPE_TEMPLATE = [['..O..',
                     '..O..',
                     '..O..',
                     '..O..',
                     '.....'],
                    ['OOOO.',
                     '.....',
                     '.....',
                     '.....',
                     '.....']]

O_SHAPE_TEMPLATE = [['.OO..',
                     '.OO..',
                     '.....',
                     '.....',
                     '.....']]

J_SHAPE_TEMPLATE = [['.O...',
                     '.OOO.',
                     '.....',
                     '.....',
                     '.....'],
                    ['..OO.',
                     '..O..',
                     '..O..',
                     '.....',
                     '.....'],
                    ['.OOO.',
                     '...O.',
                     '.....',
                     '.....',
                     '.....'],
                    ['..O..',
                     '..O..',
                     '.OO..',
                     '.....',
                     '.....']]

L_SHAPE_TEMPLATE = [['...O.',
                     '.OOO.',
                     '.....',
                     '.....',
                     '.....'],
                    ['..O..',
                     '..O..',
                     '..OO.',
                     '.....',
                     '.....'],
                    ['.OOO.',
                     '.O...',
                     '.....',
                     '.....',
                     '.....'],
                    ['.OO..',
                     '..O..',
                     '..O..',
                     '.....',
                     '.....']]

T_SHAPE_TEMPLATE = [['..O..',
                     '.OOO.',
                     '.....',
                     '.....',
                     '.....'],
                    ['..O..',
                     '..OO.',
                     '..O..',
                     '.....',
                     '.....'],
                    ['.OOO.',
                     '..O..',
                     '.....',
                     '.....',
                     '.....'],
                    ['..O..',
                     '.OO..',
                     '..O..',
                     '.....',
                     '.....']]

PIECES = {'S': S_SHAPE_TEMPLATE,
          'Z': Z_SHAPE_TEMPLATE,
          'J': J_SHAPE_TEMPLATE,
          'L': L_SHAPE_TEMPLATE,
          'I': I_SHAPE_TEMPLATE,
          'O': O_SHAPE_TEMPLATE,
          'T': T_SHAPE_TEMPLATE}

PIECE_TO_ID = {
    'S': 1,
    'Z': 2,
    'J': 3,
    'L': 4,
    'I': 5,
    'O': 6,
    'T': 7}


class GameState:
    def __init__(self):
        self.pygame_initiated = False
        self.random = Random()

        # DEBUG
        self.total_lines = 0

        # setup variables for the start of the game
        self.board = self.getBlankBoard()
        self.movingDown = False  # note: there is no movingUp variable
        self.movingLeft = False
        self.movingRight = False
        self.score = 0
        self.lines = 0
        self.height = 0
        self.level, self.fallFreq = self.calculateLevelAndFallFreq()

        self.fallingPiece = self.getNewPiece()
        self.nextPiece = self.getNewPiece()

        self.frame_step([1, 0, 0, 0, 0, 0])

    def seed(self, seed):
        self.random.seed(seed)

    def reinit(self):
        self.board = self.getBlankBoard()
        self.movingDown = False  # note: there is no movingUp variable
        self.movingLeft = False
        self.movingRight = False
        self.score = 0
        self.lines = 0
        self.height = 0
        self.level, self.fallFreq = self.calculateLevelAndFallFreq()

        self.fallingPiece = self.getNewPiece()
        self.nextPiece = self.getNewPiece()

        self.frame_step([1, 0, 0, 0, 0, 0])

    def get_observation(self):
        board = copy.deepcopy(self.board)
        for x in range(BOARDWIDTH):
            for y in range(BOARDHEIGHT):
                board[x][y] = (0 if board[x][y] == BLANK else 1)

        if self.fallingPiece is not None:
            shiftx, shifty = self.fallingPiece['x'], self.fallingPiece['y']
            for x in range(TEMPLATEWIDTH):
                for y in range(TEMPLATEHEIGHT):
                    shapeToDraw = PIECES[self.fallingPiece['shape']][self.fallingPiece['rotation']]
                    if shapeToDraw[y][x] != BLANK:
                        board[shiftx + x][shifty + y] = 2
        return board

    def frame_step(self, input):
        self.movingLeft = False
        self.movingRight = False

        reward = 0
        terminal = False

        # none is 100000, left is 010000, up is 001000, right is 000100, space is 000010, q is 000001
        if self.fallingPiece == None:
            # No falling piece in play, so start a new piece at the top
            self.fallingPiece = self.nextPiece
            self.nextPiece = self.getNewPiece()# reset self.lastFallTime

            if not self.isValidPosition():
                terminal = True

                self.reinit()
                return self.get_observation(), reward, terminal  # can't fit a new piece on the self.board, so game over

        # moving the piece sideways
        if (input[1] == 1) and self.isValidPosition(adjX=-1):
            self.fallingPiece['x'] -= 1
            self.movingLeft = True
            self.movingRight = False

        elif (input[3] == 1) and self.isValidPosition(adjX=1):
            self.fallingPiece['x'] += 1
            self.movingRight = True
            self.movingLeft = False

        # rotating the piece (if there is room to rotate)
        elif (input[2] == 1):
            self.fallingPiece['rotation'] = (self.fallingPiece['rotation'] + 1) % len(
                PIECES[self.fallingPiece['shape']])
            if not self.isValidPosition():
                self.fallingPiece['rotation'] = (self.fallingPiece['rotation'] - 1) % len(
                    PIECES[self.fallingPiece['shape']])

        elif (input[5] == 1):  # rotate the other direction
            self.fallingPiece['rotation'] = (self.fallingPiece['rotation'] - 1) % len(
                PIECES[self.fallingPiece['shape']])
            if not self.isValidPosition():
                self.fallingPiece['rotation'] = (self.fallingPiece['rotation'] + 1) % len(
                    PIECES[self.fallingPiece['shape']])

        # move the current piece all the way down
        elif (input[4] == 1):
            self.movingDown = False
            self.movingLeft = False
            self.movingRight = False
            for i in range(1, BOARDHEIGHT):
                if not self.isValidPosition(adjY=i):
                    break
            self.fallingPiece['y'] += i - 1

        # handle moving the piece because of user input
        if (self.movingLeft or self.movingRight):
            if self.movingLeft and self.isValidPosition(adjX=-1):
                self.fallingPiece['x'] -= 1
            elif self.movingRight and self.isValidPosition(adjX=1):
                self.fallingPiece['x'] += 1

        if self.movingDown:
            self.fallingPiece['y'] += 1

        # see if the piece has landed
        cleared = 0
        score = self.score
        if not self.isValidPosition(adjY=1):
            # falling piece has landed, set it on the self.board
            self.addToBoard()

            cleared = self.removeCompleteLines()
            if cleared > 0:
                if cleared == 1:
                    self.score += 40 * self.level
                elif cleared == 2:
                    self.score += 100 * self.level
                elif cleared == 3:
                    self.score += 300 * self.level
                elif cleared == 4:
                    self.score += 1200 * self.level

            #self.score += self.fallingPiece['y']

            self.lines += cleared
            self.total_lines += cleared

            height_delta = self.height - self.getHeight()
            self.height = self.getHeight()

            self.level, self.fallFreq = self.calculateLevelAndFallFreq()
            self.fallingPiece = None

        else:
            # piece did not land, just move the piece down
            self.fallingPiece['y'] += 1
            height_delta = 0

        #if cleared > 0:
        #    reward = 100 * cleared
        reward = self.score - score

        return self.get_observation(), reward, terminal

    def getImage(self):
        image_data = np.zeros((WINDOWHEIGHT, WINDOWWIDTH, 3), dtype=np.int)
        image_data[:, :] = BGCOLOR
        self.drawBoard(image_data)
        if self.fallingPiece is not None:
            self.drawPiece(image_data, self.fallingPiece)
        return image_data

    def getActionSet(self):
        return range(6)

    def getHeight(self):
        stack_height = 0
        for i in range(0, BOARDHEIGHT):
            blank_row = True
            for j in range(0, BOARDWIDTH):
                if self.board[j][i] != '.':
                    blank_row = False
            if not blank_row:
                stack_height = BOARDHEIGHT - i
                break
        return stack_height

    def getReward(self):
        stack_height = None
        num_blocks = 0
        for i in range(0, BOARDHEIGHT):
            blank_row = True
            for j in range(0, BOARDWIDTH):
                if self.board[j][i] != '.':
                    num_blocks += 1
                    blank_row = False
            if not blank_row and stack_height is None:
                stack_height = BOARDHEIGHT - i

        if stack_height is None:
            return BOARDHEIGHT
        else:
            return BOARDHEIGHT - stack_height
            return float(num_blocks) / float(stack_height * BOARDWIDTH)

    def isGameOver(self):
        return self.fallingPiece == None and not self.isValidPosition()

    def makeTextObjs(self, text, font, color):
        surf = font.render(text, True, color)
        return surf, surf.get_rect()

    def calculateLevelAndFallFreq(self):
        # Based on the self.score, return the self.level the player is on and
        # how many seconds pass until a falling piece falls one space.
        self.level = min(int(self.lines / 10) + 1, 10)
        self.fallFreq = 0.27 - (self.level * 0.02)
        return self.level, self.fallFreq

    def getNewPiece(self):
        # return a random new piece in a random rotation and color
        shape = self.random.choice(list(PIECES.keys()))
        newPiece = {'shape': shape,
                    'rotation': self.random.randint(0, len(PIECES[shape]) - 1),
                    'x': int(BOARDWIDTH / 2) - int(TEMPLATEWIDTH / 2),
                    'y': 0,  # start it above the self.board (i.e. less than 0)
                    'color': self.random.randint(0, len(COLORS) - 1)}
        return newPiece

    def addToBoard(self):
        # fill in the self.board based on piece's location, shape, and rotation
        for x in range(TEMPLATEWIDTH):
            for y in range(TEMPLATEHEIGHT):
                if PIECES[self.fallingPiece['shape']][self.fallingPiece['rotation']][y][x] != BLANK:
                    self.board[x + self.fallingPiece['x']][y + self.fallingPiece['y']] = self.fallingPiece['color']

    def getBlankBoard(self):
        # create and return a new blank self.board data structure
        self.board = [[BLANK for _ in range(BOARDHEIGHT)]for _ in range(BOARDWIDTH)]
        return self.board

    def isOnBoard(self, x, y):
        return x >= 0 and x < BOARDWIDTH and y < BOARDHEIGHT

    def isValidPosition(self, adjX=0, adjY=0):
        # Return True if the piece is within the self.board and not colliding
        for x in range(TEMPLATEWIDTH):
            for y in range(TEMPLATEHEIGHT):
                isAboveBoard = y + self.fallingPiece['y'] + adjY < 0
                if isAboveBoard or PIECES[self.fallingPiece['shape']][self.fallingPiece['rotation']][y][x] == BLANK:
                    continue
                if not self.isOnBoard(x + self.fallingPiece['x'] + adjX, y + self.fallingPiece['y'] + adjY):
                    return False
                if self.board[x + self.fallingPiece['x'] + adjX][y + self.fallingPiece['y'] + adjY] != BLANK:
                    return False
        return True

    def isCompleteLine(self, y):
        # Return True if the line filled with boxes with no gaps.
        for x in range(BOARDWIDTH):
            if self.board[x][y] == BLANK:
                return False
        return True

    def removeCompleteLines(self):
        # Remove any completed lines on the self.board, move everything above them down, and return the number of complete lines.
        numLinesRemoved = 0
        y = BOARDHEIGHT - 1  # start y at the bottom of the self.board
        while y >= 0:
            if self.isCompleteLine(y):
                # Remove the line and pull boxes down by one line.
                for pullDownY in range(y, 0, -1):
                    for x in range(BOARDWIDTH):
                        self.board[x][pullDownY] = self.board[x][pullDownY - 1]
                # Set very top line to blank.
                for x in range(BOARDWIDTH):
                    self.board[x][0] = BLANK
                numLinesRemoved += 1
                # Note on the next iteration of the loop, y is the same.
                # This is so that if the line that was pulled down is also
                # complete, it will be removed.
            else:
                y -= 1  # move on to check next row up
        return numLinesRemoved

    def drawBoard(self, image):
        # draw the border around the self.board
        image[0:5] = BORDERCOLOR
        image[(BOARDWIDTH * BOXSIZE) + 5:(BOARDWIDTH * BOXSIZE) + 10] = BORDERCOLOR
        image[:, 0:5] = BORDERCOLOR
        image[:, (BOARDHEIGHT * BOXSIZE) + 5:(BOARDHEIGHT * BOXSIZE) + 10] = BORDERCOLOR
        for x in range(BOARDWIDTH):
            for y in range(BOARDHEIGHT):
                color = self.board[x][y]
                if color == BLANK:
                    continue
                image[5 + x * BOXSIZE:5 + (x + 1) * BOXSIZE, 5 + y * BOXSIZE:5 + (y + 1) * BOXSIZE] = COLORS[
                    self.board[x][y]]
                image[5 + x * BOXSIZE:2 + (x + 1) * BOXSIZE, 5 + y * BOXSIZE:2 + (y + 1) * BOXSIZE] = LIGHTCOLORS[
                    self.board[x][y]]

    def drawPiece(self, image, piece):
        shapeToDraw = PIECES[piece['shape']][piece['rotation']]
        pixelx, pixely = piece['x'] * BOXSIZE + 5, piece['y'] * BOXSIZE + 5

        # draw each of the boxes that make up the piece
        for x in range(TEMPLATEWIDTH):
            for y in range(TEMPLATEHEIGHT):
                if shapeToDraw[y][x] != BLANK:
                    image[pixelx + x * BOXSIZE:pixelx + (x + 1) * BOXSIZE,
                    pixely + y * BOXSIZE:pixely + (y + 1) * BOXSIZE] = COLORS[piece['color']]
                    image[pixelx + x * BOXSIZE:pixelx + (x + 1) * BOXSIZE - 2,
                    pixely + y * BOXSIZE:pixely + (y + 1) * BOXSIZE - 2] = LIGHTCOLORS[piece['color']]
