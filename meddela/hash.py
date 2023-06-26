def get_hash(byte_string):
    hash = 0

    for byte in byte_string:
        hash = (37 * hash + byte) & 0xFFFFFFFF

    return hash

def to_base36(value):
    letters = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    quotient = value & 0xFFFFFFFF
    result = ''

    while quotient != 0:
        quotient, reminder = divmod(quotient, 36)
        result = letters[reminder] + result

    return result.zfill(7)

