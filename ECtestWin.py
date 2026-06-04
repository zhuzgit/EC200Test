import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import serial
import serial.tools.list_ports
import time
import threading

class EC200ATestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quectel EC200A AT 命令测试工具")
        self.root.geometry("850x550")
        
        # 初始化默认命令列表
        default_cmds = (
            "AT+QGMR\n"
            "AT+QICSGP=1\n"
            "AT+CFUN?\n"
            "AT+CPIN?\n"
            "AT+QENG=\"SERVINGCELL\"\n"
            "AT+QCFG=\"band\"\n"
            "AT+QCFG=\"nwscanmode\""
        )
        
        # --- 布局：左右分栏 ---
        # 左侧面板（参数配置与命令输入）
        left_frame = ttk.Frame(root, padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # 右侧面板（显示测试日志）
        right_frame = ttk.Frame(root, padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # --- 左侧组件 ---
        # 1. 串口信息
        ttk.Label(left_frame, text="串口选择 (描述含 'AT Port'):", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=2)
        self.port_label = ttk.Label(left_frame, text="正在检测串口...", foreground="blue")
        self.port_label.pack(anchor=tk.W, pady=5)
        
        # 2. 命令输入框
        ttk.Label(left_frame, text="待发送的 AT 命令 (每行一条):", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(10, 2))
        self.cmd_input = scrolledtext.ScrolledText(left_frame, width=35, height=18, font=('Consolas', 10))
        self.cmd_input.pack(fill=tk.BOTH, expand=True, pady=5)
        self.cmd_input.insert(tk.END, default_cmds)
        
        # 3. 控制按钮
        self.btn_refresh = ttk.Button(left_frame, text="重新扫描串口", command=self.scan_serial_port)
        self.btn_refresh.pack(fill=tk.X, pady=2)
        
        self.btn_start = ttk.Button(left_frame, text="🚀 开始测试", command=self.start_test_thread)
        self.btn_start.pack(fill=tk.X, pady=5)
        
        # --- 右侧组件 ---
        ttk.Label(right_frame, text="测试日志与回应:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=2)
        # 🛠️ 已修正：将 fill 和 expand 从组件初始化移出
        self.log_output = scrolledtext.ScrolledText(right_frame, font=('Consolas', 10), bg="#1e1e1e", fg="#ffffff")
        self.log_output.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 启动时先扫描一次串口
        self.detected_port = None
        self.scan_serial_port()

    def log(self, text):
        """向右侧日志框追加内容"""
        self.log_output.insert(tk.END, text + "\n")
        self.log_output.see(tk.END)  # 自动滚动到最下方

    def clear_log(self):
        """清空日志"""
        self.log_output.delete('1.0', tk.END)

    def scan_serial_port(self):
        """扫描并自动匹配含有 AT Port 的串口"""
        self.detected_port = None
        ports = serial.tools.list_ports.comports()
        
        self.clear_log()
        self.log("===== 正在扫描系统串口 =====")
        
        for port in ports:
            self.log(f"发现串口: {port.device} | 描述: {port.description}")
            if "AT Port" in port.description:
                self.detected_port = port.device
                
        if self.detected_port:
            self.port_label.config(text=f"已自动匹配: {self.detected_port}", foreground="green")
            self.log(f"\n[提示] 成功锁定目标端口: {self.detected_port}")
        else:
            self.port_label.config(text="未找到 'AT Port' 模块", foreground="red")
            self.log("\n[警告] 未找到描述包含 'AT Port' 的串口，请检查驱动连接，或点击刷新。")

    def start_test_thread(self):
        """使用多线程运行测试，防止点击按钮后界面卡死"""
        if not self.detected_port:
            messagebox.showerror("错误", "未检测到有效的 EC200A AT 端口，无法开始测试！")
            return
        
        # 禁用按钮，防止重复点击
        self.btn_start.config(state=tk.DISABLED)
        self.btn_refresh.config(state=tk.DISABLED)
        
        # 开启新线程跑后台测试
        t = threading.Thread(target=self.run_at_commands)
        t.daemon = True
        t.start()

    def run_at_commands(self):
        """后台执行 AT 命令的具体逻辑"""
        self.clear_log()
        self.log(f"正在打开串口 {self.detected_port}...\n" + "="*50)
        
        # 获取输入框中的所有命令
        raw_text = self.cmd_input.get("1.0", tk.END).strip()
        if not raw_text:
            self.log("[错误] 输入框中没有命令。")
            self.reset_buttons()
            return
            
        commands = [cmd.strip() for cmd in raw_text.split("\n") if cmd.strip()]

        try:
            # 打开串口
            ser = serial.Serial(port=self.detected_port, baudrate=115200, timeout=2)
            ser.flushInput()
            
            for cmd in commands:
                self.log(f"\n[发送] ---> {cmd}")
                ser.write(f"{cmd}\r\n".encode('utf-8'))
                
                # 根据命令类型决定等待时长（QENG基站查询稍慢）
                wait_time = 2.0 if "QENG" in cmd else 1.0
                time.sleep(wait_time)
                
                # 读取回应
                if ser.in_waiting:
                    resp = ser.read_all().decode('utf-8', errors='ignore')
                    self.log(f"[回应] :\n{resp.strip()}")
                else:
                    self.log("[回应] : 无响应 (超时)")
            
            ser.close()
            self.log("\n" + "="*50 + "\n[成功] 所有命令测试完毕，串口已关闭。")
            
        except serial.SerialException as e:
            self.log(f"\n[串口错误] 无法操作该串口: {e}")
        except Exception as e:
            self.log(f"\n[未知错误] {e}")
            
        self.reset_buttons()

    def reset_buttons(self):
        """恢复按钮点击状态"""
        self.btn_start.config(state=tk.NORMAL)
        self.btn_refresh.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = EC200ATestApp(root)
    root.mainloop()