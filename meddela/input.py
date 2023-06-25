import os
import sys
import json

from .message import (
    Node,
    Message,
    Enum,
)

def load_recursive_json(data, working_dir=''):
    new_data = []

    for index, item in enumerate(data):
        if "file" not in item:
            new_data.append(item)
            continue

        filename = item["file"]

        with open(working_dir + filename) as json_data:
            next_data = json.load(json_data)

        new_data += load_recursive_json(
            next_data,
            working_dir=os.path.dirname(filename) + "/",
        )

    return new_data

def create_instances(data, classname, **kwargs):
    for instance_data in data:
        yield classname.get_from_json(instance_data, **kwargs)

def load_messages_from_dict(data):
    messages = {}

    for message in create_instances(data, Message):
        messages[message.id] = message
        messages[message.name] = message

    return messages

def load_nodes_from_dict(data, messages):
    nodes = {}

    for node in create_instances(data, Node, messages=messages):
        nodes[node.name] = node

    return nodes

def load_enums_from_dict(data):
    enums = {}

    for name in data:
        enums[name] = Enum(name, data[name])

    return enums

def load_config_from_file(config_file):
    try:
        with open(config_file) as json_data:
            data = json.load(json_data)

        if "nodeInstances" not in data:
            print("The config file must contain a 'nodeInstances' field.", file=sys.stderr)
            sys.exit(1)

        if "nodes" not in data:
            print("The config file must contain a 'nodes' field.", file=sys.stderr)
            sys.exit(1)

        if "messages" not in data:
            print("The config file must contain a 'messages' field.", file=sys.stderr)
            sys.exit(1)

        if "enums" not in data:
            print("The config file must contain an 'enums' field.", file=sys.stderr)
            sys.exit(1)

        recursive_messages = load_recursive_json(
            data["messages"],
            working_dir=os.path.dirname(config_file) + "/",
        )
        data["messages"] = recursive_messages

        recursive_nodes = load_recursive_json(
            data["nodes"],
            working_dir=os.path.dirname(config_file) + "/",
        )
        data["nodes"] = recursive_nodes

        return data
    except json.decoder.JSONDecodeError as error:
        print("Error while reading file: {}".format(error), file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("The config file could not be found", file=sys.stderr)
        sys.exit(1)

def create_instances_from_config(config):
    node_instances = {}

    messages = load_messages_from_dict(
        config["messages"],
    )
    nodes = load_nodes_from_dict(
        config["nodes"],
        messages=messages,
    )
    enums = load_enums_from_dict(config["enums"])

    for node_id in config["nodeInstances"]:
        data = config["nodeInstances"][node_id]

        try:
            id = int(node_id, 16)
            node_type = data["type"]
            node_name = data["name"]
            node = nodes[node_type]

            node_instances[id] = (id, node_type, node)
            node_instances[node_name] = (id, node_type, node)
        except KeyError:
            print("The node {} is not defined.".format(node_type), file=sys.stderr)
            sys.exit(1)

    return (node_instances, nodes, messages, enums)
