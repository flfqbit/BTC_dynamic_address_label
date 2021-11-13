import binascii


def gen_random(a, b):
    return a, b


def dec_to_hex(pk):
    hex_pk = hex(pk)[2:]
    if len(hex_pk) % 2:
        return '0' + hex_pk
    return hex(pk)[2:]


def add_to_16(text):
    """
    如果text不足16位的倍数就用空格补足为16位
    :param text: str 字符串
    :return:bytes 16位    input:'haha' output: b'haha\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    """
    if len(text.encode('utf-8')) % 16:
        add = 16 - (len(text.encode('utf-8')) % 16)
    else:
        add = 0
    text = text + ('\0' * add)
    return text.encode('utf-8')


# AES https://www.cnblogs.com/niuu/p/10107212.html

def ascii_2_hex(data):
    hex_data = binascii.hexlify(data.encode('utf-8')).decode('utf-8')
    return hex_data


def hex_2_ascii(hex_data):
    data = binascii.a2b_hex(hex_data).decode('utf-8')
    return data

