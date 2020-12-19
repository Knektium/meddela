Meddela
=======

Meddela is a command line tool for generating code for CAN node configuration,
message routing, serializing and more.

As inputs it takes message and signal definitions in JSON format along with a
jinja2 template.

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

Start by creating some files containing the definitions for the messages,
signals and network.

Create a message file called `messages.json` with the following content:

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

Create another file for the node definitions called `nodes.json` and add the
following content:

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

Meddela needs to know about the actual nodes in the network. Create a new file
called `robot.json` and add the following content:

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

Now Meddela knows about all the messages, their signals and nodes in the network
 This information can now be used when generating the desired code. A template
must first be created so add the following content to a new template file called
`structs.c.txt`:

```
/* Message struct typedefs */
{% for message in messages -%}
typedef struct {{ message.name }}_s {
{%- for signal in message.signals %}
    uint{{ signal.get_word_size(8) * 8 }}_t {{ signal.name }};
{%- endfor %}
} {{ message.name }}_t;

{% endfor -%}
```

Run Meddela and provide the node ID to generate code for:

```sh
python -m meddela --messages=messages.json --nodes=nodes.json --config=robot.json --id=0x11 --template=structs.c.txt
```
