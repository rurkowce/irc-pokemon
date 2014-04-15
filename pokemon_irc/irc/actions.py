from pokemon_irc.models import orm
from pokemon_irc.models.orm import session
from pokemon_irc.game import events
from pokemon_irc.exceptions.event import EventError
from pokemon_irc.text import TextManager
from collections import deque, namedtuple
from datetime import datetime
import logging

tm = TextManager('action_responses')


class GMActions:

    def __init__(self, GMBot):
        self.no_auth_actions = {
            'register': self._register_player,
            'auth': self._auth_player,
        }

        self.public_actions = {
            'help': self._display_help,
        }
        self.public_actions.update(self.no_auth_actions)

        self.main_actions = {
            'challenge': self._challenge_player,
            'accept': self._accept_challenge,
        }

        self.battle_actions = {
            'recall': self._recall_pokemon,
            'summon': self._summon_pokemon,
            'yield': self._yield_battle,
        }

        self.admin_actions = {
            'print': self._print
        }

        self.query_actions = {
            'list': {'pokemons': self._list_pokemons}
        }

        self.query_actions.update(self.main_actions)
        self.query_actions.update(self.public_actions)

        self.main_actions.update(self.public_actions)

        self.gm = GMBot

    def key_error_decorator(func):
        def inner(*args, **kwargs):
            try:
                return (1, func(*args, **kwargs))
            except KeyError:
                # XXX: shit happesn when exception gets thrown deeper,
                # needs a fix
                return (0, tm.get("nocommand"))
            except TypeError as e:
                return (0, str(e))
            except EventError as e:
                return (0, str(e))
        return inner

    @key_error_decorator
    def query_run(self, user, tokens):
        return self._run(user, tokens, self.query_actions)

    @key_error_decorator
    def admin_run(self, user, tokens):
        return self._run(user, tokens, self.admin_actions)

    @key_error_decorator
    def battle_run(self, battle, user, tokens):
        return self._run(user, tokens, self.battle_actions, battle=battle)

    @key_error_decorator
    def main_channel_run(self, user, tokens):
        return self._run(user, tokens, self.main_actions)

    def _run(self, user, tokens, commands, **kwargs):
        state = commands
        while tokens:
            state = state[tokens.popleft()]
            if hasattr(state, '__call__'):
                return state(user, *tokens, **kwargs)
        return tm.get("uhoh")

    ##### Event wrappers

    def _list_pokemons(self, user):
        return '\n'.join(events.list_pokemons(user.auth))

    def _register_player(self, user, password):
        return events.create_player(user.name, password)

    def _auth_player(self, user, password):
        if user.name in self.gm.authorized:
            return tm.get("alreadyauth")
        is_authorized = events.authorize_player(user.name, password)

        if is_authorized:
            logging.debug(user, "authorized")
            self.gm.authorized[user.name] = user.hostname
        return tm.get("okauth")

    def _print(self, user, *message):
        return ' '.join(message)

    def _challenge_player(self, user, challengee):
        if not self.gm.player_on_main(challengee):
            return  tm.get('absent', name=challengee)

        challenger = user.name
        events.challenge_player(challenger, challengee)
        self.gm.start_battle(challenger, challengee)
        #self.gm.write(challengee, tm.get("challenge", name=challender))
        #self.gm.pending_battles[challengee] = user.name

        return tm.get('onchallenge', name=challengee)

    # SUCH BATTLE ACTIONS

    def _recall_pokemon(self, user, pokemon_name, battle):
        pass

    def _summon_pokemon(self, user, pokemon_name, battle):
        pokemon = events.get_pokemon(user.name, pokemon_name)
        self.gm.summon_pokemon(user, battle, pokemon)
        return tm.get('onsummon', pokename=pokemon_name)

    def _yield_battle(self, user, battle):
        pass

    def _display_help(self, user):
        pass

    def _accept_challenge(self, user=None, challenger=None):
        pass


class PokemonActions:
    pass
