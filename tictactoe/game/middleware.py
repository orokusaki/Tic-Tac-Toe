from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.contrib import messages
from tictactoe.game.models import Player, Game


class PlayersMiddleware(object):
    """Makes a "Computer" player object from the getgo (if one doesn't exist),
    and requires a request.player at all times."""
    def process_request(self, request):
        try:
            request.computer = Player.objects.get(name='Computer')
        except ObjectDoesNotExist:
            request.computer = Player.objects.create(name='Computer')
        if not request.path == reverse('new_player'):
            try:
                request.player = Player.objects.get(
                    pk=request.session.get('player_pk'))
            except ObjectDoesNotExist:
                messages.warning(request, 'First, create a player.')
                return redirect('new_player')


class GameMiddleware(object):
    """Ensures there is a request.game when at any game play URLs."""
    def process_request(self, request):
        if reverse('play_game') in request.path:
            try:
                request.game = Game.objects.filter(complete=False).get(
                    pk=request.session.get('game_pk'))
            except ObjectDoesNotExist:
                return redirect('new_game')
