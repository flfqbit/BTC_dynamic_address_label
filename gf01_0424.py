import blockcypher

from user.operation import UserClient
from user.operation.settings import AES_MASTER_KEY, AES_RANDOM_KEY, BTC_ADDRESS, ETH_ADDRESS
from django.test import TestCase
from Crypto.Hash import HMAC, SHA256
import random
import time
from btc.operation.client import BitcoinClient
import binascii

from bitcoin import compress, privkey_to_pubkey, pubkey_to_address
from blockcypher.constants import COIN_SYMBOL_MAPPINGS

# 代码介绍
# 作者：高峰
# 内容：用于实现基于hmac的动态标签机制
# 相关资料：
## https://pycryptodome.readthedocs.io/en/latest/src/protocol/ss.html
## https://github.com/Legrandin/pycryptodome
uClient = UserClient()
BitcoinClient = BitcoinClient()


class hmacBasedDynamicLabel(TestCase):

    @staticmethod
    def createAddr(bitcoin_sk):
        """
            输入：比特币私钥，支持hex格式和整数格式
            输出：比特币地址
        """
        # sk = 72480691806471240390004615726374007661314220739110435308617549875591683837486
        sk = bitcoin_sk
        pk = privkey_to_pubkey(sk)

        addr = pubkey_to_address(
            pubkey=pk,
            # this method only supports paying from pubkey anyway
            magicbyte=COIN_SYMBOL_MAPPINGS['btc-testnet']['vbyte_pubkey'],
        )
        return addr

    @staticmethod
    def hmacStr(block_hash):
        """
        输入：区块哈希值，hex
        输出：基于hamc的字符串(64个hex字符)
        """
        # # str to bytes
        # bytes(s, encoding="utf8")
        #
        # # bytes to str
        # str(b, encoding="utf-8")

        secret = b'E84216ACC9321755'
        h = HMAC.new(secret, digestmod=SHA256)
        # h.update(b'Hello')
        h.update(bytes(block_hash, encoding="utf8"))
        return h.hexdigest()

    @staticmethod
    def createBitcoinSk(sk_str):
        """
            输入：16进制字符串
            输出：满足比特币私钥的256位整数（二进制），输出为10进制数字

            概念解析：
            比特币的私钥是一系列32字节。有多种写法：
            - 256个1和0（32*8=256）或100个骰子所组成的字符串。
            - Base64字符串
            - WIF密钥
            - 助记符短语
            - 十六进制字符串
            https://blog.csdn.net/zhoulei124/article/details/94611953
        """
        # sk = 72480691806471240390004615726374007661314220739110435308617549875591683837486
        sk = int(sk_str, 16)
        return sk

    def get_randomHeight(self, height_start, height_latest):
        """
            获取指定范围的随机整数，j为协商高度，n为当前最新高度
            输入：输入两个整数，取中间的整数
            输出：整数
        """
        num = random.randint(height_start, height_latest)
        return num

    def get_heightStart(self, height_latest):
        """
            获取随机选择的起始高度，默认设置为前10
            输入：输入最新的区块高度
            输出：返回随机选择的起始高度
        """
        return height_latest - 10

    def create_addrWithLabel(self, blockhash):
        """
            生成特殊地址
            输入：输入区块哈希
            输出：特殊地址
        """
        sk_str = self.hmacStr(blockhash)
        addrWithLabel = self.createAddr(sk_str)

        #print("sk_str: " + sk_str)
        #print("addrWithLabel: " + addrWithLabel)

        return addrWithLabel

    def send_txWithLabel(self, addr_with_label):
        """
            获取指定范围的随机整数，j为协商高度，n为当前最新高度
            输入：输入两个整数，取中间的整数
            输出：整数
        """
        txHash = BitcoinClient.make_transaction(addr_with_label, 10)

        return txHash

    def check_addr(self, addr):
        """
            检测指定地址是否存在交易？如果存在，说明这是特殊地址
            输入：地址
            输出：交易哈希。如果有，输出最近的第一个交易哈希，否则输出""
        """
        txHashLsit = BitcoinClient.get_tx_hash_gf(addr, 1)
        if (len(txHashLsit) == 0):
            txHash = ""
        else:
            txHash = txHashLsit[0][0]
        return txHash

    def get_blockHeight_latest_gf(self):
        heightLatest = BitcoinClient.get_blockHeight_latest_gf()

        return heightLatest

    def get_blockHashByHeight_gf(self, height):
        blockHash = BitcoinClient.get_blockHashByHeight_gf(height)

        return blockHash

    def check_newTx(self, j):
        """
            检测近期是否存在新的特殊交易，输入j为协商高度
            输入：j为协商高度
            输出：交易哈希列表
        """
        heightLatest = self.get_blockHeight_latest_gf()
        counter = heightLatest
        specialTxHashList = []
        while counter > j:
            blockHash = self.get_blockHashByHeight_gf(counter)
            addrWithLabel = self.create_addrWithLabel(blockHash)
            txhash1 = self.check_addr(addrWithLabel)
            print(str(counter) + ":" + txhash1)
            print("addr: " + addrWithLabel)
            if (txhash1 != ""):
                specialTxHashList.append(txhash1)
            counter -= 1

        return specialTxHashList


