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
git clone https://github.com/CodileAB/meddela
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
    "nodes": [
        ["Wheel", "0x11", "Right wheel"],
        ["Wheel", "0x12", "Left wheel"]
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
python -m meddela --messages=messages.json --nodes=nodes.json --config=robot.json --id=0x11 --template=structs.c.txt
```

The output can be piped to a file like this:

```sh
python -m meddela --messages=messages.json --nodes=nodes.json --config=robot.json --id=0x11 --template=structs.c.txt > structs.c
```

Template Context
----------------

The template context has the following values:

    node_id             Node ID (int)
    node                Node object
    messages            List of Message objects
    MSG_ID_OFFSET       Position of the 8-bit message ID in the 29-bit CAN message ID
    FROM_NODE_ID_OFFSET Position of the 8-bit sender node ID in the 29-bit CAN message ID
    TO_NODE_ID_OFFSET   Position of the 8-bit recipient node ID in the 29-bit CAN message ID

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
