from django.conf.urls.defaults import *


urlpatterns = patterns('game.views',
    url(r'^$', 'index', name='index'),
    url(r'^game/$', 'play_game', name='play_game'),
    url(r'^game/move/(?P<position>[0-9a-zA-Z_,\-]+)/$', 'make_move',
        name='make_move'),
    url(r'^games/new/$', 'new_game', name='new_game'),
    url(r'^players/new/$', 'new_player', name='new_player'),
)
