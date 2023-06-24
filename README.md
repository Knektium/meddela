Meddela
=======

Meddela is a command line tool for generating code for CAN node configuration,
message routing, serializing and more.

As inputs it takes message and signal definitions in JSON format along with a
Jinja2 template.

The 29-bit CAN message identifier is divided into four parts:

      28       20       12       4    0
    +-+--------+--------+--------+----+
    |-| MSG ID | TO     | FROM   | PR |
    +-+--------+--------+--------+----+

    MSG ID: Message ID (8 bits)
    TO:     ID of recipient node (8 bits)
    FROM:   ID of sender node (8 bits)
    PR:     Priority (4 bits)

The most significant bit is unused.

Installation
------------

Clone this repository:

```sh
git clone https://github.com/Knektium/meddela
```

Then use pip to install it:

```sh
pip install -e meddela

```

Getting Started
---------------

Start by creating some files for the definitions for the messages, signals,
nodes, and network:

*messages.json*:

(The content of this file can be places directly in the `messages` field in the `robot.json` file.)

```json
[
    {
        "id": "0x01",
        "name": "WheelControl",
        "priority": "0xA",
        "signals":  [
            {
                "name": "Speed",
                "size": "0x10",
                "offset": "0x0"
            },
            {
                "name": "Direction",
                "size": "0x2",
                "offset": "0x10",
                "displayType": "Direction"
            }
        ]
    },
    {
        "id": "0x02",
        "name": "WheelStatus",
        "priority": "0x9",
        "signals":  [
            {
                "name": "RevolutionsPerMinute",
                "size": "0x10",
                "offset": "0x0"
            },
            {
                "name": "OvertemperatureShutdown",
                "size": "0x01",
                "offset": "0x10"
            },
            {
                "name": "CurrentLimitation",
                "size": "0x01",
                "offset": "0x11",
                "displayType": "YesNo"
            },
            {
                "name": "Direction",
                "size": "0x02",
                "offset": "0x12",
                "displayType": "Direction"
            }
        ]
    }
]
```

*nodes.json*:

(The content of this file can be places directly in the `nodes` field in the `robot.json` file.)

```json
[
    {
        "name": "Wheel",
        "rx": [
            "WheelControl"
        ],
        "tx":  [
            "WheelStatus"
        ]
    }
]
```

*robot.json*:

```json
{
    "configurator": "Jack",
    "description": "My Robot",
    "nodeInstances": [
        ["Wheel", "0x11", "Right wheel"],
        ["Wheel", "0x12", "Left wheel"]
    ],
    "enums": {
        "Direction": {
            "NONE": "0x0",
            "FORWARD": "0x1",
            "BACKWARD": "0x2"
        }
    },
    "nodes": [
        { "file": "nodes.json" }
    ],
    "messages": [
        { "file": "messages.json" }
    ]
}
```

Now Meddela knows about all the messages, their signals and nodes in the
network. This information can now be used when generating the desired code but
first a template must first be created so add the following content to a new
file called *structs.c.txt*:

```
/* Message struct typedefs */
{% for message in node.all_messages -%}
typedef struct {{ message.name }}_s {
{%- for signal in message.signals %}
    uint{{ signal.get_word_size(8) * 8 }}_t {{ signal.name }};
{%- endfor %}
} {{ message.name }}_t;

{% endfor -%}
```

Run Meddela and provide the file paths and node ID to generate the code:

```sh
python -m meddela render --config=robot.json --id=0x11 --template=structs.c.txt
```

The output can be piped to a file like this:

```sh
python -m meddela render --config=robot.json --id=0x11 --template=structs.c.txt > structs.c
```

Template Context
----------------

The template context has the following values:

    node_id             Node ID (int)
    node                Node object
    MSG_ID_OFFSET       Position of the 8-bit message ID in the 29-bit CAN message ID
    FROM_NODE_ID_OFFSET Position of the 8-bit sender node ID in the 29-bit CAN message ID
    TO_NODE_ID_OFFSET   Position of the 8-bit recipient node ID in the 29-bit CAN message ID

### Node

Attributes:

    rx_messages         List of Message objects being received by the node
    tx_messages         List of Message objects being transmitted by the node
    all_messages        List of Message objects being received or transmitted by the node

### Message

Attributes:

    id                  Node ID
    name                Node name
    priority            Priority (0 - 15, lower has higher priority)
    signals             List of Signal objects that the message contains

Methods:

    get_mask()
        Returns the bit mask for CAN message ID filtering.

    get_id(from_node_id=0, to_node_id=0)
        Returns the full CAN message ID with priority, to, from and message ID.

    get_broadcast_id(from_node_id)
        Short for get_id(from_node_id=from_node_id).

    get_listen_id()
        Short for get_id().

### Signal

Attributes:

    name                Signal name
    offset              The bit offset in the CAN frame
    size                The bit size of the signal
    endianness          'little' or 'big'
    display_type        Data type, used for display purposes

Methods:

    get_word_offset(width)
        Returns the index of the word (of the provided width) the signal's first bit is located in.

    get_word_size(width)
        Returns the number of words (of the provided width) the signal will have bits in.

    get_word_mask(word_offset, width)
        Returns the signal's bit mask for the provided word index and width.

    get_words(width)
        Returns a list of dicts with the folliwing structure:
        {
            'offset': 0,       # The word index
            'bit_offset': 1,   # The bit offset in the word
            'mask': 255        # The signal's bit mask in the word
        }

### Examples:

Get the number of messages the node receives and transmitts:

```
{{ node.all_messages|count }}
```

Get the node ID in hexadecimal:

```
{{ node_id|hex }}
```

Loop through all messages and their signals:

```
{% for message in node.all_messages %}
    typedef struct {{ message.name }}_s {
    {%- for signal in message.signals %}
        {{ signal.get_word_size(8) * 8 }}_t {{ signal.name }};
    {%- endfor %}
    } {{ message.name }}_t;
{% endfor -%}
```

Message File Structure
----------------------

The message file should contain a JSON list of message definitions where each
message has an ID, name, priority, and a list of signals. Each signal should
have a name, size and offset in message data (in bits), and an optional
display type that tells the tools how it should be displayed:

    {
        "id": "0x01",
        "name": "WheelControl",
        "priority": "0xA",
        "signals":  [
            {
                "name": "Speed",
                "size": "0x10",
                "offset": "0x0"
            },
            {
                "name": "Direction",
                "size": "0x2",
                "offset": "0x10",
                "displayType": "Direction"
            }
        ]
    }

Or it could include a file with the same structure (a list of messages):

    { "file": "path/to/messages.json" }

Node File Structure
-------------------

The node file should contain a JSON list of node definitions where each node
has a name, a list of messages it receives, and a list of messages it sends::

    {
        "name": "Wheel",
        "rx": [
            "WheelControl"
        ],
        "tx":  [
            "WheelStatus"
        ]
    }

Or it could include a file with the same structure (a list of nodes):

    { "file": "path/to/nodes.json" }

Config File Structure
---------------------

The config file should contain a JSON object that has metadata about the CAN
network, the actual nodes and their IDs and names. It should have the following structure:

{
    "configurator": "Jack",
    "description": "My Robot",
    "nodes": [
        ["Wheel", "0x11", "Right wheel"],
        ["Wheel", "0x12", "Left wheel"]
    ]
    "enums": {
        "Direction": {
            "NONE": "0x0",
            "FORWARD": "0x1",
            "BACKWARD": "0x2"
        }
    },
    "nodes": [
        // Same as the node file
    ],
    "messages": [
        // Same as the message file
    ]
}
