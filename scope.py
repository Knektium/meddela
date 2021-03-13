#!/usr/bin/python3
import sys
import os
import asyncio
import concurrent
import getopt
import datetime
import json
import serial
import urwid

from meddela import (
    Message,
    Enum,
)


messages = {}
enums = {}
selected_messages = {}
key_mapping = {}
loop = None
serial_port = None

table_body = None
message_details = None

def hexletters(bit_size):
    display_size = bit_size // 4

    if display_size < 1:
        display_size = 1

    return display_size

def hexstr(integer, chars=2, prefix="0x"):
    return (prefix + "{:0" + str(chars) + "X}").format(integer)

def marshal(data_bytes):
    if len(data_bytes) != 13:
        raise ValueError("The length of the data_bytes must be 13.")

    message_id = data_bytes[0]
    message_id += data_bytes[1] << 8
    message_id += data_bytes[2] << 16
    message_id += data_bytes[3] << 24

    data = data_bytes[4:12]

    checksum = data_bytes[10]

    return (message_id, data, checksum)

def to_pdu(message_id, data):
    hexdata = ""
    hexid = ""

    i = 8
    while i > 0:
    	hexdata += hexstr(data & 0xFF, 2, "")
    	data = data >> 8
    	i -= 1

    i = 4
    while i > 0:
    	hexid += hexstr(message_id & 0xFF, 2, "")
    	message_id = message_id >> 8
    	i -= 1

    return bytearray(hexid + hexdata + "A5\n", encoding="ascii")

def get_data():
    data = serial_port.readline(100)
    return (
        data,
        datetime.datetime.now(),
    )

@asyncio.coroutine
def get_byte_async():
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        while True:
            message = yield from loop.run_in_executor(executor, get_data)
            table_body.set_row(message)

def get_and_print():
    yield from get_byte_async()

def get_message_and_data_from_conf(message_conf):
    for message_conf in message_conf:
        message = messages[message_conf['messageName']]

        yield (
            message,
            message.get_data_from_signal_values(message_conf['signalValues'])
        )

def exit_on_q(key):
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()

    key_conf = key_mapping.get(key, None)

    if key_conf:
        for message, data in get_message_and_data_from_conf(key_conf['sendMessages']):
            try:
                serial_port.write(to_pdu(message.get_id(), data))
            except TypeError:
                pass

def update_message_details():
    text = ""

    for message_id in selected_messages:
        message_row = selected_messages[message_id]

        if message_row.message:
            headline = "{} | To: {} From: {}".format(
                message_row.message.name,
                hexstr(message_row.message.get_receiver_from_can_id(message_row.message_id)),
                hexstr(message_row.message.get_sender_from_can_id(message_row.message_id)),
            )
            values = message_row.message.get_signal_values_from_data(message_row.data)
            datatext = ""

            for name in values:
                display_type = ""
                value, signal = values[name]


                try:
                    display_type = signal.display_type
                except AttributeError:
                    pass

                if not display_type:
                    display_type = "Hex"

                if display_type in enums:
                    value = enums[display_type].get_name_from_value(value)
                    if value is None:
                        value = "UNKNOWN"
                else:
                    value = hexstr(value, hexletters(signal.size))

                datatext += name + ": " + value + "\n"
        else:
            headline = hexstr(message_row.message_id, 7)
            datatext = str(message_row.data)

        if text:
            text += "\n"

        text += "{}\n{}\n".format(            
            headline,
            datatext,
        )

    message_details.set_text(text)

def on_message_click(message_row):
    if message_row.message_id in selected_messages:
        del selected_messages[message_row.message_id]
    else:
        selected_messages[message_row.message_id] = message_row

    update_message_details()

class TableRow(urwid.Button):
    def __init__(self, message_id, count, last_received, time_delta, data):
        self.message_id = message_id
        self.count = count
        self.last_received = last_received
        self.data = data
        self.message = None

        id = "0x00"
        sender = "0x00"
        receiver = "0x00"
        name = "-"

        widgets = [
            urwid.Text(hexstr(message_id, 10)),
            urwid.Text(str(count)),
            urwid.Text(str(time_delta)),
        ]

        try:
            self.message = messages[Message.get_id_from_can_id(message_id)]

            name = self.message.name
            id = hexstr(self.message.id, 2)
            sender = hexstr(self.message.get_sender_from_can_id(message_id), 2)
            receiver = hexstr(self.message.get_receiver_from_can_id(message_id), 2)
        except KeyError:
            pass

        text = "{} | {} => {} | {} | {} | {} | {}".format(                
            id,
            sender,
            receiver,
            str(count).rjust(5),
            last_received.strftime("%H:%M:%S"),
            str(time_delta),
            name
        )

        super(TableRow, self).__init__(text)

        self._w = urwid.AttrMap(urwid.SelectableIcon(text, 1),
            None, focus_map='selected')

        urwid.connect_signal(self, 'click', on_message_click)

