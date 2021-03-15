#!/usr/bin/python
import sys
import getopt
import json
import jinja2

from .message import (
    Signal,
    Node,
    Message,
    NODE_ID_SIZE,
    FROM_NODE_ID_OFFSET,
    TO_NODE_ID_OFFSET,
    MSG_ID_SIZE,
    MSG_ID_OFFSET,
)
from .input import (
    load_messages_from_file,
    load_nodes_from_file,
    load_config_from_file,
)


jinja_env = jinja2.Environment()
jinja_env.filters["hex"] = hex

def main():
    message_file = None
    node_file = None
    config_file = None
    requested_node = None
    template_argument = None

    messages = {}
    nodes = {}
    node_instances = []

    try:
        opts, args = getopt.getopt(sys.argv[1:],  "", ["messages=", "nodes=", "config=", "id=", "template="])
    except getopt.GetoptError:
        sys.exit(1)

    for opt, arg in opts:
        if opt == "--messages":
            message_file = arg
        elif opt == "--nodes":
            node_file = arg
        elif opt == "--config":
            config_file = arg
        elif opt == "--template":
            template_argument = arg
        elif opt == "--id":
            requested_node = int(arg, 16)

    if not message_file:
        print("Missing 'messages' argument")
        sys.exit(1)

    if not node_file:
        print("Missing 'nodes' argument")
        sys.exit(1)

    if not config_file:
        print("Missing 'config' argument")
        sys.exit(1)

    if not template_argument:
        print("Missing 'template' argument")
        sys.exit(1)

    if not requested_node:
        print("Missing 'id' argument")
        sys.exit(1)

    messages = load_messages_from_file(message_file)
    nodes = load_nodes_from_file(node_file, messages=messages)
    node_instances = load_config_from_file(config_file, nodes=nodes)

    for node_id, description, node in node_instances:
        if not node_id == requested_node:
            continue

        with open(template_argument) as template_file:
            template = jinja_env.from_string(template_file.read())

            print(template.render(
                node_id=node_id,
                node=node,
                MSG_ID_SIZE=MSG_ID_SIZE,
                MSG_ID_OFFSET=MSG_ID_OFFSET,
                NODE_ID_SIZE=NODE_ID_SIZE,
                FROM_NODE_ID_OFFSET=FROM_NODE_ID_OFFSET,
                TO_NODE_ID_OFFSET=TO_NODE_ID_OFFSET,
            ))
