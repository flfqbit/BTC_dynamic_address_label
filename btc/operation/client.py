from .settings import *
from .tools import dec_to_hex, add_to_16, ascii_2_hex, hex_2_ascii
import blockcypher
import random

from bitcoin import compress, privkey_to_pubkey, pubkey_to_address
from blockcypher import create_unsigned_tx, verify_unsigned_tx, make_tx_signatures, broadcast_signed_transaction
from blockcypher.utils import is_valid_coin_symbol
from blockcypher.constants import COIN_SYMBOL_MAPPINGS
from requests.exceptions import ProxyError, ConnectionError
from binascii import b2a_hex, a2b_hex


class BitcoinClient(object):
    def __init__(self):
        self._sk = SK
        self._pk = privkey_to_pubkey(self._sk)

        self._addr = pubkey_to_address(
            pubkey=self._pk,
            # this method only supports paying from pubkey anyway
            magicbyte=COIN_SYMBOL_MAPPINGS['btc-testnet']['vbyte_pubkey'],
        )

    def get_tx_hash(self, addr=MONITORING_ADDRESS, txn_limit=10):
        """
        获取交易哈希
        :param txn_limit: 限制输出数量
        :param addr: 比特币地址，默认从setting.py里面导入，也可以指定
        :return: 返回list 查询到的和addr相关的交易hash
        """
        try:
            addr_full_info = blockcypher.get_address_full(addr, coin_symbol='btc-testnet', api_key=MY_TOKEN,
                                                          txn_limit=txn_limit)
        except AssertionError:
            raise Exception('params error')
        except ConnectionError:
            raise Exception('network error')
        except Exception as e:
            raise Exception('other error', e)
        txs = []
        op_returns = []

        for tx in addr_full_info['txs']:
            for output in tx['outputs']:
                if output['script_type'] == 'null-data':
                    txs.append((tx['hash'], tx['received']))

        return txs

    # 这个筛选结果是去混淆后的数据
    def get_raw_data_by_tx_hash(self, tx):
        """
        根据txhash查找op_return
        :param tx: 交易hash
        :return: op_return的data_hex
        """
        try:
            tx = blockcypher.get_transaction_details(tx_hash=tx, coin_symbol='btc-testnet', api_key=MY_TOKEN)
        except AssertionError:
            raise Exception('params error')
        except ConnectionError:
            raise Exception('network error')
        except Exception as e:
            raise Exception('other error', e)
        op_return_data = ''
        for output in tx['outputs']:
            if output['script_type'] == 'null-data':
                op_return_data = output['data_hex']
                break
        if op_return_data:
            return hex_2_ascii(self.data_extract_from_opreturn(bytes.fromhex(op_return_data)))
        return ''

    # 这个筛选结果是链上数据
    def get_data_by_tx_hash(self, tx):
        """
        根据txhash查找op_return
        :param tx: 交易hash
        :return: op_return的data_hex
        """
        try:
            tx = blockcypher.get_transaction_details(tx_hash=tx, coin_symbol='btc-testnet', api_key=MY_TOKEN)
        except AssertionError:
            raise Exception('params error')
        except ConnectionError:
            raise Exception('network error')
        except Exception as e:
            raise Exception('other error', e)

        for output in tx['outputs']:
            if output['script_type'] == 'null-data':
                hex_data = bytes.fromhex(output['data_hex'])  # str 十六进制解密 => bytes => 再16进制解码
                return hex_2_ascii(hex_data)

        return ''

    def get_all_data_by_addr(self, addr=MONITORING_ADDRESS):
        """
        根据比特币地址,返回所有op_return和对应交易的hash
        :param addr:默认从setting.py里面导入，也可以指定
        :return:所有op_return和对应交易的hash ([txs],[op_returns])
        """
        try:
            addr_full_info = blockcypher.get_address_full(addr, coin_symbol='btc-testnet', api_key=MY_TOKEN)
        except AssertionError:
            raise Exception('params error')
        except ConnectionError:
            raise Exception('network error')
        except Exception as e:
            raise Exception('other error', e)

        txs = []
        op_returns = []

        for tx in addr_full_info['txs']:
            for output in tx['outputs']:
                if output['script_type'] == 'null-data':
                    txs.append(tx['hash'])
                    op_returns.append(output['data_hex'])

        return txs, op_returns

    # 这个是进行混淆再发送混淆后数据的接口，输入是原始数据
    def shuffle_and_post_data(self, message, from_privkey=None, to_address=None, to_satoshis=0, change_address=None,
                              privkey_is_compressed=False, min_confirmations=0, api_key=MY_TOKEN,
                              coin_symbol='btc-testnet'):
        try:
            message = ascii_2_hex(message)  # 十六进制编码 hello => '68656c6c6f'
            message = self.data_shuffle(message)
            txhash = self._post_data(message, from_privkey, to_address, to_satoshis, change_address,
                                     privkey_is_compressed, min_confirmations, api_key,
                                     coin_symbol)
            return txhash
        except AssertionError:
            raise Exception('params error')
        except ConnectionError:
            raise Exception('network error')
        except Exception as e:
            raise Exception('other error', e)

    # 这个是直接发送混淆后数据的接口，输入是已经混淆的数据
    def post_data(self, message, from_privkey=None, to_address=None, to_satoshis=0, change_address=None,
                  privkey_is_compressed=False, min_confirmations=0, api_key=MY_TOKEN, coin_symbol='btc-testnet'):
        try:

            message = ascii_2_hex(message)  # 十六进制编码 hello => '68656c6c6f'
            # message = self.data_shuffle(message)
            txhash = self._post_data(message, from_privkey=None, to_address=None, to_satoshis=0, change_address=None,
                                     privkey_is_compressed=False, min_confirmations=0, api_key=MY_TOKEN,
                                     coin_symbol='btc-testnet')
            return txhash
        except AssertionError:
            raise Exception('params error')
        except ConnectionError:
            raise Exception('network error')
        except Exception as e:
            raise Exception('other error', e)

    def get_from_address(self, from_privkey=None, to_satoshis=0, privkey_is_compressed=False, api_key=MY_TOKEN,
                         coin_symbol='btc-testnet'):
        assert is_valid_coin_symbol(coin_symbol), coin_symbol
        assert isinstance(to_satoshis, int), to_satoshis
        assert api_key, 'api_key required'

        if not from_privkey:
            from_privkey = self._sk

        from_privkey = dec_to_hex(from_privkey)

        if privkey_is_compressed:
            from_pubkey = compress(privkey_to_pubkey(from_privkey))
        else:
            from_pubkey = privkey_to_pubkey(from_privkey)
        from_address = pubkey_to_address(
            pubkey=from_pubkey,
            # this method only supports paying from pubkey anyway
            magicbyte=COIN_SYMBOL_MAPPINGS[coin_symbol]['vbyte_pubkey'],
        )

        return from_address

    def _post_data(self, message, from_privkey=None, to_address=None, to_satoshis=0, change_address=None,
                   privkey_is_compressed=False, min_confirmations=0, api_key=MY_TOKEN, coin_symbol='btc-testnet'):
        """

        :param message: 要嵌入的OP_return数据 string
        :param from_privkey: 发送地址的私钥 10进制，默认为self._sk
        :param to_address: 接收地址，只发送op_return无需设置
        :param to_satoshis: 转账金额，只发送op_return无需设置
        :param change_address: 找钱地址，无需设置
        :param privkey_is_compressed: 私钥是否是压缩的，咱们不压缩，默认False
        :param min_confirmations:Number of subsequent blocks, including the block the transaction is in. Unconfirmed transactions have 0 confirmations.
        :param api_key:
        :param coin_symbol: 网络，目前测试链
        :return: 发送后交易的hash
        """
        # print('postData:')
        assert is_valid_coin_symbol(coin_symbol), coin_symbol
        assert isinstance(to_satoshis, int), to_satoshis
        assert api_key, 'api_key required'

        if not from_privkey:
            from_privkey = self._sk

        from_privkey = dec_to_hex(from_privkey)

        if privkey_is_compressed:
            from_pubkey = compress(privkey_to_pubkey(from_privkey))
        else:
            from_pubkey = privkey_to_pubkey(from_privkey)
        from_address = pubkey_to_address(
            pubkey=from_pubkey,
            # this method only supports paying from pubkey anyway
            magicbyte=COIN_SYMBOL_MAPPINGS[coin_symbol]['vbyte_pubkey'],
        )

        # inputs = [{'address': from_address}, ]
        # logger.info('inputs: %s' % inputs)
        # outputs = [{'address': to_address, 'value': to_satoshis}, ]
        # logger.info('outputs: %s' % outputs)

        inputs = [{'address': from_address}, ]
        # logger.info('inputs: %s' % inputs)
        message_len = len(message)
        # print(message_len)
        if isinstance(message, bytes):
            message_hex = message.hex()
        else:
            if message_len > 0xff:
                message_hex = message
                message_len = message_len // 2
            else:
                message_hex = message.encode('ascii').hex()

        script_command = {255: [2, '4c'], 0xffff: [4, '4d'], 0xffffffff: [8, '4e']}
        op_script = None
        for l, command in script_command.items():
            if message_len <= l:
                message_len = format(message_len, 'x').rjust(command[0], '0')
                op_script = "6a" + command[1] + message_len + message_hex
                break
        # print(op_script)
        outputs = [{'value': 0, "script_type": "null-data", "data_hex": message_hex, "script": op_script}, ]
        # outputs = [{'value': 0, "script_type": "null-data", "data_hex":message_hex, "script":op_script}, {'address':to_address,'value':45300}]
        # logger.info('outputs: %s' % outputs)

        unsigned_tx = create_unsigned_tx(
            inputs=inputs,
            outputs=outputs,
            # may build with no change address, but if so will verify change in next step
            # done for extra security in case of client-side bug in change address generation
            change_address=change_address,
            coin_symbol=coin_symbol,
            preference='low',
            min_confirmations=min_confirmations,
            verify_tosigntx=False,  # will verify in next step
            include_tosigntx=True,
            api_key=api_key,
        )
        # logger.info('unsigned_tx: %s' % unsigned_tx)

        # print("unsigned_tx ... ")
        if 'errors' in unsigned_tx:
            # print('TX Error(s): Tx NOT Signed or Broadcast')
            # for error in unsigned_tx['errors']:
            #     print(error['error'])
            # Abandon
            raise Exception('Build Unsigned TX Error')

        if change_address:
            change_address_to_use = change_address
        else:
            change_address_to_use = from_address

        tx_is_correct, err_msg = verify_unsigned_tx(
            unsigned_tx=unsigned_tx,
            inputs=inputs,
            outputs=outputs,
            sweep_funds=bool(to_satoshis == -1),
            change_address=change_address_to_use,
            coin_symbol=coin_symbol,
        )
        if not tx_is_correct:
            # print(unsigned_tx)  # for debug
            raise Exception('TX Verification Error: %s' % err_msg)

        privkey_list, pubkey_list = [], []
        for proposed_input in unsigned_tx['tx']['inputs']:
            privkey_list.append(from_privkey)
            pubkey_list.append(from_pubkey)
            # paying from a single key should only mean one address per input:
            assert len(proposed_input['addresses']) == 1, proposed_input['addresses']
        # logger.info('privkey_list: %s' % privkey_list)
        # logger.info('pubkey_list: %s' % pubkey_list)

        # print('privkey_list : ', privkey_list)
        # print('pubkey_list : ', pubkey_list)
        # sign locally
        tx_signatures = make_tx_signatures(
            txs_to_sign=unsigned_tx['tosign'],
            privkey_list=privkey_list,
            pubkey_list=pubkey_list,
        )
        # logger.info('tx_signatures: %s' % tx_signatures)

        # print('tx_signatures : ', tx_signatures)
        # broadcast TX
        broadcasted_tx = broadcast_signed_transaction(
            unsigned_tx=unsigned_tx,
            signatures=tx_signatures,
            pubkeys=pubkey_list,
            coin_symbol=coin_symbol,
            api_key=api_key,
        )
        # logger.info('broadcasted_tx: %s' % broadcasted_tx)

        if 'errors' in broadcasted_tx:
            # print('TX Error(s): Tx May NOT Have Been Broadcast')
            # for error in broadcasted_tx['errors']:
            #     print(error['error'])
            # print(broadcasted_tx)
            raise Exception('Tx May NOT Have Been Broadcast')
            # return

        # print('tx_hash : ', broadcasted_tx['tx']['hash'])
        return broadcasted_tx['tx']['hash']

    def gen_op_return_length(self):
        """
        根据分布规律输出op_return长度
        :return: op_return长度 int
        """
        total = sum(DISTRIBUTION.values())  # 权重求和
        _random = random.randint(0, total)  # 在0与权重和之前获取一个随机数
        curr_sum = 0
        ret = None

        _keys = DISTRIBUTION.keys()  # 使用Python3.x中的keys
        for k in _keys:
            curr_sum += DISTRIBUTION[k]  # 在遍历中，累加当前权重值
            if _random <= curr_sum:  # 当随机数<=当前权重和时，返回权重key
                ret = k
                break
        return ret

    def aes_encrypt(self, text):
        """
        AES_CBC加密函数
        :param text: str，要加密的字符串
        :return: bytes 十六进制
        """
        text = add_to_16(text)
        cryptos = AES.new(AES_KEY, AES_MODE, AES_IV)
        cipher_text = cryptos.encrypt(text)
        # 因为AES加密后的字符串不一定是ascii字符集的，输出保存可能存在问题，所以这里转为16进制字符串
        return b2a_hex(cipher_text)  # b'8572914becf187f3f9e9744fc953c6bf'

    def aes_decrypt(self, text):
        """
        AES_CBC解密函数
        :param text: bytes
        :return: str 字符串
        """
        cryptos = AES.new(AES_KEY, AES_MODE, AES_IV)
        plain_text = cryptos.decrypt(a2b_hex(text))
        return bytes.decode(plain_text).rstrip('\0')  # b'hello world\x00\x00\x00\x00\x00' => hello world

    def make_transaction(self, to_address, to_satoshis):
        """
        转账接口
        :param to_address: 目标地址
        :param to_satoshis: 聪
        :return: 返回string 交易hash
        """
        try:
            from_privkey = dec_to_hex(self._sk)
            txhash = blockcypher.simple_spend(from_privkey=from_privkey, to_address=to_address, to_satoshis=to_satoshis,
                                              privkey_is_compressed=False, api_key=MY_TOKEN, coin_symbol='btc-testnet')
            return txhash
        except AssertionError:
            raise Exception('params error')
        except ConnectionError:
            raise Exception('network error')
        except Exception as e:
            raise Exception('other error', e)

    #高峰临时测试函数1
    def make_transaction_gf(self, from_address_sk, to_address, to_satoshis):
        """
        转账接口
        :param to_address: 目标地址
        :param to_satoshis: 聪
        :return: 返回string 交易hash
        """
        try:
            from_privkey = dec_to_hex(from_address_sk)
            txhash = blockcypher.simple_spend(from_privkey=from_privkey, to_address=to_address, to_satoshis=to_satoshis,
                                              privkey_is_compressed=False, api_key=MY_TOKEN, coin_symbol='btc-testnet')
            return txhash
        except AssertionError:
            raise Exception('params error')
        except ConnectionError:
            raise Exception('network error')
        except Exception as e:
            raise Exception('other error', e)

    # 高峰临时测试函数2
    def get_blockHeight_latest_gf(self):
        """
        获取当前最新高度
        """
        try:
            blockHeight=blockcypher.get_latest_block_height(coin_symbol='btc-testnet', api_key=MY_TOKEN)
            return blockHeight
        except AssertionError:
            raise Exception('params error')
        except ConnectionError:
            raise Exception('network error')
        except Exception as e:
            raise Exception('other error', e)

    # 高峰临时测试函数3
    def get_blockHashByHeight_gf(self, height):
        """
        获取当前最新高度
        """
        try:
            blockHash = blockcypher.get_block_hash(block_height=str(height),coin_symbol='btc-testnet', api_key=MY_TOKEN)
            return blockHash
        except AssertionError:
            raise Exception('params error')
        except ConnectionError:
            raise Exception('network error')
        except Exception as e:
            raise Exception('other error', e)

    # 高峰临时测试函数4
    def get_tx_hash_gf(self, addr, limit):
        """
        根据指定地址或取地址相关的交易哈希(哈希和时间)；如果有，输出最近的第一个交易哈希，否则输出""
        """
        try:
            addr_full_info = blockcypher.get_address_full(addr, coin_symbol='btc-testnet', api_key=MY_TOKEN,
                                                      txn_limit =limit)
        except AssertionError:
            raise Exception('params error')
        except ConnectionError:
            raise Exception('network error')
        except Exception as e:
            raise Exception('other error', e)

        txs = []
        for tx in addr_full_info['txs']:
            txs.append((tx['hash'], tx['received']))

        return txs

    def get_balance(self, addr=None, ):

        if not addr: addr = self._addr
        # print(addr)
        try:
            balance = blockcypher.get_address_overview(address=addr, api_key=MY_TOKEN, coin_symbol='btc-testnet')[
                'balance']
            return balance
        except AssertionError:
            raise Exception('params error')
        except ConnectionError:
            raise Exception('network error')
        except Exception as e:
            raise Exception('other error', e)

    def data_shuffle(self, message):
        size = len(message)
        if size > 78:
            raise Exception('params error')
        size_of_data = format(size, 'x').rjust(2, '0').upper()
        size_of_random = 78 - size
        padding = ''
        while size_of_random:
            padding += PADDINGS[random.randint(0, 15)]
            size_of_random -= 1

        data = padding + message + size_of_data
        return data

    def data_extract_from_opreturn(self, data):
        size_of_data = int(data[-2:], 16)
        return data[-size_of_data - 2:-2]

    # 这个筛选结果是链上数据
    def get_op_return_by_tx_hash(self, tx):
        """
        根据txhash查找op_return
        :param tx: 交易hash
        :return: op_return的data_hex
        """
        try:
            tx = blockcypher.get_transaction_details(tx_hash=tx, coin_symbol='btc-testnet', api_key=MY_TOKEN)
        except AssertionError:
            raise Exception('params error')
        except ConnectionError:
            raise Exception('network error')
        except Exception as e:
            raise Exception('other error', e)

        for output in tx['outputs']:
            if output['script_type'] == 'null-data':
                hex_data = bytes.fromhex(output['data_hex'])  # str 十六进制解密 => bytes => 再16进制解码
                return hex_data.decode()

        return ''

    def xor_send(self, arr):
        txs = []
        for data in arr:
            txs.append(self._post_data(message=data))

        return txs

    def xor_extract(self, txs):
        op_returns = []
        for tx in txs:
            op_returns.append(self.get_op_return_by_tx_hash(tx))

        return op_returns

    def omni(self, message, from_privkey=None, to_address=None, to_satoshis=0, change_address=None,
              privkey_is_compressed=False, min_confirmations=0, api_key=MY_TOKEN, coin_symbol='btc-testnet'):
        """

        :param message: 要嵌入的OP_return数据 string
        :param from_privkey: 发送地址的私钥 10进制，默认为self._sk
        :param to_address: 接收地址，
        :param to_satoshis: 转账金额，
        :param change_address: 找钱地址，无需设置
        :param privkey_is_compressed: 私钥是否是压缩的，咱们不压缩，默认False
        :param min_confirmations:Number of subsequent blocks, including the block the transaction is in. Unconfirmed transactions have 0 confirmations.
        :param api_key:
        :param coin_symbol: 网络，目前测试链
        :return: 发送后交易的hash
        """
        # print('postData:')
        assert is_valid_coin_symbol(coin_symbol), coin_symbol
        assert isinstance(to_satoshis, int), to_satoshis
        assert api_key, 'api_key required'

        if not from_privkey:
            from_privkey = self._sk

        from_privkey = dec_to_hex(from_privkey)

        if privkey_is_compressed:
            from_pubkey = compress(privkey_to_pubkey(from_privkey))
        else:
            from_pubkey = privkey_to_pubkey(from_privkey)
        from_address = pubkey_to_address(
            pubkey=from_pubkey,
            # this method only supports paying from pubkey anyway
            magicbyte=COIN_SYMBOL_MAPPINGS[coin_symbol]['vbyte_pubkey'],
        )

        # inputs = [{'address': from_address}, ]
        # logger.info('inputs: %s' % inputs)
        # outputs = [{'address': to_address, 'value': to_satoshis}, ]
        # logger.info('outputs: %s' % outputs)

        inputs = [{'address': from_address}, ]
        # logger.info('inputs: %s' % inputs)
        message_len = len(message)
        # print(message_len)
        if isinstance(message, bytes):
            message_hex = message.hex()
        else:
            # message_hex = message.encode('ascii').hex()
            message_hex = message

        message_hex = message_hex.rjust(16, '0')

        # message_len = format(message_len, 'x').rjust(2, '0')
        op_script = "6a146f6d6e69000000000000001f" + message_hex

        # print(op_script)
        outputs = [{'value': 0, "script_type": "null-data", "data_hex": message_hex, "script": op_script},
                   {'address': to_address, 'value': 3600}]
        # outputs = [{'value': 0, "script_type": "null-data", "data_hex":message_hex, "script":op_script}, {'address':to_address,'value':45300}]
        # logger.info('outputs: %s' % outputs)

        unsigned_tx = create_unsigned_tx(
            inputs=inputs,
            outputs=outputs,
            # may build with no change address, but if so will verify change in next step
            # done for extra security in case of client-side bug in change address generation
            change_address=change_address,
            coin_symbol=coin_symbol,
            preference='low',
            min_confirmations=min_confirmations,
            verify_tosigntx=False,  # will verify in next step
            include_tosigntx=True,
            api_key=api_key,
        )
        # logger.info('unsigned_tx: %s' % unsigned_tx)

        # print("unsigned_tx ... ")
        if 'errors' in unsigned_tx:
            # print('TX Error(s): Tx NOT Signed or Broadcast')
            # for error in unsigned_tx['errors']:
            #     print(error['error'])
            # Abandon
            raise Exception('Build Unsigned TX Error')

        if change_address:
            change_address_to_use = change_address
        else:
            change_address_to_use = from_address

        tx_is_correct, err_msg = verify_unsigned_tx(
            unsigned_tx=unsigned_tx,
            inputs=inputs,
            outputs=outputs,
            sweep_funds=bool(to_satoshis == -1),
            change_address=change_address_to_use,
            coin_symbol=coin_symbol,
        )
        if not tx_is_correct:
            # print(unsigned_tx)  # for debug
            raise Exception('TX Verification Error: %s' % err_msg)

        privkey_list, pubkey_list = [], []
        for proposed_input in unsigned_tx['tx']['inputs']:
            privkey_list.append(from_privkey)
            pubkey_list.append(from_pubkey)
            # paying from a single key should only mean one address per input:
            assert len(proposed_input['addresses']) == 1, proposed_input['addresses']
        # logger.info('privkey_list: %s' % privkey_list)
        # logger.info('pubkey_list: %s' % pubkey_list)

        # print('privkey_list : ', privkey_list)
        # print('pubkey_list : ', pubkey_list)
        # sign locally
        tx_signatures = make_tx_signatures(
            txs_to_sign=unsigned_tx['tosign'],
            privkey_list=privkey_list,
            pubkey_list=pubkey_list,
        )
        # logger.info('tx_signatures: %s' % tx_signatures)

        # print('tx_signatures : ', tx_signatures)
        # broadcast TX
        broadcasted_tx = broadcast_signed_transaction(
            unsigned_tx=unsigned_tx,
            signatures=tx_signatures,
            pubkeys=pubkey_list,
            coin_symbol=coin_symbol,
            api_key=api_key,
        )
        # logger.info('broadcasted_tx: %s' % broadcasted_tx)

        if 'errors' in broadcasted_tx:
            # print('TX Error(s): Tx May NOT Have Been Broadcast')
            # for error in broadcasted_tx['errors']:
            #     print(error['error'])
            # print(broadcasted_tx)
            raise Exception('Tx May NOT Have Been Broadcast')
            # return

        # print('tx_hash : ', broadcasted_tx['tx']['hash'])
        return broadcasted_tx['tx']['hash']
