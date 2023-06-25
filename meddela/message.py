NODE_ID_SIZE = 8
FROM_NODE_ID_OFFSET = 4
TO_NODE_ID_OFFSET = 12
MSG_ID_SIZE = 8
MSG_ID_OFFSET = 20

def get_hash(byte_string):
    hash = 0

    for byte in byte_string:
        hash = (37 * hash + byte) % 0xFFFFFF

    return hash

class Signal:
    def __init__(self, name, offset, size, type="uint", endianness="little"):
        self.name = name
        self.offset = offset
        self.size = size
        self.endianness = endianness
        self.type = type

    def get_word_offset(self, width):
        return self.offset // width

    def get_word_size(self, width):
        words = self.size // width

        if self.size % width > 0:
            words += 1

        return words

    def get_word_mask(self, word_offset, width):
        offset_from_word = self.offset - (word_offset * width)
        zeros_after = (word_offset * width + width) - (self.offset + self.size)

        if offset_from_word < 0:
            offset_from_word = 0

        if zeros_after < 0:
            zeros_after = 0

        n_bits = width - (offset_from_word + zeros_after)

        return ((2**n_bits - 1) << offset_from_word)

    def get_words(self, width):
        first = self.get_word_offset(width)
        last = (self.offset + self.size - 1) // width

        for word in range(first, last + 1):
            offset_from_word = self.offset - (word * width)

            yield {
                'offset': word,
                'bit_offset': offset_from_word if offset_from_word >= 0 else 0,
                'mask': self.get_word_mask(word, width),
            }

    @classmethod
    def get_from_json(cls, data):
        name = data["name"]
        size = int(data["size"], 16)
        offset = int(data["offset"], 16)
        type = data.get("type", "uint")
        endianness = data.get("endianness", "little")
    
        return cls(
            name=name,
            size=size,
            offset=offset,
            endianness=endianness,
            type=type,
        )

    def get_value_from_data(self, data):
        value = 0

        for index, word in enumerate(self.get_words(8)):
            value |= ((data[word['offset']] & word['mask']) >> word['bit_offset']) << index * 8

        return value

    @property
    def hash(self):
        string = ":".join([
            self.name,
            str(self.size),
            self.type,
        ]).encode()

        return get_hash(string)


class Message:
    def __init__(self, id, name, priority):
        self.id = id
        self.name = name
        self.priority = priority
        self.signals = []

    def add_signal(self, signal):
        self.signals.append(signal)

    def get_mask(self):
        return self.id << MSG_ID_OFFSET

    def get_id(self, from_node_id=0, to_node_id=0):
        return (
            (self.id << MSG_ID_OFFSET) +
            (to_node_id << TO_NODE_ID_OFFSET) +
            (from_node_id << FROM_NODE_ID_OFFSET) +
            self.priority
        )

    def get_broadcast_id(self, from_node_id):
        return self.get_id(from_node_id)

    def get_listen_id(self):
        return self.get_id()

    @classmethod
    def get_from_json(cls, data):
        id = int(data["id"], 16)
        name = data["name"]
        priority = int(data["priority"], 16)
        signals = data["signals"]
    
        message = cls(
            id=id,
            name=name,
            priority=priority,
        )
    
        for signal_data in signals:
            message.add_signal(Signal.get_from_json(signal_data))
    
        return message

    @staticmethod
    def get_id_from_can_id(can_id):
        return (can_id >> MSG_ID_OFFSET) & 0xFF

    @staticmethod
    def get_receiver_from_can_id(can_id):
        return (can_id >> TO_NODE_ID_OFFSET) & 0xFF

    @staticmethod
    def get_sender_from_can_id(can_id):
        return (can_id >> FROM_NODE_ID_OFFSET) & 0xFF

    def get_signal_values_from_data(self, data):
        return {
            signal.name: (signal.get_value_from_data(data), signal)
            for signal in self.signals
        }

    def get_data_from_signal_values(self, values):
        data = 0

        for signal in self.signals:
            try:
                value = values[signal.name]
                conf = next(signal.get_words(64))
                data |= (value << conf['bit_offset']) & conf['mask']
            except KeyError:
                pass

        return data

    @property
    def hash(self):
        hash = 0

        for signal in self.signals:
            hash = hash ^ signal.hash

        return hash

    def __str__(self):
        return "{} ({})".format(hex(self.id), self.name)

class Node:
    def __init__(self, name):
        self.name = name
        self.rx_messages = []
        self.tx_messages = []
        self.all_messages = []

    def add_rx_message(self, message):
        self.rx_messages.append(message)
        self.all_messages.append(message)

    def add_tx_message(self, message):
        self.tx_messages.append(message)
        self.all_messages.append(message)

    @classmethod
    def get_from_json(cls, data, messages):
        name = data["name"]
        rx_messages = data["rx"]
        tx_messages = data["tx"]
    
        node = cls(
            name=name,
        )
    
        for rx_name in rx_messages:
            node.add_rx_message(
                messages[rx_name]
            )
    
        for tx_name in tx_messages:
            node.add_tx_message(
                messages[tx_name]
            )
    
        return node

    def __str__(self):
        return "{}".format(self.name)

class Enum:
    def __init__(self, name, members={}):
        self.name = name
        self.members = {
            name: int(value, 16)
            for name, value in members.items()
        }

    def get_name_from_value(self, value):
        for name in self.members:
            if value == self.members[name]:
                return name

        return None

    def __str__(self):
        return "{}".format(self.name)
