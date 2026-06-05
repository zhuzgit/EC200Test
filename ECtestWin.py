import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import serial
import serial.tools.list_ports
import time
import threading

class EC200ATestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quectel EC200A AT 命令高级测试工具")
        self.root.geometry("1000x600") # 略微加宽以容纳更多功能
        
        self.serial_conn = None # 串口长连接句柄
        
        # 初始化默认批量命令列表
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
        left_frame = ttk.Frame(root, padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        right_frame = ttk.Frame(root, padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # --- 左侧面板组件 ---
        # 1. 串口配置（升级为下拉框与独立开关）
        ttk.Label(left_frame, text="串口选择与控制:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=2)
        
        port_action_frame = ttk.Frame(left_frame)
        port_action_frame.pack(fill=tk.X, pady=2)
        
        self.port_combobox = ttk.Combobox(port_action_frame, width=28, state="readonly")
        self.port_combobox.pack(side=tk.LEFT, padx=(0, 5))
        
        self.btn_refresh = ttk.Button(port_action_frame, text="🔄", width=3, command=self.scan_serial_ports)
        self.btn_refresh.pack(side=tk.LEFT)
        
        # 串口打开/关闭独立按钮
        self.btn_toggle_serial = ttk.Button(left_frame, text="🔌 打开串口", command=self.toggle_serial_port)
        self.btn_toggle_serial.pack(fill=tk.X, pady=5)
        
        # 2. 单条指令手动发送区域 (新需求)
        ttk.Label(left_frame, text="单条命令手动发送:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(10, 2))
        single_cmd_frame = ttk.Frame(left_frame)
        single_cmd_frame.pack(fill=tk.X, pady=5)
        
        self.single_cmd_input = ttk.Entry(single_cmd_frame, font=('Consolas', 10))
        self.single_cmd_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.single_cmd_input.bind("<Return>", lambda event: self.send_single_command()) # 支持回车发送
        self.single_cmd_input.insert(0, "AT")
        
        self.btn_send_single = ttk.Button(single_cmd_frame, text="发送", width=6, command=self.send_single_command)
        self.btn_send_single.pack(side=tk.RIGHT)
        
        # 3. 常用网络快捷命令面板 (新需求)
        ttk.Label(left_frame, text="常用网络状态查询 (快捷键):", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(10, 2))
        quick_btn_frame = ttk.Frame(left_frame)
        quick_btn_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(quick_btn_frame, text="网络注册 (CEREG?)", command=lambda: self.send_quick_cmd("AT+CEREG?")).grid(row=0, column=0, sticky="ew", pady=2, padx=2)
        ttk.Button(quick_btn_frame, text="当前运营商 (COPS?)", command=lambda: self.send_quick_cmd("AT+COPS?")).grid(row=0, column=1, sticky="ew", pady=2, padx=2)
        ttk.Button(quick_btn_frame, text="搜索运营商 (COPS=?)", command=lambda: self.send_quick_cmd("AT+COPS=?", timeout=15.0)).grid(row=1, column=0, columnspan=2, sticky="ew", pady=2, padx=2)
        quick_btn_frame.columnconfigure(0, weight=1)
        quick_btn_frame.columnconfigure(1, weight=1)

        # 4. 批量序列命令输入框
        ttk.Label(left_frame, text="批量队列测试 AT 命令 (每行一条):", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(15, 2))
        self.cmd_input = scrolledtext.ScrolledText(left_frame, width=35, height=12, font=('Consolas', 10))
        self.cmd_input.pack(fill=tk.BOTH, expand=True, pady=5)
        self.cmd_input.insert(tk.END, default_cmds)
        
        self.btn_start_batch = ttk.Button(left_frame, text="🚀 顺序执行批量队列", command=self.start_batch_thread)
        self.btn_start_batch.pack(fill=tk.X, pady=2)
        
        # --- 右侧面板组件 ---
        log_header_frame = ttk.Frame(right_frame)
        log_header_frame.pack(fill=tk.X, pady=2)
        ttk.Label(log_header_frame, text="测试日志与回应终端:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        ttk.Button(log_header_frame, text="清空日志", width=8, command=self.clear_log).pack(side=tk.RIGHT)
        
        self.log_output = scrolledtext.ScrolledText(right_frame, font=('Consolas', 10), bg="#1e1e1e", fg="#ffffff")
        self.log_output.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 初始化扫描
        self.scan_serial_ports()

    # --- 基础辅助逻辑 ---
    def log(self, text):
        """线程安全地向右侧日志框追加内容"""
        self.root.after(0, self._safe_log, text)

    def _safe_log(self, text):
        self.log_output.insert(tk.END, text + "\n")
        self.log_output.see(tk.END)

    def clear_log(self):
        self.log_output.delete('1.0', tk.END)

    # --- 串口识别与管理逻辑 ---
    def scan_serial_ports(self):
        """扫描系统所有串口并填充至下拉框"""
        ports = serial.tools.list_ports.comports()
        self.clear_log()
        self.log("===== 开始扫描系统串口 =====")
        
        port_lists = []
        default_index = 0
        
        for idx, port in enumerate(ports):
            display_str = f"{port.device} ({port.description})"
            port_lists.append(display_str)
            self.log(f"发现串口 -> 端口: {port.device} | 详细描述: {port.description}")
            
            # 智能优先匹配包含 AT Port 的第一个项
            if "AT" in port.description and default_index == 0:
                default_index = idx

        if port_lists:
            self.port_combobox['values'] = port_lists
            self.port_combobox.current(default_index)
            self.log(f"\n[提示] 扫描完成。已为您默认选中第 {default_index + 1} 个端口，支持点击下拉框自主切换。")
        else:
            self.port_combobox['values'] = []
            self.port_combobox.set("未检测到任何串口")
            self.log("\n[警告] 未检测到任何活动的串口设备，请检查物理连接。")

    def get_selected_port(self):
        """从选中的下拉框文本中提取物理 COM 号"""
        selected_text = self.port_combobox.get()
        if selected_text and " (" in selected_text:
            return selected_text.split(" (")[0]
        return None

    def toggle_serial_port(self):
        """手动 控制串口的长连接开关"""
        if self.serial_conn and self.serial_conn.is_open:
            # 关串口
            try:
                self.serial_conn.close()
            except:
                pass
            self.serial_conn = None
            self.btn_toggle_serial.config(text="🔌 打开串口")
            self.port_combobox.config(state="readonly")
            self.log("\n[🔒 断开] 串口已手动关闭释放。")
        else:
            # 开串口
            target_port = self.get_selected_port()
            if not target_port:
                messagebox.showerror("错误", "请先选择一个有效的物理串口！")
                return
            try:
                self.serial_conn = serial.Serial(port=target_port, baudrate=115200, timeout=1.5)
                self.btn_toggle_serial.config(text="❌ 关闭串口")
                # 打开后锁定下拉框，防止中途切换端口导致句柄错乱
                self.port_combobox.config(state="disabled")
                self.log(f"\n[🔓 成功] 已成功连接到端口 {target_port}，你可以开始收发 AT 指令。")
            except serial.SerialException as e:
                messagebox.showerror("串口错误", f"无法打开端口 {target_port}, 极可能已被其他工具占用！\n原因: {e}")

    # --- 后台通信执行核心逻辑 ---
    def send_at_core(self, cmd, timeout=1.0):
        """底层的统一发收函数（非阻塞、确保带锁或长连接安全）"""
        if not self.serial_conn or not self.serial_conn.is_open:
            self.log("\n[限制] 操作失败，请先点击顶部按钮【打开串口】！")
            return None
            
        try:
            self.serial_conn.timeout = timeout
            self.serial_conn.flushInput()
            
            self.log(f"\n[发送] ---> {cmd}")
            self.serial_conn.write(f"{cmd}\r\n".encode('utf-8'))
            
            # 稍作延时给模块处理硬件缓冲
            time.sleep(0.1)
            
            # 等待读取
            start_time = time.time()
            resp_accumulator = b""
            while (time.time() - start_time) < timeout:
                if self.serial_conn.in_waiting:
                    resp_accumulator += self.serial_conn.read_all()
                    # 如果读取到了明确的结束符，可以提早断开，优化响应体验
                    if b"OK" in resp_accumulator or b"ERROR" in resp_accumulator:
                        break
                time.sleep(0.05)
                
            if resp_accumulator:
                resp_str = resp_accumulator.decode('utf-8', errors='ignore').strip()
                self.log(f"[回应] :\n{resp_str}")
                return resp_str
            else:
                self.log("[回应] : 无响应 (接收超时)")
                return ""
        except Exception as e:
            self.log(f"[通信异常] : {e}")
            return None

    # --- 按钮派发逻辑 ---
    def send_single_command(self):
        """发送单条手动输入的 AT 核心"""
        cmd = self.single_cmd_input.get().strip()
        if not cmd:
            return
        threading.Thread(target=self.send_at_core, args=(cmd, 2.0), daemon=True).start()

    def send_quick_cmd(self, cmd, timeout=2.0):
        """发送单条一键快捷指令面板"""
        threading.Thread(target=self.send_at_core, args=(cmd, timeout), daemon=True).start()

    def start_batch_thread(self):
        """顺序跑左下角批量列表的调度器"""
        if not self.serial_conn or not self.serial_conn.is_open:
            messagebox.showerror("提示", "执行批量队列前，必须先【打开串口】！")
            return
            
        raw_text = self.cmd_input.get("1.0", tk.END).strip()
        if not raw_text:
            return
            
        commands = [cmd.strip() for cmd in raw_text.split("\n") if cmd.strip()]
        
        self.btn_start_batch.config(state=tk.DISABLED)
        
        def batch_task():
            self.log("\n=================== 开始跑批量队列任务 ===================")
            for cmd in commands:
                t = 4.0 if "QENG" in cmd else 1.5
                self.send_at_core(cmd, timeout=t)
                time.sleep(0.2)
            self.log("\n=================== 批量队列任务全部完毕 ===================")
            self.root.after(0, lambda: self.btn_start_batch.config(state=tk.NORMAL))
            
        threading.Thread(target=batch_task, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = EC200ATestApp(root)
    root.mainloop()