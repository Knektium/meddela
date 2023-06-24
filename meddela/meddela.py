#!/usr/bin/python
import sys
import getopt
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
    load_config_from_file,
)


jinja_env = jinja2.Environment()
jinja_env.filters["hex"] = hex

def main():
    config_file = None
    requested_node = None
    template_argument = None

    node_instances = []

    try:
        opts, args = getopt.getopt(sys.argv[1:],  "", ["config=", "id=", "template="])
    except getopt.GetoptError:
        sys.exit(1)

    for opt, arg in opts:
        if opt == "--config":
            config_file = arg
        elif opt == "--template":
            template_argument = arg
        elif opt == "--id":
            requested_node = int(arg, 16)

    if not config_file:
        print("Missing 'config' argument")
        sys.exit(1)

    if not template_argument:
        print("Missing 'template' argument")
        sys.exit(1)

    if not requested_node:
        print("Missing 'id' argument")
        sys.exit(1)

    node_instances, nodes, messages, enums = load_config_from_file(config_file)
    node_id, description, node = node_instances[requested_node]

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
