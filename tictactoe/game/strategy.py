"""This module is intended to be usable by itself, with no coupling to Django.
This module provides the API for game play, but leaves state, game control flow,
and everything else up to you (ie, gives you everything you need, but stays out
of your way).

Example usage (and doc-test):

>>> # Starting with moves on the board already (get from database or other)
>>> board = Board(
        {
            0: Square('X'),  # Each spot on the board is a Square instance
            1: Square('O'),
            2: Square('X'),
            4: Square('O'),
            6: Square('O'),
            7: Square('X'),
            8: Square('X'),
        }
    )
>>> board.complete
False
>>> board.best_move('O')
5
>>> board.make_move(5, 'O')
>>> board.complete
True
>>> board.tied
True
>>>
>>> # Starting from an empty board
>>> board = Board()
>>> board.make_move(4, 'X')  # Start in center, if you feel like.
>>> board.available_moves
[0, 1, 2, 3, 5, 6, 7, 8]
"""
from copy import deepcopy
import time


MIN = -1
MAX = 1

class Square(object):
    """Having a square object feels more natural than just a string
    representation of the player, and adds flexiblity."""
    def __init__(self, player=None):
        self.player = player
    
    @property
    def empty(self):
        return self.player is None


class Board(object):
    winning_combos = (
        [0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6],
    )
    
    def __init__(self, squares={}):
        self.squares = squares
        for i in range(9):
            if self.squares.get(i) is None:
                self.squares[i] = Square()
    
    @property
    def available_moves(self):
        """Returns a list of moves that are vacant."""
        return [k for k, v in self.squares.iteritems() if v.empty]
    
    def owned_or_vacant(self, player):
        """Returns a list of moves that are owned by the specified player, or
        are vacant."""
        return self.available_moves + self.get_squares(player)
    
    @property
    def complete(self):
        """Check if there is a winning combo left for either player, and return
        True if the game is a winner or there are no combos left, or False if
        there are moves left or if there is a winner."""
        for player in ('X', 'O'):
            for combo in self.winning_combos:
                combo_available = True
                for pos in combo:
                    if not pos in self.owned_or_vacant(player):
                        combo_available = False
                if combo_available:
                    return self.winner is not None
            return True
    
    @property
    def tied(self):
        return self.complete == True and self.winner is None
    
    @property
    def winner(self):
        """Returns a winner ('X' or 'O'), for the current state of the board, if
        there is one, else returns None."""
        for player in ('X', 'O'):
            positions = self.get_squares(player)
            for combo in self.winning_combos:
                win = True
                for pos in combo:
                    if pos not in positions:
                        win = False
                if win:
                    return player
        return None
    
    def best_move(self, player):
        """Returns the best move for the specified player according to negamax,
        by trying each move, and checking the minimax value of the board after
        the move is made, finding the one which leaves the enemy in the best
        position, and then returning that move. As an obvious speed optimization
        on the first and second move, the board is checked to see if the middle
        is open. That's the best spot to start, and if it's not open on the
        seconde move, 0 is returned (top left is fine)."""
        if len(self.available_moves) > 7 :
            if 4 in self.available_moves:
                return 4
            return 0
        highest = -1e10000
        for move in self.available_moves:
            board = deepcopy(self)
            board.make_move(move, player)
            score = self.negamax(board, player, self.get_enemy(player), MIN,
                                 -1e10000, 1e10000)
            if score > highest:
                highest = score
                best_move = move
        return best_move
    
    def negamax(self, board, o_player, player, mm, alpha, beta):
        """Using recursion, this method checks at each level, making the
        assumption along the way that the enemy of player will pick the best
        move each time as well. This allows us to minimize the risk of losing to
        zero, always choosing a cat's game over a potential loss. Since it takes
        just a hundred milliseconds to check from move 2 on, there is no use in
        creating a complicated heuristic method which guesses the value of the
        board at depth n. Instead we brute force our way to the bottom to find
        all the real possible wins/losses/cat's games.
        
        board: Board instance with current state.
        o_player: The player whom the method is working for (doesn't change).
        player: The current player of the move (changes with each resursion).
        mm: MIN or MAX, depending on whether you want to minimize the enemy's
            moves or maximize them (changes with each recursion).
        alpha: -infinity
        beta: infinity"""
        if board.complete:  # terminal node == game over in tictactoe
            return board.heuristic(o_player)
        if mm == MAX:
            for move in board.available_moves:
                copy = deepcopy(board)
                copy.make_move(move, player)
                alpha = max(alpha, self.negamax(copy, o_player,
                                                self.get_enemy(player), -mm,
                                                alpha, beta))
                # A/B Pruning skips pointless nodes when they're go nowhere.
                if alpha >= beta:
                    return beta
            return alpha
        elif mm == MIN:
            for move in board.available_moves:
                copy = deepcopy(board)
                copy.make_move(move, player)
                beta = min(beta, self.negamax(copy, o_player,
                                              self.get_enemy(player), -mm,
                                              alpha, beta))
                if beta <= alpha:
                    return alpha
            return beta
    
    def heuristic(self, player):
        """Returns the "heuristic value of the board for the specified player,
        calculated by taking the number of moves left on the board +1 (to allow
        for 0 pieces left (earlier wins are better, of course), and multiplying
        that number times -1 (player loses), 1 (player wins), or 0 (game tied).
        If `not game.complete`, an exception will occur (left by design)."""
        if self.winner == player:
            value = 1
        elif self.tied:
            value = 0
        elif self.winner == self.get_enemy(player):
            value = -1
        multiplier = len(self.available_moves) + 1
        return value * multiplier
    
    def get_squares(self, player):
        """Returns all the Squares on self, for the specified player."""
        return [k for k,v in self.squares.iteritems() if v.player == player]
    
    def make_move(self, position, player):
        """Create a Square for the player in the position specified."""
        self.squares[position] = Square(player)
    
    def get_enemy(self, player):
        if player == 'X':
            return 'O'
        return 'X'
