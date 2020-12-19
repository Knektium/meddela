#!/usr/bin/python3 -u
import sys
import getopt
import json
from sys import stdout
from time import sleep
from random import getrandbits, randrange

from meddela import Message


def hexstr(integer, chars=2):
    return ('{:0' + str(chars) + 'X}').format(integer)

def print_usage_and_exit():
    print("Usage: ", sys.argv[0], " --messages=MESSAGE_FILE")
    sys.exit(1)

message_file = None
messages = []

try:
    opts, args = getopt.getopt(sys.argv[1:],  "", ["messages="])
except getopt.GetoptError:
    sys.exit(1)

for opt, arg in opts:
    if opt == "--messages":
        message_file = arg

if not message_file:
    print("Missing 'messages' argument")
    print_usage_and_exit()

with open(message_file) as json_data:
    data = json.load(json_data)

    for message_data in data:
        messages.append(Message.get_message_from_json(message_data))

while True:
	msg = messages[randrange(0, len(messages))]
	msg_id = msg.get_id()
	msg_data = 0

	for s in msg.signals:
		conf = next(s.get_words(64))
		msg_data |= (getrandbits(s.size) << conf['bit_offset']) & conf['mask']

	i = 8
	hexdata = ''
	while i > 0:
		hexdata += hexstr(msg_data & 0xFF, 2)
		msg_data = msg_data >> 8
		i -= 1

	i = 4
	hexid = ''
	while i > 0:
		hexid += hexstr(msg_id & 0xFF, 2)
		msg_id = msg_id >> 8
		i -= 1

	stdout.write(hexid + hexdata + "A5\n")
	sleep(0.2)
