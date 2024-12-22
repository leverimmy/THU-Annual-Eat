# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "pycryptodome",
# ]
# ///

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
import json
import requests

def decrypt_aes_ecb(encrypted_data: str) -> str:
    
    key = encrypted_data[:16].encode('utf-8')
    encrypted_data = encrypted_data[16:]
    encrypted_data_bytes = base64.b64decode(encrypted_data)
    
    cipher = AES.new(key, AES.MODE_ECB)
    
    decrypted_data = unpad(cipher.decrypt(encrypted_data_bytes), AES.block_size)

    return decrypted_data.decode('utf-8')

idserial = ""
servicehall = ""
all_data = dict()

if __name__ == "__main__":
    # 读入账户信息
    try:
        with open("config.json", "r", encoding='utf-8') as f:
            account = json.load(f)
            idserial = account["idserial"]
            servicehall = account["servicehall"]
    except Exception as e:
        print("账户信息读取失败，请重新输入")
        idserial = input("请输入学号: ")
        servicehall = input("请输入服务代码: ")
        with open("config.json", "w", encoding='utf-8') as f:
            json.dump({"idserial": idserial, "servicehall": servicehall}, f, indent=4)
    
    # 发送请求，得到加密后的字符串
    url = f"https://card.tsinghua.edu.cn/business/querySelfTradeList?pageNumber=0&pageSize=5000&starttime=2024-01-01&endtime=2024-12-31&idserial={idserial}&tradetype=-1"
    cookie = {
        "servicehall": servicehall,
    }
    response = requests.post(url, cookies=cookie)

    # 解密字符串
    try:
        encrypted_string = json.loads(response.text)["data"]
    except Exception as e:
        print("账户信息好像过期了。你需要再登陆 https://card.tsinghua.edu.cn/userselftrade 获得一个新的服务代码，然后修改 config.json 文件，把 servicehall 的值改成新的服务代码。")
        raise e
        
    decrypted_string = decrypt_aes_ecb(encrypted_string)

    # 整理数据
    data = json.loads(decrypted_string)["resultData"]["rows"]
    data = [{
        "name": item["mername"],
        "place": item["meraddr"],
        "date": item["txdate"],
        "value": item["txamt"],
        "balance": item["balance"],
        "cardno": item["cardno"],
    } for item in data if ("mername" in item)]
    with open("output.js", "w", encoding='utf-8') as f:
        f.write("const raw = ")
        json.dump(data, f, indent=4, ensure_ascii=False)
