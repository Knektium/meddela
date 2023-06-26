#!/usr/bin/python
import sys
import getopt
import json
import gzip
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
    create_instances_from_config,
)
from .hash import (
    get_hash,
    to_base36,
)

jinja_env = jinja2.Environment()
jinja_env.filters["hex"] = hex

def print_usage_and_exit():
    print("Usage: ", sys.argv[0], "[compress --config=CONFIG_FILE] [render --config=CONFIG_FILE --id=NODE_ID --template=TEMPLATE_FILE]")
    sys.exit(1)

def compress(config_file):
    config = load_config_from_file(config_file)
    node_instances, nodes, messages, enums = create_instances_from_config(config)

    hash = 0

    for message in config["messages"]:
        hash = hash ^ messages[message["name"]].hash

    for node_id in config["nodeInstances"]:
        id, node_type, node = node_instances[int(node_id, 16)]
        node_name = config["nodeInstances"][node_id]["name"]

        hash = hash ^ node.get_hash(node_id, node_name)

    for enum in enums:
        hash = hash ^ enums[enum].hash

    hash_str = to_base36(hash)

    json_string = json.dumps(config).encode()
    filename = hash_str + '.json.gz'

    with gzip.open(filename, 'wb') as file:
        file.write(json_string)

    print("Created compressed network description file ´{}´". format(filename))

def render(config_file, template_file, requested_node):
    config = load_config_from_file(config_file)
    node_instances, nodes, messages, enums = create_instances_from_config(config)
    node_id, node_name, node = node_instances[requested_node]

    try:
        with open(template_file) as file:
            template = jinja_env.from_string(file.read())
            rendered = template.render(
                node_id=node_id,
                node=node,
                MSG_ID_SIZE=MSG_ID_SIZE,
                MSG_ID_OFFSET=MSG_ID_OFFSET,
                NODE_ID_SIZE=NODE_ID_SIZE,
                FROM_NODE_ID_OFFSET=FROM_NODE_ID_OFFSET,
                TO_NODE_ID_OFFSET=TO_NODE_ID_OFFSET,
            )

            print(rendered)
    except FileNotFoundError:
        print("The template file could not be found", file=sys.stderr)
        sys.exit(1)

def main():
    config_file = None
    requested_node = None
    template_file = None
    command = None

    if len(sys.argv) < 2:
        print_usage_and_exit()

    command = sys.argv[1]

    if command not in ["render", "compress"]:
        print_usage_and_exit()

    try:
        opts, args = getopt.getopt(sys.argv[2:],  "", ["config=", "id=", "template="])
    except getopt.GetoptError:
        print_usage_and_exit()

    for opt, arg in opts:
        if opt == "--config":
            config_file = arg
        elif opt == "--template":
            template_file = arg
        elif opt == "--id":
            requested_node = int(arg, 16)

    if not config_file:
        print("Missing the 'config' argument", file=sys.stderr)
        print_usage_and_exit()

    if command == "compress":
        compress(config_file)
        sys.exit()

    if not template_file:
        print("Missing the 'template' argument", file=sys.stderr)
        print_usage_and_exit()

    if not requested_node:
        print("Missing the 'id' argument", file=sys.stderr)
        print_usage_and_exit()

    render(config_file, template_file, requested_node)
