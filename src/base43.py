#!/usr/bin/env python

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ$*+-./:"

def divmod43(digits, start_at):
    remainder = 0
    i = start_at
    while i < len(digits):
        digit256 = digits[i]
        temp = remainder * 256 + digit256

        digits[i] = temp / 43
        remainder = temp % 43

        i += 1

    return (remainder, digits)

def encode(data):
    if len(data) == 0:
        return ""

    digits = []
    for byte in data:
        digits.append(ord(byte))

    zero_count = 0
    while zero_count < len(digits) and digits[zero_count] == 0:
        zero_count += 1

    temp_length = len(digits) * 2
    temp = [0] * temp_length
    j = temp_length

    start_at = zero_count
    while start_at < len(digits):
        (mod, digits) = divmod43(digits, start_at)
        if digits[start_at] == 0:
            start_at += 1
        j -= 1
        temp[j] = ALPHABET[mod]

    while j < temp_length and temp[j] == ALPHABET[0]:
        j += 1

    while (zero_count > 0):
        zero_count -= 1
        j -= 1
        temp[j] = ALPHABET[0]

    return ''.join(temp[j:temp_length])
