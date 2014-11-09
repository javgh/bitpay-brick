#!/usr/bin/env python

from os.path import expanduser, isfile

API_KEY_FILE = '.bitpay-brick-api-key'

def read_api_key():
    api_key_file = expanduser('~') + '/' + API_KEY_FILE
    if not isfile(api_key_file):
        return None
    with open(api_key_file, 'r') as f:
        api_key = f.read()
    return api_key.strip()
