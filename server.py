import socket
import base64
import os
import sys
import threading
import random
import logging
from typing import Tuple, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 配置文件存储目录（修改为实际存储文件的目录）
FILE_DIR = os.getcwd()  # 默认使用当前工作目录
DATA_PORT_RANGE = (50000, 51000)

def handle_client_request(welcome_socket: socket.socket, request: str, client_address: Tuple[str, int]):
    """处理客户端的下载请求，创建数据传输线程"""
    parts = request.strip().split()
    if not (parts and parts[0] == "DOWNLOAD"):
        logging.error(f"无效请求: {request} from {client_address}")
        return
    
    # 处理带空格的文件名
    filename = " ".join(parts[1:])
    file_path = os.path.join(FILE_DIR, filename)
    
    logging.info(f"客户端请求文件: '{filename}', 实际路径: {file_path}")
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        error_msg = f"ERR {filename} NOT_FOUND"
        welcome_socket.sendto(error_msg.encode(), client_address)
        logging.error(f"文件不存在: {file_path}")
        return
    
    if not os.path.isfile(file_path):
        error_msg = f"ERR {filename} NOT_FILE"
        welcome_socket.sendto(error_msg.encode(), client_address)
        logging.error(f"不是有效文件: {file_path}")
        return
    
    # 分配数据端口并发送响应
    data_port = random.randint(*DATA_PORT_RANGE)
    file_size = os.path.getsize(file_path)
    ok_msg = f"OK {filename} SIZE {file_size} PORT {data_port}"
    welcome_socket.sendto(ok_msg.encode(), client_address)
    logging.info(f"准备发送文件: {filename} (大小: {file_size}B, 数据端口: {data_port})")
    
    # 启动数据传输线程
    data_thread = threading.Thread(
        target=handle_data_transmission,
        args=(filename, client_address, data_port)
    )
    data_thread.daemon = True
    data_thread.start()

def handle_data_transmission(filename: str, client_address: Tuple[str, int], data_port: int):
    """处理文件数据的传输"""
    try:
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data_socket.bind(('0.0.0.0', data_port))
        logging.info(f"数据线程已启动: 端口 {data_port}, 文件 {filename}")
        
        file_path = os.path.join(FILE_DIR, filename)
        with open(file_path, 'rb') as f:
            while True:
                try:
                    request, _ = data_socket.recvfrom(4096)
                    request_str = request.decode().strip()
                    logging.info(f"收到数据请求: {request_str}")
                    
                    parts = request_str.split()
                    if not parts or parts[0] != "FILE" or parts[1] != filename:
                        logging.error(f"无效数据请求: {request_str}")
                        continue
                    
                    if parts[2] == "CLOSE":
                        close_msg = f"FILE {filename} CLOSE_OK"
                        data_socket.sendto(close_msg.encode(), client_address)
                        logging.info(f"文件传输完成: {filename}")
                        break
                    
                    elif parts[2] == "GET":
                        try:
                            start = int(parts[4])
                            end = int(parts[6])
                            block_size = end - start + 1
                            
                            f.seek(start)
                            file_data = f.read(block_size)
                            
                            if len(file_data) == block_size:
                                base64_data = base64.b64encode(file_data).decode()
                                response = f"FILE {filename} OK START {start} END {end} DATA {base64_data}"
                                data_socket.sendto(response.encode(), client_address)
                            else:
                                logging.error(f"读取数据块失败: 期望 {block_size}B, 实际 {len(file_data)}B (位置: {start})")
                        except (IndexError, ValueError) as e:
                            logging.error(f"请求解析失败: {e}, 请求: {request_str}")
                except socket.timeout:
                    continue
                except Exception as e:
                    logging.error(f"数据传输异常: {e}")
                    break
    except Exception as e:
        logging.error(f"数据线程异常: {e}")
    finally:
        try:
            data_socket.close()
        except:
            pass

def main():
    """服务器主函数，解析命令行参数并启动监听"""
    if len(sys.argv) != 2:
        logging.error("使用方法: python server.py <监听端口>")
        sys.exit(1)
    
    server_port = int(sys.argv[1])
    
    try:
        welcome_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        welcome_socket.bind(('0.0.0.0', server_port))
        welcome_socket.settimeout(1.0)
        logging.info(f"服务器已启动: 监听端口 {server_port}")
        
        while True:
            try:
                data, client_address = welcome_socket.recvfrom(1024)
                request = data.decode().strip()
                
                # 为每个请求创建新线程处理
                client_thread = threading.Thread(
                    target=handle_client_request,
                    args=(welcome_socket, request, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                logging.error(f"服务器异常: {e}")
    except Exception as e:
        logging.error(f"程序异常: {e}")
    finally:
        try:
            welcome_socket.close()
        except:
            pass

if __name__ == "__main__":
    main()