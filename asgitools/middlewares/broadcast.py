import asyncio
import asyncio_redis
import collections
import json


class PubSubChannel(object):
    def __init__(self, pub, sub):
        self._pub = pub
        self._sub = sub
        # Keep a mapping from group -> set(channel names)
        self._subscribers = collections.defaultdict(set)

    async def send(self, message):
        group = message['group']
        if 'add' in message:
            if not self._subscribers[group]:
                await self._sub.subscribe([group])
            self._subscribers[group] |= set([message['add']])
        if 'discard' in message:
            self._subscribers[group] -= set([message['discard']])
            if not self._subscribers[group]:
                await self._sub.unsubscribe([group])
        if 'send' in message:
            text = json.dumps(message['send'])
            await self._pub.publish(group, text)


async def listener(sub, subscribers, clients):
    loop = asyncio.get_event_loop()
    while True:
        reply = await sub.next_published()
        message = json.loads(reply.value)
        for channel_name in subscribers[reply.channel]:
            print(channel_name)
            loop.create_task(clients[channel_name].send(message))


class BroadcastMiddleware:

    def __init__(self, asgi_instance, scope, host='localhost', port=6379):
        self.asgi_instance = asgi_instance
        self.scope = scope
        self.host = host
        self.port = port
        self.clients = {}
        self.pubsub = None

    async def __call__(self, message):
        if self.pubsub is None:
            pub = await asyncio_redis.Connection.create(self.host, self.port)
            sub = await asyncio_redis.Connection.create(self.host, self.port)
            sub = await sub.start_subscribe()
            self.pubsub = PubSubChannel(pub, sub)
            loop = asyncio.get_event_loop()
            loop.create_task(listener(sub, self.pubsub._subscribers, self.clients))
            self.asgi_instance.groups = self.pubsub

        try:
            client_id = self.asgi_instance.id
        except AttributeError:
            client_id = 'asgi_ws:%d' % id(self.asgi_instance)
            self.asgi_instance.id = client_id

        if message['type'] == 'websocket.accept':
            self.clients[client_id] = self.asgi_instance
        elif message['type'] == 'websocket.disconnect':
            self.clients.pop(client_id)
        return