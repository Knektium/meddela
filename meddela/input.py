import os
import json

from .message import (
    Node,
    Message,
    Enum,
)

def get_instances_from_dict(data, classname, cwd='', **kwargs):
    for instance_data in data:
        if "file" in instance_data:
            yield from get_instances_from_file(
                cwd + instance_data["file"],
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

def load_messages_from_dict(data):
    messages = {}

    for message in get_instances_from_dict(data, Message):
        messages[message.id] = message
        messages[message.name] = message

    return messages

def load_messages_from_file(message_file):
    messages = {}

    for message in get_instances_from_file(message_file, Message):
        messages[message.id] = message
        messages[message.name] = message

    return messages

def load_nodes_from_dict(data, messages):
    nodes = {}

    for node in get_instances_from_dict(data, Node, messages=messages):
        nodes[node.name] = node

    return nodes

def load_nodes_from_file(node_file, messages):
    nodes = {}

    for node in get_instances_from_file(node_file, Node, messages=messages):
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

def load_config_from_file(config_file, nodes):
    node_instances = []

    with open(config_file) as json_data:
        data = json.load(json_data)

        try:
            for node_config_data in data["nodes"]:
                node = nodes[node_config_data[0]]
                description = node_config_data[2]
                id = int(node_config_data[1], 16)

                node_instances.append((id, description, node))
        except KeyError as error:
            print("{}: The node {} is not defined.".format(config_file, error))

    return node_instances
