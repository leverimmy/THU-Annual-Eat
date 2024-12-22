from tkinter import *
from tkinter.ttk import *
import platform
import ctypes

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
import json
import requests

class I_dont_know_what_is_a_good_name_for_this_fucking_gui_class_only_used_once(Tk):
    def __init__(self, idserial, servicehall, serverid):
        super().__init__()
        self.title("THU Eating")
        self.tk_idserial    = StringVar(master=self, value=idserial)
        self.tk_servicehall = StringVar(master=self, value=servicehall)
        self.tk_serverid    = StringVar(master=self, value=serverid)

        self.bottom_frame = Frame(self)
        self.input_frame  = Frame(self.bottom_frame)
        Label(self.input_frame, text="学号:")       .grid(row=0, column=0, sticky="e")
        Label(self.input_frame, text="servicehall:").grid(row=1, column=0, sticky="e")
        Label(self.input_frame, text="serverid:")   .grid(row=2, column=0, sticky="e")
        Entry(self.input_frame, width=30, textvariable=self.tk_idserial)   .grid(row=0, column=1)
        Entry(self.input_frame, width=30, textvariable=self.tk_servicehall).grid(row=1, column=1)
        Entry(self.input_frame, width=30, textvariable=self.tk_serverid)   .grid(row=2, column=1)
        self.input_frame.pack(side="left")

        Button(self.bottom_frame, text="run script", command=self.on_button_clicked).pack(side="right")
        self.bottom_frame.pack(fill="x",side="bottom", padx=20, pady=20)

        self.plt_canvas = FigureCanvasTkAgg(plt.figure(), master=self)
        self.plt_canvas.get_tk_widget().pack(fill="both", side="top", expand=True)
        self.plt_toolbar = NavigationToolbar2Tk(self.plt_canvas, self)
        self.plt_toolbar.update()
        

    def on_button_clicked(self):
        idserial    = self.tk_idserial   .get()
        servicehall = self.tk_servicehall.get()
        serverid    = self.tk_serverid   .get()

        with open("config.json", "w", encoding='utf-8') as f:
                json.dump({"idserial": idserial, "servicehall": servicehall, "serverid":serverid}, f, indent=4)
        print("running script")
        process_data(idserial, servicehall, serverid)
        self.plt_canvas.draw()



def decrypt_aes_ecb(encrypted_data: str) -> str:
    
    key = encrypted_data[:16].encode('utf-8')
    encrypted_data = encrypted_data[16:]
    encrypted_data_bytes = base64.b64decode(encrypted_data)
    
    cipher = AES.new(key, AES.MODE_ECB)
    
    decrypted_data = unpad(cipher.decrypt(encrypted_data_bytes), AES.block_size)

    return decrypted_data.decode('utf-8')


def process_data(idserial, servicehall, serverid):
    all_data = dict()
    url = f"https://card.tsinghua.edu.cn/business/querySelfTradeList?pageNumber=0&pageSize=5000&starttime=2024-01-01&endtime=2024-12-31&idserial={idserial}&tradetype=-1"
    cookie = {
        "servicehall": servicehall,
        "serverid": serverid,
    }
    response = requests.post(url, cookies=cookie)
    # 解密字符串
    try:
        encrypted_string = json.loads(response.text)["data"]
    except json.decoder.JSONDecodeError as e:
        if "登录" in response.text: # 如果填入的服务代码无效，就会获得一个在线服务系统的登录页面
            print("登录失败，你需要重新获取服务代码")
            return
        else:
            print("未知错误")
            raise e
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
    if platform.system() == "Darwin":
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
    elif platform.system() == "Linux":
        plt.rcParams['font.family'] = ['Droid Sans Fallback', 'DejaVu Sans']
    else:
        plt.rcParams['font.sans-serif'] = ['SimHei']
        
    # plt.figure(figsize=(12, len(all_data) / 66 * 18))
    plt.barh(list(all_data.keys()), list(all_data.values()))
    for index, value in enumerate(list(all_data.values())):
        plt.text(value + 0.01 * max(all_data.values()),
                index,
                str(value),
                va='center')
        
    # plt.tight_layout()
    plt.xlim(0, 1.2 * max(all_data.values()))
    plt.title("华清大学食堂消费情况")
    plt.xlabel("消费金额（元）")


if __name__ == "__main__":
    # 读入账户信息
    idserial = ""; servicehall = ""; serverid = ""
    try:
        with open("config.json", "r", encoding='utf-8') as f:
            account = json.load(f)
            idserial = account["idserial"]; servicehall = account["servicehall"]; serverid = account["serverid"]
    except Exception as _:
        print("未正确读取到账户信息")
    
    # 适配高分屏
    match platform.system():
        case "Windows":
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        case "Darwin":  # 等待补充
            pass
        case "Linux":
            pass
    # 创建窗口
    window = I_dont_know_what_is_a_good_name_for_this_fucking_gui_class_only_used_once(idserial, servicehall, serverid)
    window.mainloop()
