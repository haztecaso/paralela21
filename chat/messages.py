#!/usr/bin/env python3
from datetime import datetime
import bisect
import json
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

class Message():
    """
    Inmmutable class
    """

    def __init__(self, **kwargs):
        self._data = { 'timestamp': datetime.now() }
        if 'code' in kwargs:
            self._type = code_to_type(kwargs['code'])
            del kwargs['code']
        elif 'type' in kwargs:
            self._type = kwargs['type']
            del kwargs['type']
        elif 'payload' in kwargs:
            payload = kwargs['payload']
            del kwargs['payload']
            self._type = code_to_type(payload['type_code'])
            del payload['type_code']
            timestamp = payload['timestamp']
            if type(timestamp) is str:
                timestamp = datetime.strptime(timestamp, DATETIME_FORMAT)
            self._data['timestamp'] = timestamp
            del payload['timestamp']
            self._payload_hash = payload['hash']
            del payload['hash']
            for key in payload:
                kwargs[key] = payload[key]
        else:
            raise ValueError
        for key in self.type['keys']:
            key_name = key['name']
            if key_name in kwargs:
                assert key['type'] == type(kwargs[key_name]),\
                        f"key {key_name} must be of type {key['type'].__name__}"
                self._data[key_name] = kwargs[key_name]
                del kwargs[key_name]
            elif key['optional']:
                    self._data[key_name] = key['default']
            else:
                raise ValueError(f"Required key missing: {key['name']}")
        error_message = ""
        for key in kwargs:
            error_message+=f"Unknown key: {key}\n"
        if error_message:
            ValueError(error_message[0:-1])
        self._data['hash'] = hash(self)

    @property
    def type(self):
        return self._type

    @property
    def data(self):
        return self._data.copy()

    def get(self, key):
        return self.data[key]

    @property
    def timestamp(self):
        return self.get('timestamp')

    def encode(self):
        payload = {}
        payload['type_code'] = self.type['code']
        for key in self._data:
            data = self._data[key]
            if type(data) is datetime:
                data = datetime.strftime(data, format=DATETIME_FORMAT)
            elif type(data) is MessageHistory:
                data = data.encode()
            payload[key] = data
        return payload

    def __lt__(self, other):
        return self.timestamp < other.timestamp

    def __str__(self):
        result = f"type: {self.type['name']}\n"
        for key, data in self.data.items():
            result += f"{key}: {data}\n"
        return result[0:-1]

    def __repr__(self):
        return f"«type {self.type['code']}, hash {hash(self)}»"

    def __hash__(self):
        if 'hash' in self.data:
            result = self.data['hash']
        else:
            result = self.type['code']
            for key in self.data:
                if key != 'hash':
                    result = abs(hash((result, self.data[key])))
        return result


class MessageHistory():
    def __init__(self, **args):
        self.manager = args.get('manager', None)
        messages = args.get('messages', [])
        if self.manager:
            self.messages = self.manager.list(messages) #TODO: sort
        else:
            self.messages = messages #TODO: sort

    def add(self, new_message):
        assert new_message.type != MESSAGE_HISTORY
        bisect.insort(self.messages, new_message)

    def encode(self, _json = True):
        result = []
        for message in self.messages:
            result.append(message.encode())
        if _json:
            return json.dumps(result)
        return result

    def __len__(self):
        return len(self.messages)

    def __str__(self):
        result = ""
        for message in self.messages:
            result += f"{message}\n"
        return result

def decode_history(json_encoded):
    message_list = []
    for payload in json.loads(json_encoded):
        message_list.append(Message(payload = payload))
    return message_list


ERROR = {
        'name' : 'Error',
        'code' : -1,
        'keys' : [
            { 'name': 'message', 'type': str, 'optional': False },
            { 'name': 'critical', 'type': bool, 'optional': True, 'default': False},
            ],
        }

CLOSE = {
        'name' : 'Close',
        'code' : 0,
        'keys' : []
        }

CONNECT = {
        'name' : 'Connect',
        'code' : 1,
        'keys' : [ { 'name': 'username', 'type': str, 'optional': False } ]
        }

ACK = {
        'name' : 'Acknowledge',
        'code' : 2,
        'keys' : []
        }

MESSAGE = {
        'name' : 'Message',
        'code' : 3,
        'keys' : [
            { 'name': 'message', 'type': str, 'optional': False },
            { 'name': 'username', 'type': str, 'optional': False },
            ]
        }

MESSAGE_HISTORY = {
        'name' : 'MessageHistory',
        'code' : 4,
        'keys' : [ { 'name': 'history', 'type': MessageHistory, 'optional': False }, ]
        }

MESSAGE_TYPES = [ERROR, CLOSE, CONNECT, ACK, MESSAGE, MESSAGE_HISTORY]

def code_to_type(code):
    for TYPE in MESSAGE_TYPES:
        if TYPE['code'] == code:
            return TYPE

