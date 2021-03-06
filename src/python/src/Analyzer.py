from rsa import common, transform, core, PublicKey, pkcs1
import six
import base64
import datetime
import uuid


class DecryptByPublicKey(object):
    """
        先产生模数因子
        然后生成rsa公钥
        再使用rsa公钥去解密传入的加密str
    """
    def __init__(self, activation_code_source, key_source, mode="str"):
        if mode == "str":
            self._activation_code = activation_code_source
        elif mode == "file":
            with open(activation_code_source) as f:
                self._activation_code = f.read()
        self._key_source = key_source
        self._mode = mode
        # 使用公钥字符串求出模数和因子
        self._modulus = None   # 模数
        self._exponent = None  # 因子
        # 使用PublicKey(模数,因子)算出公钥
        self._pub_rsa_key = None

    def _gen_modulus_exponent(self, s) ->int:
        # p.debug("Now base64 decode pub key,return modulus and exponent")
        # 对字符串解码, 解码成功返回 模数和指数
        b_str = base64.urlsafe_b64decode(s)
        if len(b_str) < 162:
            return False
        hex_str = b_str.hex()
        # 按位转换成16进制
        for x in b_str:
            h = hex(ord(chr(x)))[2:]
            h = h.rjust(2, '0')
            hex_str += h
        # 找到模数和指数的开头结束位置
        m_start = 33 * 2
        e_start = 291 * 2
        m_len = 256 * 2
        e_len = 3 * 2
        self._modulus = int(hex_str[m_start:m_start + m_len], 16)
        self._exponent = int(hex_str[e_start:e_start + e_len], 16)
        # self._modulus = hex_str[m_start:m_start + m_len]
        # self._exponent = hex_str[e_start:e_start + e_len]

    def _load_key_file(self):
        # 从.pem文件中读取key
        try:
            with open(self._key_source) as f:
                p = f.read()
                self._pub_rsa_key = PublicKey.load_pkcs1(p.encode())
        except Exception as error:
            raise error

    def _gen_rsa_pubkey(self):
        # 将pub key string 转换为 pub rsa key
        # p.debug("Now turn key string to rsa key")
        try:
            rsa_pubkey = PublicKey(self._modulus, self._exponent)
            # 赋值到_pub_rsa_key
            self._pub_rsa_key = PublicKey.load_pkcs1(rsa_pubkey.save_pkcs1())
            # print("self._pub_rsa_key：{}".format(rsa_pubkey))
            # p.error("self._pub_rsa_key：{}".format(self._pub_rsa_key))
        except Exception as e:
            # p.error(e)
            # p.error("Invalid public_key")
            raise e

    def decode(self) ->str:
        """
        decrypt msg by public key
        """
        # p.debug("Now decrypt msg by public rsa key")
        # public_key = PublicKey.load_pkcs1(self._pub_rsa_key)
        keylength = common.byte_size(self._pub_rsa_key.n)
        encrypted = transform.bytes2int(base64.urlsafe_b64decode(self._activation_code))
        decrypted = core.decrypt_int(encrypted, self._pub_rsa_key.e, self._pub_rsa_key.n)
        clearsig = transform.int2bytes(decrypted, keylength)
        # Compare with the signed one
        # 这里使用了six库的iterbytes()方法去模拟python2对bytes的轮询
        if len(clearsig) > 0 and list(six.iterbytes(clearsig))[0] == 0:
            try:
                raw_info = clearsig[clearsig.find(b'\xff\x00')+2:]
            except Exception as e:
                raise e
            return raw_info.decode()

    def decrypt(self) -> str:
        """
        先产生模数因子
        然后生成rsa公钥
        再使用rsa公钥去解密
        """
        if self._mode == "str":
            self._gen_modulus_exponent(self._key_source)
            self._gen_rsa_pubkey()
        elif self._mode == "file":
            self._load_key_file()
        ret = self.decode()
        return ret

    # 获取机器Mac地址
    def get_mac_address(self):
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        return "-".join([mac[e:e + 2] for e in range(0, 11, 2)]).upper()

    # 验证激活码
    def validity(self):
        mess_list = self.decrypt().split('&')
        mac = self.get_mac_address()
        if mac == mess_list[0]:
            if datetime.datetime.strptime(mess_list[1], '%Y-%m-%d') > datetime.datetime.now():
                return True
            else:
                print("激活码已过期，请重新获取!")
                return False
        else:
            print("设备验证未通过")
            return False


if __name__ == "__main__":
    # Base64格式的激活码，包含注册信息和有效期
    activation_code = """"""
    # Base64格式的公钥
    publickey_base64 = """"""
    # 返回值为真即验证通过
    result = DecryptByPublicKey(activation_code, publickey_base64).validity()
    if result:
        # 验证成功要执行的代码
        print("可以用")
    else:
        # 验证失败要执行的代码
        print("不让用")
