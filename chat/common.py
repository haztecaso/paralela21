#!/usr/bin/env python3

MSG_CODES = {
        -1: 'ERROR',
        0: 'CLOSE',
        1: 'CONNECT',
        2: 'ACKNOWLEDGE',
        3: 'MESSAGE'
        }

CLOSE = { 'code' : 0 }

def encode_error(message, critical=False):
    return {
            'code': -1,
            'message': message,
            'critical': critical
            }

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