def testCreateAddr():
    """
        输入：0x
        输出：打印结果
        概念解析：
            - 测试地址生成功能
        测试结果：
            - 给予交易哈希生成的hamc字符串长度正好是64个16进制字符，满足比特币私钥的长度要求
            - createAddr函数同时支持“大整数”和“十六进制字符串”私钥格式，可以生成比特币地址
    """
    # sk = 72480691806471240390004615726374007661314220739110435308617549875591683837486
    # data1 = "hello world!"
    # 比特币主网区块哈希，高度=627,416，00000000000000000008db2ab36961fb527e6bd8b23a5e0c5fc5b36e6e25cd12
    test1 = hmacBasedDynamicLabel()
    block_hash_627416 = "00000000000000000008db2ab36961fb527e6bd8b23a5e0c5fc5b36e6e25cd12"
    sk_str = test1.hmacStr(block_hash_627416)
    print("sk_str: " + sk_str)

    sk_int = test1.createBitcoinSk(sk_str)
    print("sk_int: " + str(sk_int))

    print("new bitcoin address1: " + test1.createAddr(sk_str))
    print("new bitcoin address2: " + test1.createAddr(sk_int))


def testCreateAddr():
    """
        输入：0x
        输出：打印结果
        概念解析：
            - 测试新生成的地址能否接收比特币和发送比特币
        测试结果：
            - 新生成的地址：mt6MLMHRbToM9FythbyADiA379WdD6kysQ
            - 能够正常接收比特币：
            -- ad20aa762acadffcf47b4e930cb515287bb779d0b8685cda5ef74ee87ca60d52
            --- mmHZSreV1dvWmCUkzVKZCmkjZFVK9dZr2i (output)
            --- mt6MLMHRbToM9FythbyADiA379WdD6kysQ (unspent
            - 能够正常发送比特币：
            -- 5f3b5b4730e9b2d61cfb04acf5ef719620ed67cb69929c40ad26d16b4c9849bb
            --- mt6MLMHRbToM9FythbyADiA379WdD6kysQ (output)
            --- mmHZSreV1dvWmCUkzVKZCmkjZFVK9dZr2i (unspent)
    """
    # 根据区块哈希，生成新地址
    test1 = hmacBasedDynamicLabel()
    block_hash_627416 = "00000000000000000008db2ab36961fb527e6bd8b23a5e0c5fc5b36e6e25cd12"
    sk_str = test1.hmacStr(block_hash_627416)
    addr_new = test1.createAddr(sk_str)
    print("new bitcoin address1: " + addr_new)

    # 给指定地址转账
    test2 = BitcoinClient()
    # make_transaction的第二个参数是转账金额，单位是 0.00000001 BTC
    SK_1 = 72480691806471240390004615726374007661314220739110435308617549875591683837486
    addr_1 = "mmHZSreV1dvWmCUkzVKZCmkjZFVK9dZr2i"
    # print("txhash: " + test2.make_transaction_gf(SK_1, addr_new, 1000000))
    print("txhash: " + test2.make_transaction_gf(test1.createBitcoinSk(sk_str), addr_1, 10000))


