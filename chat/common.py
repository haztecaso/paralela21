#!/usr/bin/env python3

def encode_error(message, critical=False):
    return {
            'code': -1,
            'message': message,
            'critical': critical
            }

def decode_error(payload):
    assert payload['code'] == -1
    message = str(payload['message'])
    critical = bool(payload['critical'])
    return (message, critical)

def decode_close(payload):
    assert payload['code'] == 0
    return payload['username']

def encode_connect(username):
    return {
            'code' : 1,
            'username' : username
            }

ACK = { 'code': 2 }

def decode_connect(payload):
    assert payload['code'] == 1
    return payload['username']

def encode_message(timestamp, message, username=None):
    return {
            'code' : 3,
            'timestamp' : timestamp,
            'message' : message,
            'username' : username
            }

def decode_message(payload):
    assert payload['code'] == 3
    timestamp = payload['timestamp']
    message = str(payload['message'])
    username = str(payload['username'])
    return (timestamp, message, username)


# IDEA DE CLASE PARA LOS MENSAJES

# ERROR = {
#         'code' : -1,
#         'keys' : ['message', 'critical']
#         }

# CLOSE = {
#         'code' : 0,
#         'keys' : []
#         }

# CONNECT = {
#         'code' : 1,
#         'keys' : ['username']
#         } 

# ACK = {
#         'code' : 2,
#         'keys' : []
#         }

# MESSAGE = {
#         'code' : 3,
#         'keys' : ['message', 'timestamp', 'username']
#         }


# def code_to_type(code):
#     if code == -1:
#         return ERROR
#     elif code == 0:
#         return CLOSE
#     elif code == 1:
#         return CONNECT
#     elif code == 2:
#         return ACK
#     elif code == 3:
#         return MESSAGE

# class Message():
#     def __init__(self, **kwargs):
#         if 'code' in kwargs:
#             self.type = code_to_type(kwargs['code'])
#             del kwargs['code']
#         elif 'message_type' in kwargs:
#             self.type = kwargs['message_type']
#             del kwargs['message_type']
#         else:
#             raise ValueError
#         self.data = {}
#         self.set_data(kwargs)

#     def set_data(self, data):
#         for key in self.type['keys']:
#             if key in data:
#                 self.data[key] = data[key]
#                 del data[key]
#             else:
#                 raise ValueError(f"Required key missing: {key}")
#         for key in data:
#             raise ValueError(f"Unknown key: {key}")

#     def encode(self):
#         payload = {}
#         payload['code'] = self.type['code']
#         for key in self.data:
#             payload[key] = self.data[key]
#         return payload 
