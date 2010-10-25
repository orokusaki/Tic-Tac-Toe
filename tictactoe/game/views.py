from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError
from django.db.transaction import commit_on_success
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext, Template
from django.contrib import messages
from tictactoe.game.models import Game, Player
from tictactoe.game.forms import PlayerForm
from tictactoe.game.strategy import Board


def index(request):
    return redirect('play_game')


def play_game(request):
    """Gets the current game pieces from request.game, request.computer, and
    request.player (see game.middleware for upstream logic where the attributes
    are being set), and displays the game using game.html."""
    all_positions = range(9)
    plr_positions = [move.position for move in request.game.moves.filter(
        player=request.player)]
    com_positions = [move.position for move in request.game.moves.filter(
        player=request.computer)]
    avl_positions = [p for p in all_positions if p not in com_positions and p
                     not in plr_positions]
    data = {
        'all_positions': all_positions,
        'plr_positions': plr_positions,
        'com_positions': com_positions,
        'avl_positions': avl_positions,
    }
    return render_to_response('game.html', RequestContext(request, data))


@commit_on_success
def make_move(request, position):
    """This view accepts an integer position argument for the move the player
    would like to make. It then builds up a game.strategy.Board (Board) form the
    current state (for access to tictactoe logic (e.g. board.best_move('X'),
    board.winner, etc). After making your move, first the game checks that you
    aren't the winner (which... you're not :), rebuilds the Board and checks for
    the best next move, and makes that move with the computer. If any move is a
    game ending one, it redirects to new_game after adding a message to the
    request letting the player know what happened."""
    game = request.game
    try:
        board = Board(game.squares(request.player, request.computer))
        if board.complete:
            return redirect('new_game')
        request.player.make_move(game=game, position=position)
        board = Board(game.squares(request.player, request.computer))
        if board.complete:  # Game over
            if not board.tied:
                winner = board.winner
                if winner == 'X':  # Player wins (not possible, so useless :)
                    game.complete = True
                    game.winner = request.player
                    game.save()
                    messages.success(request, 'Ok {0}, You won :O'.format(
                        request.player.name))
            else:
                messages.warning(request, 'Cat\'s game :)'.format(
                    request.player.name))
            return redirect('new_game')
        best_move = board.best_move('O')
        request.computer.make_move(game=game, position=best_move)
        board = Board(game.squares(request.player, request.computer))
        if board.complete:
            if board.tied:
                game.complete = True
                game.save()
                messages.warning(request, 'Cat\'s game :)'.format(
                    request.player.name))
                return redirect('play_game')
            else:
                game.complete = True
                game.winner = request.computer
                game.save()
                if request.player.number_of_losses % 4 == 0:
                    messages.success(
                        request, 'One of these days, if you try hard enough :)')
                if request.player.number_of_losses % 9 == 0:
                    messages.success(request, 'Ok, you should just give up :)')
                messages.error(
                    request, 'You lost, {0} :('.format(request.player.name))
    except IntegrityError:
        messages.error(request, 'That move is already taken!')
    return redirect('play_game')


def new_player(request):
    """Creates a new Player, leaving any previous Player to grow dust. It then
    redirects to new_game."""
    if request.method == 'POST':
        form = PlayerForm(request.POST)
        if form.is_valid():
            instance = form.save()
            request.session['player_pk'] = instance.pk
            return redirect('new_game')
    else:
        form = PlayerForm()
    data = {
        'form': form,
    }
    return render_to_response('form.html', RequestContext(request, data))


def new_game(request):
    """Creates a new game, and redirects to play_game."""
    game = Game.objects.create()
    game.players.add(request.player, request.computer)
    request.session['game_pk'] = game.pk
    messages.info(request, 'Good luck, {0} :)'.format(request.player.name))
    return redirect('play_game')
