from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
import json
import matplotlib.pyplot as plt
import requests
import platform
from collections import defaultdict
import datetime

def decrypt_aes_ecb(encrypted_data: str) -> str:
    key = encrypted_data[:16].encode('utf-8')
    encrypted_data = encrypted_data[16:]
    encrypted_data_bytes = base64.b64decode(encrypted_data)
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted_data = unpad(cipher.decrypt(encrypted_data_bytes), AES.block_size)
    return decrypted_data.decode('utf-8')

idserial = ""
servicehall = ""
all_data = defaultdict(float)  # 商家数据
canteen_data = defaultdict(float)  # 食堂分类数据
quarter_data = defaultdict(lambda: defaultdict(float))  # 季度数据

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
    
    # 分季度查询并处理数据
    quarters = [
        ("2024-01-01", "2024-03-31"),
        ("2024-04-01", "2024-06-30"),
        ("2024-07-01", "2024-09-30"),
        ("2024-10-01", "2024-12-31")
    ]
    
    for starttime, endtime in quarters:
        url = f"https://card.tsinghua.edu.cn/business/querySelfTradeList?pageNumber=0&pageSize=5000&starttime={starttime}&endtime={endtime}&idserial={idserial}&tradetype=-1"
        cookie = {"servicehall": servicehall}
        response = requests.post(url, cookies=cookie)

        # 解密字符串
        encrypted_string = json.loads(response.text)["data"]
        decrypted_string = decrypt_aes_ecb(encrypted_string)

        # 整理数据
        data = json.loads(decrypted_string)
        for item in data["resultData"]["rows"]:
            try:
                mername = item["mername"]
                txamt = item["txamt"] / 100  # 将分转换为元
                all_data[mername] += txamt
                # 按食堂名称分类
                canteen_name = mername.split('_')[0]
                canteen_data[canteen_name] += txamt
                # 按季度分类
                quarter_data[f"{starttime} - {endtime}"][canteen_name] += txamt
            except Exception as e:
                pass

    # 绘制按食堂分类的扇形图
    canteen_data = dict(sorted(canteen_data.items(), key=lambda x: x[1], reverse=True))
    plt.figure(figsize=(8, 8))
    if platform.system() == "Darwin":
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
    elif platform.system() == "Linux":
        plt.rcParams['font.family'] = ['Droid Sans Fallback', 'DejaVu Sans']
    else:
        plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.pie(list(canteen_data.values()), labels=list(canteen_data.keys()), autopct='%1.1f%%', startangle=140)
    plt.title("华清大学食堂消费分布")
    plt.savefig("canteen_pie_chart.png")
    plt.show()

    # 输出按季度最喜欢去的食堂
    for quarter, data in quarter_data.items():
        # 找出消费最多的食堂
        favorite_canteen = max(data, key=data.get)
        print(f"在 {quarter} 期间，最喜欢去的食堂是：{favorite_canteen}，消费金额为：{round(data[favorite_canteen], 2)}元")

    # 绘制每个商家的消费图
    all_data = dict(sorted(all_data.items(), key=lambda x: x[1], reverse=False))
    plt.figure(figsize=(12, len(all_data) / 66 * 18))
    if platform.system() == "Darwin":
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
    elif platform.system() == "Linux":
        plt.rcParams['font.family'] = ['Droid Sans Fallback', 'DejaVu Sans']
    else:
        plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.barh(list(all_data.keys()), list(all_data.values()))
    for index, value in enumerate(list(all_data.values())):
        plt.text(value + 0.01 * max(all_data.values()), index, str(round(value, 2)), va='center')
    plt.xlim(0, 1.2 * max(all_data.values()))
    plt.title("华清大学食堂消费情况")
    plt.xlabel("消费金额（元）")
    plt.savefig("merchant_result.png")
    plt.show()
