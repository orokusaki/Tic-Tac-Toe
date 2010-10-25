from django.forms.models import ModelForm
from tictactoe.game.models import Player


class PlayerForm(ModelForm):
    class Meta:
        model = Player
