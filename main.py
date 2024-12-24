from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
import json
import matplotlib
import matplotlib.pyplot as plt
import requests
import platform

# https://stackoverflow.com/a/79298983/13688160
from matplotlib.font_manager import get_font_names
def font_exists(name):
    return name in get_font_names()

# https://superuser.com/a/1866863/1677998
from fontTools.ttLib import TTFont
def chars_in_cmap(unicode_chars, cmap):
    for char in unicode_chars:
        if ord(char) not in cmap.cmap:
            return False
    return True
def chars_in_font(unicode_chars, path):
    if path.endswith('.ttf'):
        font = TTFont(path)
    elif path.endswith('.ttc'):
        # https://github.com/fonttools/fonttools/issues/541
        font = TTFont(path, fontNumber=0)
    else:
        return False
    for cmap in font['cmap'].tables:
        if cmap.isUnicode():
            if chars_in_cmap(unicode_chars, cmap):
                return True
    return False

from matplotlib.font_manager import findSystemFonts
def find_font_containing(unicode_chars):
    for path in findSystemFonts(fontpaths=None, fontext='ttf'):
        if chars_in_font(unicode_chars, path):
            return path
    return None

if platform.system() == "Darwin":
    preferred_font = 'Arial Unicode MS'
elif platform.system() == "Linux":
    preferred_font = 'Droid Sans Fallback'
else:
    preferred_font = 'SimHei'
if font_exists(preferred_font):
    font = preferred_font
else:
    print(preferred_font + ' not found')
    print('Searching for an alternative font...')
    path = find_font_containing(u'汉字')
    font = matplotlib.font_manager.FontProperties(fname=path).get_name()
    print('Using ' + font)
plt.rcParams['font.sans-serif'] = [font]


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
    encrypted_string = json.loads(response.text)["data"]
    decrypted_string = decrypt_aes_ecb(encrypted_string)

    # 整理数据
    data = json.loads(decrypted_string)
    for item in data["resultData"]["rows"]:
        try:
            if item["mername"] in all_data:
                all_data[item["mername"]] += item["txamt"]
            else:
                all_data[item["mername"]] = item["txamt"]
        except Exception as e:
            pass
    all_data = {k: round(v / 100, 2) for k, v in all_data.items()} # 将分转换为元，并保留两位小数
    print(len(all_data))
    # 输出结果
    all_data = dict(sorted(all_data.items(), key=lambda x: x[1], reverse=False))
    plt.figure(figsize=(12, len(all_data) / 66 * 18))
    plt.barh(list(all_data.keys()), list(all_data.values()))
    for index, value in enumerate(list(all_data.values())):
        plt.text(value + 0.01 * max(all_data.values()),
                index,
                str(value),
                va='center')
        
    # plt.tight_layout()
    plt.xlim(0, 1.2 * max(all_data.values()))
    plt.title(f"华清大学食堂消费情况（共计{sum(all_data.values())}元）")
    plt.xlabel("消费金额（元）")
    plt.savefig("result.png")
    plt.show()
