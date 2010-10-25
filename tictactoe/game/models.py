from django.db import models
from django.core.exceptions import ValidationError
from tictactoe.game.strategy import Board, Square


class Player(models.Model):
    """Use of the Player model leaves this app flexible, as well as provides the
    ability to track statistics, such as number of wins, etc."""
    name = models.CharField(max_length=100, unique=True)
    
    def __unicode__(self):
        return u'Player: {0}'.format(self.name)
    
    def make_move(self, game, position):
        return Move.objects.create(game=game, player=self, position=position)
    
    @property
    def number_of_wins(self):
        return self.games.filter(winner=self).count()
    
    @property
    def number_of_losses(self):
        """Uses Django's Q objet to negate game.winner = self in the lookup."""
        return self.games.filter(winner__isnull=False).filter(
            ~models.Q(winner=self)).count()
    
    @property
    def number_of_cats_games(self):
        """Returns the number of games for self, in which winner is null."""
        return self.games.filter(complete=True).filter(
            winner__isnull=True).count()


class Game(models.Model):
    players = models.ManyToManyField('game.Player', related_name='games')
    complete = models.BooleanField(default=False)
    winner = models.ForeignKey('game.Player', blank=True, null=True)
    datetime = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return u'Game created on {0}'.format(self.datetime)
    
    def squares(self, player, computer):
        """Returns a set of Square instances for use in a strategy.Board
        instance (a helper method)."""
        squares = dict([[move.position, Square('X')] for move in
            self.moves.filter(player=player)])
        squares.update(dict([[move.position, Square('O')] for move in
            self.moves.filter(player=computer)]))
        return squares


class Move(models.Model):
    """Positions are marked by integers in rows, counting from left to right,
    beginning with 0. Example:
    
       |   | X 
    -----------
       | O |   
    -----------
       |   |   
    
    "X" resides in position 2, and "O" resides in position 4.
    """
    game = models.ForeignKey('game.Game', related_name='moves')
    player = models.ForeignKey('game.Player', related_name='moves')
    position = models.PositiveIntegerField()
    datetime = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = (('position', 'game'),)
    
    
    def __unicode__(self):
        return u'{0} by {1}'.format(self.position, self.player)
