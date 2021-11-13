from Crypto.Cipher import AES
#私钥，外部生成，写在这里，用于生成交易，具体查看blockcypher API的使用方法
SK = xxxx
#地址
MONITORING_ADDRESS = 'xxxx'

#高峰token,blockcypher,在网站上申请
MY_TOKEN = 'xxx'   #高峰token

DISTRIBUTION = {22: 30, 30: 2, 42: 3, 83: 60}  # 长度:权重 具体分布情况可以参考 https://opreturn.org/op-return-sizes/

AES_KEY = '9999999999999999'.encode('utf-8')
AES_IV = b'qqqqqqqqqqqqqqqq'
AES_MODE = AES.MODE_CBC
