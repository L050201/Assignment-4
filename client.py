import socket
import sys
import base64
import os
import logging
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MAX_RETRIES = 5
INITIAL_TIMEOUT = 1.0

def send_and_receive(socket: socket.socket, address: Tuple[str, int], data: bytes, operation: str) -> Optional[str]:
    """发送数据并接收响应，实现超时重传机制"""
    timeout = INITIAL_TIMEOUT
    for retries in range(MAX_RETRIES):
        try:
            socket.sendto(data, address)
            socket.settimeout(timeout)
            response, _ = socket.recvfrom(4096)
            return response.decode().strip()
        except socket.timeout:
            timeout *= 2  # 指数退避策略
            logging.warning(f"超时: {operation} 请求超时，正在重试...")
    
    logging.error(f"失败: {operation} 达到最大重试次数")
    return None

def download_file(socket: socket.socket, server_address: Tuple[str, int], filename: str) -> bool:
    """从服务器下载单个文件的完整流程"""
    logging.info(f"开始下载文件: '{filename}'")
    
    download_msg = f"DOWNLOAD {filename}"
    response = send_and_receive(socket, server_address, download_msg.encode(), "DOWNLOAD")
    
    if not response:
        logging.error(f"下载失败: 无法获取服务器响应 - {filename}")
        return False
    
    logging.info(f"服务器响应: {response}")
    
    parts = response.split()
    if parts[0] == "ERR":
        logging.error(f"错误: 文件不存在 - {filename}")
        return False
    
    if parts[0] != "OK" or parts[1] != filename:
        logging.error(f"无效响应: {response}")
        return False
    
    # 解析文件大小和数据端口
    try:
        file_size = int(parts[3])
        data_port = int(parts[5])
        logging.info(f"文件大小: {file_size} 字节, 数据端口: {data_port}")
    except (IndexError, ValueError) as e:
        logging.error(f"解析响应失败: {e}, 响应: {response}")
        return False
    
    # 创建并打开文件
    try:
        with open(filename, 'wb') as f:
            block_size = 1000
            total_received = 0
            progress = 0
            
            # 显示进度条
            print(f"下载进度: [{filename}] ", end='', flush=True)
            
            while total_received < file_size:
                start = total_received
                end = min(total_received + block_size - 1, file_size - 1)
                get_msg = f"FILE {filename} GET START {start} END {end}"
                
                data_address = (server_address[0], data_port)
                response = send_and_receive(socket, data_address, get_msg.encode(), "FILE GET")
                
                if not response:
                    logging.error(f"下载失败: 数据传输超时 - {filename}")
                    try:
                        os.remove(filename)  # 删除不完整文件
                    except Exception as e:
                        logging.error(f"删除部分下载文件时出错: {e}")
                    return False
                
                parts = response.split()
                if parts[0] != "FILE" or parts[1] != filename or parts[2] != "OK":
                    logging.error(f"无效数据响应: {response}")
                    continue
                
                try:
                    data_index = parts.index("DATA") + 1
                    base64_data = ' '.join(parts[data_index:])
                    file_data = base64.b64decode(base64_data)
                    
                    f.write(file_data)
                    total_received += len(file_data)
                    
                    # 更新进度条
                    new_progress = int((total_received / file_size) * 20)
                    while progress < new_progress:
                        print("*", end='', flush=True)
                        progress += 1
                except (ValueError, base64.binascii.Error) as e:
                    logging.error(f"数据解码失败: {e}")
    
    except Exception as e:
        logging.error(f"文件操作异常: {e}")
        if os.path.exists(filename):
            os.remove(filename)
        return False
    
    logging.info(f"\n文件下载完成: {filename}")
    
    # 关闭文件连接
    close_msg = f"FILE {filename} CLOSE"
    data_address = (server_address[0], data_port)
    response = send_and_receive(socket, data_address, close_msg.encode(), "CLOSE")
    
    if not response or not response.startswith(f"FILE {filename} CLOSE_OK"):
        logging.warning("警告: 未收到CLOSE_OK响应，连接可能未正常关闭")
    else:
        logging.info("连接已正常关闭")
    
    return True

def main():
    """客户端主函数，解析命令行参数并下载文件列表"""
    if len(sys.argv) != 4:
        logging.error("使用方法: python client.py <主机名> <服务器端口> <文件列表路径>")
        sys.exit(1)
    
    hostname, server_port, file_list_path = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    server_address = (hostname, server_port)
    
    try:
        # 创建UDP套接字
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # 检查文件列表是否存在
        if not os.path.exists(file_list_path):
            logging.error(f"文件列表不存在: {file_list_path}")
            sys.exit(1)
        
        # 读取文件列表
        with open(file_list_path, 'r') as f:
            file_list = [line.strip() for line in f if line.strip()]
        
        if not file_list:
            logging.error(f"文件列表为空: {file_list_path}")
            sys.exit(1)
        
        logging.info(f"开始下载 {len(file_list)} 个文件")
        
        # 逐个下载文件
        for filename in file_list:
            download_file(client_socket, server_address, filename)
    
    except socket.gaierror:
        logging.error(f"主机名解析失败: {hostname}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"程序异常: {e}")
        sys.exit(1)
    finally:
        # 关闭套接字
        try:
            client_socket.close()
        except:
            pass

if __name__ == "__main__":
    main()