class TableBody(urwid.ListBox):
    def __init__(self):
        body = urwid.SimpleFocusListWalker([])
        super(TableBody, self).__init__(body)

    def get_row(self, message_id):
        index = 0
        for tr in self.body:
            if tr.message_id == message_id:
                return index

            index += 1

        return None

    def set_row(self, message):
        data, receive_time = message

        try:
            data = data.decode('ascii')
        except (UnicodeDecodeError, AttributeError):
            pass

        data_bytes = bytes.fromhex(data.rstrip())

        try:
            message_id, message_data, checksum = marshal(data_bytes)
        except ValueError:
            return

        row_index = self.get_row(message_id)

        if row_index is None:
            self.body.append(TableRow(
                message_id,
                count=1,
                last_received=receive_time,
                time_delta=datetime.timedelta(),
                data=message_data,
            ))
        else:
            tr = self.body[row_index]
            
            new_tr = TableRow(
                message_id,
                count=tr.count + 1,
                last_received=receive_time,
                time_delta=receive_time - tr.last_received,
                data=message_data,
            )
            self.body[row_index] = new_tr

            if message_id in selected_messages:
                selected_messages[message_id] = new_tr
                update_message_details()

def print_usage_and_exit():
    print("Usage: ", sys.argv[0], " --port=SERIAL_PORT --messages=MESSAGE_FILE")
    sys.exit(1)

def main():
    global loop
    global serial_port
    global table_body
    global message_details
    global key_mapping

    message_file = None
    port_file = None
    enum_file = None

    try:
        opts, args = getopt.getopt(sys.argv[1:],  "", ["messages=", "port=", "enums="])
    except getopt.GetoptError:
        sys.exit(1)

    try:
        with open(os.getcwd() + "/Scopefile") as json_data:
            data = json.load(json_data)
            message_file = data.get('messageFile', None)
            port_file = data.get('serialPort', None)
            enum_file = data.get('enumFile', None)
            key_mapping = data.get('keyMapping', None)
    except json.decoder.JSONDecodeError as error:
        print("Error while reading Scopefile:", error)
        exit(1)
    except FileNotFoundError:
        pass

    for opt, arg in opts:
        if opt == "--messages":
            message_file = arg
        elif opt == "--port":
            port_file = arg
        elif opt == "--enums":
            enum_file = arg

    if not message_file:
        print("Missing 'messages' argument")
        print_usage_and_exit()

    if not port_file:
        print("Missing 'port' argument")
        print_usage_and_exit()

    with open(message_file) as json_data:
        data = json.load(json_data)

        for message_data in data:
            message = Message.get_from_json(message_data)
            messages[message.id] = message
            messages[message.name] = message

    if enum_file:
        with open(enum_file) as json_data:
            data = json.load(json_data)

            for name in data:
                enums[name] = Enum(name, data[name])

    palette = [
        (None, 'light blue', 'white'),
        ('bg', 'light blue', 'white'),
        ('footer', 'light blue', 'white'),
        ('selected', 'white', 'light blue'),
    ]

    if not port_file.startswith("/dev/"):
        serial_port = open(port_file, 'r')
    else:
        serial_port  = serial.Serial(
            port_file,
            baudrate=19200,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_TWO,
            bytesize=serial.EIGHTBITS,
        )

    message_details = urwid.Text("Select a message to show more details.\n")
    table_body = TableBody()
    message_table = urwid.AttrMap(
        urwid.Padding(
            urwid.Frame(
                header=urwid.Text("\nMessages:\n"),
                footer=urwid.AttrMap(message_details, "footer"),
                body=table_body,
            ),
            left=2, right=2
        ),
        "bg",
    )

    loop = asyncio.get_event_loop()
    loop.create_task(get_and_print())
    evl = urwid.AsyncioEventLoop(loop=loop)
    uloop = urwid.MainLoop(message_table, palette=palette, event_loop=evl, unhandled_input=exit_on_q)
    uloop.run()

if __name__ == "__main__":
    main()
