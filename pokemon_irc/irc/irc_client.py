import irc.bot
import irc.strings
import logging
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr
from pokemon_irc.settings import IRC_SERVER, IRC_PORT, IRC_MAIN_CHANNEL, IRC_GM_NICK, IRC_REALNAME, IRC_OWNER
from .actions import GMActions
from collections import deque, defaultdict, namedtuple

user = namedtuple('user', ['name', 'real_name', 'hostname'])
user_auth = namedtuple('auth', ['hostname', 'player'])


class BotBase(irc.bot.SingleServerIRCBot):
    def parse_source(self, source):
        t = str.maketrans('!@', '  ')
        u = user(*source.translate(t).split())
        logging.debug(u)
        return u

    def ircify(self, nickname):
        """ turn into valid irc nickname """
        pass

    def tokenize_command(self, message, name=None, query=False):
        if not name: name = self.name
        command = None

        if message.startswith(name+':'):
            command = message[len(name)+1:].strip()
        elif query:
            command = message.strip()

        if command:
            logging.debug(command)
            tokens = deque(command.split())
            return tokens
        return False


class PokemonBot(BotBase):
    def __init__(self, pokemon, battle, server=IRC_SERVER, port=IRC_PORT):

        self.name = self.ircify(pokemon.name)
        realname = pokemon.base_pokemon.name
        self.channel = ircify(battle.name)

        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], self.name, realname)
        self.channel = channel

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_privmsg(self, c, e):
        pass

    def on_pubmsg(self, c, e):
        pass


class GMBot(BotBase):
    authorized = {}
    pending_battles = defaultdict(dict)
    current_battles = set()

    def __init__(
        self,
        channel=IRC_MAIN_CHANNEL,
        nickname=IRC_GM_NICK,
        realname=IRC_REALNAME,
        server=IRC_SERVER,
        port=6667,
        bot_list=None
        ):

            self.name = nickname

            if not bot_list:
                bot_list = []

            self.bot_list = bot_list

            irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, realname)
            self.channel = channel
            self.actions = GMActions(self)

            self.connection.add_global_handler("part", self.on_exit, -42)
            self.connection.add_global_handler("quit", self.on_exit, -42)
            self.connection.add_global_handler("nick", self.move_auth, -42)
            self.connection.add_global_handler("welcome", self.clear_auth, 1)

    def clear_auth(self, c, e):
        self.authorized = {}

    def get_auth(self, nick, hostname):
        if user.name not in self.authorized:
            return False

        if user.hostname == self.authorized[user.name].hostname:
            return self.authorized[user.name]

    def move_auth(self, c, e):
        user = self.parse_source(c.source)
        player = self.get_auth(user.name, user.hostname)

        if player:
            self.authorized[e.target] = player
            del self.authorized[user.name]

    def auth(self, user, player):
        logging.debug(user, "authorized")
        self.gm.authorized[user.name] = user_auth(user.hostname, player)

    def deauth(self, user):
        logging.debug(user, "deauthorized")
        auth = self.get_auth(user.name, user.hostname)
        if not auth:
            return

        del self.authorized[user.name]

    def on_exit(self, c, e):
        user = self.parse_source(c.source)

        if e.type == 'quit':
            self.deauth(user)

        elif e.target == IRC_MAIN_CHANNEL:  # parts from main channel
            self.deauth(user)

    def on_nicknameinuse(self, c, e):
        raise Exception("get me a real name!")

    def on_welcome(self, c, e):
        c.join(self.channel)

    # TODO: refactoring this with on_pubmsg would be cool
    def on_privmsg(self, c, e):

        user = self.parse_source(e.source)
        tokens = self.tokenize_command(e.arguments[0], query=True)

        if not tokens:
            return

        hostname = self.authorized.get(user.name, False)
        player = user.hostname == self.hostname

        if player and tokens[0] in self.actions.no_auth_actions:
            self.write(user.name, "already authorized")
            return

        if not player and tokens[0] not in self.actions.public_actions:
            self.write(user.name, "Not authorized")
            return

        message = self.actions.query_run(user, tokens)
        self.write(user.name, message)

    def on_pubmsg(self, c, e):
        user = self.parse_source(e.source)
        tokens = self.tokenize_command(e.arguments[0])

        if not tokens:
            return

        player = self.authorized.get((user.name, user.hostname), False)

        if player and tokens[0] in self.actions.no_auth_actions:
            self.respond(user.name, e.target, "already authorized")
            return

        if not player and tokens[0] not in self.actions.public_actions:
            self.respond(user.name, e.target, "not authorized")
            return

        if e.target == IRC_MAIN_CHANNEL:
            message = self.actions.main_channel_run(user, tokens)
        else:
            message = self.actions.battle_run(user, tokens)

        self.respond(user.name, e.target, message)

    def _run(self, command, channel=None):
        # pointless, probably bad, but i found it interesting

        user = user(name="admin", hostname="127.0.0.1", realname="admin")
        tokens = deque(command.split())
        if not channel:
            message = self.actions.admin_run(user, tokens)

        elif channel == IRC_MAIN_CHANNEL:
            message = self.actions.main_channel_run(name, tokens)

        else:
            message = self.actions.battle_run(name, tokens)

        self.write(channel, message)

    def write(self, channel, message):
        """ send message to a channel(username) """
        for line in message.split('\n'):
            print("#%s %s: %s" % (channel, IRC_GM_NICK, line))
            self.connection.privmsg(channel, line)

    def respond(self, nick, channel, message):
        """ send message to a channel, prefixed with nick: """
        print("#%s %s: %s" % (channel, nick, message))
        self.connection.privmsg(channel, "%s: %s" % (nick, message))

    def create_pokemon(self, user, battle, pokemon):
        """ Deploys a PokeBot on IRC"""
        id = pokemon.id
        player = pokemon.player

        p = PokeBot(
        channel=settings.IRC_MAIN_CHANNEL,
        nickname='%s[%s]' % (pokemon_name, player)
        )
        p._connect()
        bot_list[id] = p


    def start_battle(self, player1, player2):
        pass
