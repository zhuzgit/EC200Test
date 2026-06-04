import serial
import serial.tools.list_ports
import time

def find_at_port():
    """自动寻找串口描述中包含 'AT Port' 的端口"""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # 打印发现的所有串口，方便调试
        print(f"发现串口: {port.device} - 描述: {port.description}")
        if "AT Port" in port.description:
            print(f"--> 成功匹配到 EC200A AT 端口: {port.device}")
            return port.device
    return None

def send_at_command(ser, command, timeout=1.5):
    """向模块发送 AT 命令并获取返回结果"""
    print(f"\n[执行命令] ---> {command}")
    
    # 清空缓冲区，确保数据干净
    ser.flushInput()
    
    # 写入命令（记得加回车换行）
    ser.write(f"{command}\r\n".encode('utf-8'))
    
    # 等待模块处理（部分查询命令如 QENG 需要稍长一点的时间）
    time.sleep(timeout)
    
    # 读取返回数据
    if ser.in_assigned_buffers if hasattr(ser, 'in_assigned_buffers') else ser.in_waiting:
        response = ser.read_all().decode('utf-8', errors='ignore')
        print(f"[模块回应] :\n{response.strip()}")
    else:
        print("[模块回应] : 无响应 (Timeout)")

def run_quectel_test():
    # 1. 自动寻找 AT 端口
    at_port = find_at_port()
    
    if not at_port:
        print("\n[错误] 未找到描述中包含 'AT Port' 的串口！")
        print("请检查模块驱动是否安装成功，或手动修改代码中的端口号。")
        return

    # 2. 准备执行的命令列表
    commands = [
        "AT",                         # 握手测试
        "AT+QGMR",                    # 查询固件版本号
        "AT+QICSGP=1",                # 查询或配置当前 Context 的 APN 参数
        "AT+CFUN?",                   # 查询当前的在线状态/全功能状态 (1为正常)
        "AT+CPIN?",                   # 查询 SIM 卡状态 (READY为正常)
        'AT+QENG="SERVINGCELL"',      # 查询当前服务小区的详细网络信息（基站、信号等）
        'AT+QCFG="band"',             # 查询当前频段配置
        'AT+QCFG="nwscanmode"'        # 查询网络搜索模式（如：仅LTE、仅GSM、自动等）
    ]

    try:
        # 3. 打开串口 (EC200A 默认波特率通常为 115200)
        ser = serial.Serial(port=at_port, baudrate=115200, timeout=2)
        print(f"\n已成功建立连接 {at_port}，开始测试...\n" + "="*40)
        
        # 4. 循环执行所有命令
        for cmd in commands:
            # 针对需要基站搜索或较慢的命令，稍微延长等待时间
            current_timeout = 2.0 if "QENG" in cmd else 1.0
            send_at_command(ser, cmd, timeout=current_timeout)
            
        # 5. 关闭串口
        ser.close()
        print("\n" + "="*40 + "\n所有测试命令执行完毕，串口已安全关闭。")

    except serial.SerialException as e:
        print(f"\n[串口错误] 无法打开或操作串口 {at_port}: {e}")
    except Exception as e:
        print(f"\n[未知错误] {e}")

if __name__ == "__main__":
    run_quectel_test()