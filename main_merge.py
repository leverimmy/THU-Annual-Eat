from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
import json
import matplotlib.pyplot as plt
import requests
# import matplotlib.font_manager as fm
import seaborn as sns

def decrypt_aes_ecb(encrypted_data: str) -> str:
    # 密钥取前16个字符
    key = encrypted_data[:16].encode('utf-8')
    encrypted_data = encrypted_data[16:]
    encrypted_data_bytes = base64.b64decode(encrypted_data)
    
    cipher = AES.new(key, AES.MODE_ECB)
    
    decrypted_data = unpad(cipher.decrypt(encrypted_data_bytes), AES.block_size)
    
    return decrypted_data.decode('utf-8')

def aggregate_data(data_rows):
    aggregated = {}
    for item in data_rows:
        try:
            # 提取下划线前的食堂名称
            mername_full = item["mername"]
            mername = mername_full.split('_')[0]
            if mername in aggregated:
                aggregated[mername] += item["txamt"]
            else:
                aggregated[mername] = item["txamt"]
        except Exception as e:
            print(f"Error processing item {item}: {e}")
    # 转换为元并保留两位小数
    aggregated = {k: round(v / 100, 2) for k, v in aggregated.items()}
    return aggregated

def set_chinese_font():
    # 查找系统中可用的中文字体
    chinese_fonts = [f.name for f in fm.fontManager.ttflist if 'SimHei' in f.name or 'Noto Sans CJK SC' in f.name or 'Microsoft YaHei' in f.name]
    
    if 'SimHei' in chinese_fonts:
        plt.rcParams['font.sans-serif'] = ['SimHei']
    elif 'Noto Sans CJK SC' in chinese_fonts:
        plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC']
    elif 'Microsoft YaHei' in chinese_fonts:
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
    else:
        print("警告：未能找到合适的中文字体，请确保系统中已安装中文字体。")
        exit(0)
    
    plt.rcParams['axes.unicode_minus'] = False

def main():
    username = ""
    password = ""
    idserial = ""
    servicehall = ""
    all_data = dict()
    
    # 读入账户信息
    try:
        with open("config.json", "r", encoding='utf-8') as f:
            account = json.load(f)
            username = account["username"]
            password = account["password"]
            idserial = account["idserial"]
            servicehall = account["servicehall"]
    except Exception as e:
        print("账户信息读取失败，请重新输入")
        username = input("请输入用户名: ")
        password = input("请输入密码: ")
        idserial = input("请输入学号: ")
        servicehall = input("请输入服务代码: ")
        with open("config.json", "w", encoding='utf-8') as f:
            json.dump({"username": username, "password": password, "idserial": idserial, "servicehall": servicehall}, f, ensure_ascii=False, indent=4)
    
    # 发送请求，得到加密后的字符串
    url = f"https://card.tsinghua.edu.cn/business/querySelfTradeList?pageNumber=0&pageSize=5000&starttime=2024-01-01&endtime=2024-12-31&idserial={idserial}&tradetype=-1"
    cookie = {
        "servicehall": servicehall,
    }
    
    try:
        response = requests.post(url, cookies=cookie)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return
    
    # 解密字符串
    try:
        encrypted_string = json.loads(response.text)["data"]
        decrypted_string = decrypt_aes_ecb(encrypted_string)
    except Exception as e:
        print(f"解密失败: {e}")
        return
    
    # 整理数据并聚合
    try:
        data = json.loads(decrypted_string)
        all_data = aggregate_data(data["resultData"]["rows"])
    except Exception as e:
        print(f"数据整理失败: {e}")
        return
    
    print(f"总食堂数量: {len(all_data)}")
    
    # 排序
    all_data = dict(sorted(all_data.items(), key=lambda x: x[1], reverse=False))
    
    # 设置中文字体
    # set_chinese_font()
    
    # 使用高级配色方案
    sns.set(style="whitegrid")
    color_palette = sns.color_palette("viridis", len(all_data))
    color_palette.reverse()
    
    # 绘制水平条形图
    plt.figure(figsize=(12, max(6, len(all_data) * 0.3)))  # 动态调整高度
    plt.rcParams['font.sans-serif'] = ['SimHei']
    bars = plt.barh(list(all_data.keys()), list(all_data.values()), color=color_palette)

    # 添加数据标签
    for bar in bars:
        width = bar.get_width()
        plt.text(width + max(all_data.values()) * 0.01, bar.get_y() + bar.get_height()/2,
                 f'{width}', va='center', fontsize=10)
    
    # 设置标题和标签
    plt.title("华清大学食堂消费情况", fontsize=18)
    plt.xlabel("消费金额（元）", fontsize=14)
    plt.ylabel("食堂名称", fontsize=14)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    plt.savefig("result.png", dpi=300, bbox_inches='tight')
    
    # 显示图表
    plt.show()

if __name__ == "__main__":
    main()