def testCreate_addrWithLabel():
    """
        输入：0x
        输出：打印结果
        概念解析：
            - 测试create_addrWithLabel函数能否执行
        测试结果：
            -
    """
    test1 = hmacBasedDynamicLabel()
    heightLatest = BitcoinClient.get_blockHeight_latest_gf()
    heightStart = test1.get_heightStart(heightLatest)
    randomHeight = test1.get_randomHeight(heightStart, heightLatest)
    blockHash = BitcoinClient.get_blockHashByHeight_gf(randomHeight)
    addrWithLabel = test1.create_addrWithLabel(blockHash)

    print("heightStart: " + str(heightStart))
    print("heightLatest: " + str(heightLatest))
    print("randomHeight: " + str(randomHeight))
    print("blockHash: " + blockHash)
    print("addrWithLabel: " + addrWithLabel)


def testSend_txWithLabel():
    """
        输入：0x
        输出：打印结果
        概念解析：
            - 测试send_txWithLabel函数能否执行
        测试结果：
            - 能够正常生成特殊地址，能够正常发起交易
    """
    test1 = hmacBasedDynamicLabel()
    heightLatest = BitcoinClient.get_blockHeight_latest_gf()
    heightStart = test1.get_heightStart(heightLatest)
    randomHeight = test1.get_randomHeight(heightStart, heightLatest)
    blockHash = BitcoinClient.get_blockHashByHeight_gf(randomHeight)
    addrWithLabel = test1.create_addrWithLabel(blockHash)

    txhash1 = test1.send_txWithLabel(addrWithLabel)

    print("heightStart: " + str(heightStart))
    print("heightLatest: " + str(heightLatest))
    print("randomHeight: " + str(randomHeight))
    print("blockHash: " + blockHash)
    print("addrWithLabel: " + addrWithLabel)
    print("txhash: " + txhash1)


def testSend_txWithLabel_shuffle_and_post_data():
    """
        相比函数testSend_txWithLabel()，本函数发出的交易中包含隐蔽数据
        输入：0x
        输出：打印结果
        概念解析：
            - 测试send_txWithLabel函数能否执行
        测试结果：
            - 能够正常生成特殊地址，能够正常发起交易
    """
    test1 = hmacBasedDynamicLabel()
    heightLatest = BitcoinClient.get_blockHeight_latest_gf()
    heightStart = test1.get_heightStart(heightLatest)
    randomHeight = test1.get_randomHeight(heightStart, heightLatest)
    blockHash = BitcoinClient.get_blockHashByHeight_gf(randomHeight)
    addrWithLabel = test1.create_addrWithLabel(blockHash)

    # def shuffle_and_post_data(self, message, from_privkey=None, to_address=None, to_satoshis=0, change_address=None,
    #                           privkey_is_compressed=False, min_confirmations=0, api_key=MY_TOKEN,
    #                           coin_symbol='btc-testnet'):

    # plaintext = "abcdefghigklmnopqrstuvwxyz"
    # sk1 = test1.createBitcoinSk("e815851e6c3f193dfbadfadb11c27be07de22deacf269723a686e9ca031b5ac8")
    # # sk1=72480691806471240390004615726374007661314220739110435308617549875591683837486
    # change_address1 = "mmHZSreV1dvWmCUkzVKZCmkjZFVK9dZr2i"
    #
    # txhash1 = BitcoinClient.shuffle_and_post_data(message=plaintext, from_privkey=sk1, change_address=change_address1)
    plaintext = "plaintext"
    txhash1 = BitcoinClient.shuffle_and_post_data(message=plaintext)

    # print("heightStart: " + str(heightStart))
    # print("heightLatest: " + str(heightLatest))
    # print("randomHeight: " + str(randomHeight))
    # print("blockHash: " + blockHash)
    # print("addrWithLabel: " + addrWithLabel)
    print("txhash: " + txhash1)
    # print("plaintext: " + plaintext)


