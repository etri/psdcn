import pubsub.server.local

class Publisher(object):
    def __init__(self, server):
        self.server = server

    def publish(self, topic, message):
        self.server.addMessage(topic, message)

class Subscriber(object):
    def __init__(self, server):
        self.server = server
        self.messages = []

    @property
    def messages(self):
        return self._messages

    @messages.setter
    def messages(self, messages):
        self._messages = messages

    def subscribe(self, topic):
        self.server.addSubscription(topic, self)

    def unsubscribe(self, topic):
        self.server.removeSubscription(topic, self)

    def fetch(self, topic=None):# For servers with storage capability
        self.server.request(self, quest=topic)

    def clear(self):
        self.messages = []

    def show(self):
        for message in self.messages:
            print(" ", "Topic", message.topic + ":", message.payload)

PubsubService = pubsub.server.local.PubsubService

