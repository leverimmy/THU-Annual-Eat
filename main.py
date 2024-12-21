import argparse
import base64
import json
import platform

import matplotlib.pyplot as plt
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


def decrypt_aes_ecb(encrypted_data: str) -> str:

    key = encrypted_data[:16].encode('utf-8')
    encrypted_data = encrypted_data[16:]
    encrypted_data_bytes = base64.b64decode(encrypted_data)

    cipher = AES.new(key, AES.MODE_ECB)

    decrypted_data = unpad(cipher.decrypt(encrypted_data_bytes), AES.block_size)

    return decrypted_data.decode('utf-8')


def aggregate_cafeteria(data: dict) -> dict:
    """
    Aggregate data and show the results by cafeteria instead of windows.

    """
    new_data = {}
    for k in data.keys():
        try:
            cafe_name = k.split("_")[0]

        except Exception as e:
            cafe_name = k
        new_data[cafe_name] = new_data.get(cafe_name, 0) + data[k]
    return new_data


idserial = ""
servicehall = ""
all_data = dict()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--by_cafe",
        action='store_true',
        help="Aggregate data by cafeteria instead of windows.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
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

    if args.by_cafe:
        all_data = aggregate_cafeteria(all_data)

    all_data = {
        k: round(v / 100, 2) for k, v in all_data.items()
    }  # 将分转换为元，并保留两位小数
    # print(len(all_data))

    # 输出结果
    all_data = dict(sorted(all_data.items(), key=lambda x: x[1], reverse=False))
    if platform.system() == "Darwin":
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
    else:
        plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.figure(figsize=(12, len(all_data) / 66 * 18))
    plt.barh(list(all_data.keys()), list(all_data.values()))
    for index, value in enumerate(list(all_data.values())):
        plt.text(value + 0.01 * max(all_data.values()), index, str(value), va='center')

    # plt.tight_layout()
    plt.xlim(0, 1.2 * max(all_data.values()))
    plt.title("华清大学食堂消费情况")
    plt.xlabel("消费金额（元）")
    plt.savefig("result.png")
    # plt.show()
