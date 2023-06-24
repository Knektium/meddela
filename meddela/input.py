import os
import sys
import json

from .message import (
    Node,
    Message,
    Enum,
)

def get_instances_from_dict(data, classname, working_dir='', **kwargs):
    for instance_data in data:
        if "file" in instance_data:
            yield from get_instances_from_file(
                working_dir + instance_data["file"],
                classname,
                **kwargs,
            )
        else:
            yield classname.get_from_json(instance_data, **kwargs)

def get_instances_from_file(filename, classname, **kwargs):
    with open(filename) as json_data:
        data = json.load(json_data)

        yield from get_instances_from_dict(
            data,
            classname,
            os.path.dirname(filename) + "/",
            **kwargs,
        )

def load_messages_from_dict(data, working_dir=''):
    messages = {}

    for message in get_instances_from_dict(
        data,
        Message,
        working_dir=working_dir,
    ):
        messages[message.id] = message
        messages[message.name] = message

    return messages

def load_messages_from_file(message_file, working_dir=''):
    messages = {}

    for message in get_instances_from_file(
        message_file,
        Message,
        working_dir=working_dir,
    ):
        messages[message.id] = message
        messages[message.name] = message

    return messages

def load_nodes_from_dict(data, messages, working_dir=''):
    nodes = {}

    for node in get_instances_from_dict(
        data,
        Node,
        messages=messages,
        working_dir=working_dir,
    ):
        nodes[node.name] = node

    return nodes

def load_nodes_from_file(node_file, messages, working_dir=''):
    nodes = {}

    for node in get_instances_from_file(
        node_file,
        Node,
        messages=messages,
        working_dir=working_dir,
    ):
        nodes[node.name] = node

    return nodes

def load_enums_from_dict(data):
    enums = {}

    for name in data:
        enums[name] = Enum(name, data[name])

    return enums

def load_enums_from_file(enum_file):
    enums = {}

    with open(enum_file) as json_data:
        data = json.load(json_data)

        for name in data:
            enums[name] = Enum(name, data[name])

    return enums

def load_config_from_file(config_file):
    node_instances = []
    nodes = {}
    messages = {}
    enums = {}

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

        messages = load_messages_from_dict(
            data["messages"],
            working_dir=os.path.dirname(config_file) + "/",
        )
        nodes = load_nodes_from_dict(
            data["nodes"],
            working_dir=os.path.dirname(config_file) + "/",
            messages=messages,
        )
        enums = load_enums_from_dict(enums)

        for node_instance in data["nodeInstances"]:
            try:
                node = nodes[node_instance[0]]
                description = node_instance[2]
                id = int(node_instance[1], 16)

                node_instances.append((id, description, node))
            except KeyError as error:
                print("{}: The node {} is not defined.".format(config_file, error), file=sys.stderr)
                sys.exit(1)

    return (node_instances, nodes, messages, enums)
