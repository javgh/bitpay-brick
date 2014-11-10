#!/usr/bin/env python

import sys

import base43

if len(sys.argv) < 2:
    print "Usage: %s <file>" % sys.argv[0]
    sys.exit(1)

with open(sys.argv[1], 'r') as f:
    data = f.read()
    enc = base43.encode(data)
    remaining = len(enc)
    while remaining > 80:
        print "\"%s\" \\" % enc[0:80]
        enc = enc[81:]
        remaining = len(enc)