def testCheck_addr():
    """
        输入：0x
        输出：打印结果
        概念解析：
            - 测试Check_addr函数能否执行
        测试结果：
            - 能够正常返回数据，有交易返回交易哈希，无返回空字符串
    """
    test1 = hmacBasedDynamicLabel()
    heightLatest = BitcoinClient.get_blockHeight_latest_gf()
    blockHash = BitcoinClient.get_blockHashByHeight_gf(1722216)
    addrWithLabel = test1.create_addrWithLabel(blockHash)

    # txhash1 = test1.check_addr(addrWithLabel)
    txhash1 = test1.check_addr("mkKjnXbAPZYZk6gMfVfNxySf1P2tV7pea9")

    print("heightLatest: " + str(heightLatest))
    print("blockHash: " + blockHash)
    print("addrWithLabel: " + addrWithLabel)
    print("txhash: " + txhash1)


def testCheck_newTx(num=20):
    """
        输入：0x
        输出：打印结果
        概念解析：
            - 测试check_newTx函数能否执行
        测试结果：
            - 能够正常返回数据，有交易返回交易哈希，无返回空字符串
    """
    test1 = hmacBasedDynamicLabel()
    # 此处的j做简单处理。实际上j应该是本地存储的一个值，每次检查完后更新。
    j = test1.get_blockHeight_latest_gf() - num
    txhashList = test1.check_newTx(j)
    print("特殊交易个数: " + str(len(txhashList)))
    print("特殊交易哈希列表: ")
    for tx in txhashList:
        print(tx)


def testTime_local_fun(funID=1):
    """
        测试方案中本地函数的成本
        输入：0x
        输出：打印结果
        概念解析：
            - 测试本方案中各个函数的执行时间
            --t_randomNum
            --t_createAddress

        测试结果：
            - 能够各个函数的平均执行时间
    """
    test1=hmacBasedDynamicLabel()
    start_time = time.time()  # 记录程序开始运行时间
    funName=""
    for i in range(1000):
        if(funID==1):
            test1.get_randomHeight(1000, 1100)
            funName="t_randomNum"
        elif(funID==2):
            test1.create_addrWithLabel("0000000000cb932598efc085e06a27469b34be764de9f62a037abc5378915eb5")
            funName = "t_createAddress"

    end_time = time.time()  # 记录程序结束运行时间
    print('%s Took %f second' % (funName, (end_time - start_time)/1000))

def testTime_api(funID=1):
    """
        测试方案的成本
        输入：0x
        输出：打印结果
        概念解析：
            - 测试本方案中各个函数的执行时间
            --t_api_height
            --t_api_hash
            --t_api_getTx
            --t_api_sendTx
            --T1
            --T2

        测试结果：
            - 能够各个函数的平均执行时间
    """
    test1=hmacBasedDynamicLabel()
    start_time = time.time()  # 记录程序开始运行时间
    funName=""
    for i in range(1):
        if(funID==1):
            heightLatest = BitcoinClient.get_blockHeight_latest_gf()
            funName="t_api_height"
        elif(funID==2):
            blockHash = BitcoinClient.get_blockHashByHeight_gf(1732804)
            funName = "t_api_hash"
        elif (funID == 3):
            txHashLsit = BitcoinClient.get_tx_hash_gf("mmHZSreV1dvWmCUkzVKZCmkjZFVK9dZr2i", 1)
            print(txHashLsit)
            funName = "t_api_getTx"
        elif (funID == 4):
            txhash1 = BitcoinClient.shuffle_and_post_data(message="plaintext")
            print(txhash1)
            funName = "t_api_sendTx"
        elif (funID == 5):
            testSend_txWithLabel_shuffle_and_post_data()
            funName = "T1"
        elif (funID == 6):
            testCheck_newTx(num=1)
            funName = "T2"

    end_time = time.time()  # 记录程序结束运行时间
    print('%s Took %f second' % (funName, (end_time - start_time)/1))

# 执行入口
# 发送特殊交易
testSend_txWithLabel()
#testSend_txWithLabel_shuffle_and_post_data()
# 筛选特殊交易
# testCheck_newTx()

# 测试方案中各个函数的执行时间
#testTime_local_fun(funID=1)
#testTime_local_fun(funID=2)
#testTime_api(funID=6)

