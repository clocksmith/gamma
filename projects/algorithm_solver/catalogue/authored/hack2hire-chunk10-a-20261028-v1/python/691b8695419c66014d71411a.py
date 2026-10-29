"""Hack2Hire 691b8695419c66014d71411a (Design ChatBot System, variant 2 of 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class EchoBot:
    def react(self, text, user_messages):
        return text[6:] if text.startswith('/echo ') else None


class ReverseBot:
    def react(self, text, user_messages):
        return text[9:][::-1] if text.startswith('/reverse ') else None


class CountBot:
    def react(self, text, user_messages):
        return str(user_messages) if text == '/count' else None


BOT_TYPES = {'echo': EchoBot, 'reverse': ReverseBot, 'count': CountBot}  # new bot types only extend this table


class Channel:
    def __init__(self):
        self.log = []
        self.bots = []  # (name, bot) in the order added
        self.names = set()
        self.user_messages = 0

    def add_bot(self, name, kind):
        factory = BOT_TYPES.get(kind)
        if factory is None or name in self.names:
            return False
        self.names.add(name)
        self.bots.append((name, factory()))
        return True

    def send(self, user, text):
        self.user_messages += 1
        self.log.append(user + ': ' + text)
        for name, bot in self.bots:
            reply = bot.react(text, self.user_messages)
            if reply is not None:
                self.log.append(name + ': ' + reply)

    def recent(self, k):
        return self.log[max(0, len(self.log) - k):]


class ChatApp:
    def __init__(self):
        self.channels = {}

    def createChannel(self, channelId):
        if channelId in self.channels:
            return False
        self.channels[channelId] = Channel()
        return True

    def addBot(self, channelId, botName, botType):
        channel = self.channels.get(channelId)
        return channel is not None and channel.add_bot(botName, botType)

    def sendMessage(self, channelId, userId, text):
        channel = self.channels.get(channelId)
        if channel is None:
            return False
        channel.send(userId, text)
        return True

    def getRecentMessages(self, channelId, k):
        channel = self.channels.get(channelId)
        return [] if channel is None else channel.recent(k)


def solve(operation_names, argument_lists):
    if operation_names[0] != 'ChatApp' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = ChatApp(*argument_lists[0])
    allowed = {'createChannel', 'addBot', 'sendMessage', 'getRecentMessages'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
