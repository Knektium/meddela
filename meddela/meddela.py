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

#jinja_env = jinja2.Environment()
#jinja_env.filters["rx"] = 


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

    with open(message_file) as json_data:
        data = json.load(json_data)

        for message_data in data:
            message = Message.get_from_json(message_data)
            messages[message.name] = message

    with open(node_file) as json_data:
        data = json.load(json_data)

        for node_data in data:
            node = Node.get_from_json(node_data, messages)
            nodes[node.name] = node

    with open(config_file) as json_data:
        data = json.load(json_data)

        for node_config_data in data["nodes"]:
            node = nodes[node_config_data[0]]
            description = node_config_data[2]
            id = int(node_config_data[1], 16)

            node_instances.append((id, description, node))

    for node_id, description, node in node_instances:
        if not node_id == requested_node:
            continue

        with open(template_argument) as template_file:
            template = jinja2.Template(template_file.read())
            node_messages = [
                {
                    'type': 'rx',
                    'name': m.name,
                    'id': hex(m.get_listen_id()),
                    'mask': hex(m.get_mask()),
                    'signals': m.signals,
                }
                for m in node.rx_messages
            ] + [
                {
                    'type': 'tx',
                    'name': m.name,
                    'id': hex(m.get_broadcast_id(node_id)),
                    'mask': hex(m.get_mask()),
                    'signals': m.signals,
                }
                for m in node.tx_messages
            ]

            print(template.render(
                node_id=hex(node_id),
                node=node,
                messages=node_messages,
                MSG_ID_SIZE=MSG_ID_SIZE,
                MSG_ID_OFFSET=MSG_ID_OFFSET,
                NODE_ID_SIZE=NODE_ID_SIZE,
                FROM_NODE_ID_OFFSET=FROM_NODE_ID_OFFSET,
                TO_NODE_ID_OFFSET=TO_NODE_ID_OFFSET,
            ))