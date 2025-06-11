import socket
import sys
import base64
import os
from typing import Optional, Tuple

MAX_RETRIES =5
INITIAL_TIMEOUT = 1.0
#Initial Timeout (Seconds)

def send_and_receive(socket: socket.socket, address: Tuple[str, int], data: bytes, operation: str) -> Optional[str]:
    #Send packets and receive responses, and implement a timeout retransmission mechanism
    timeout = INITIAL_TIMEOUT
    for retries in range(MAX_RETRIES):
        try:
            socket.sendto(data, address)
            socket.settimeout(timeout)
            response, _ = socket.recvfrom(4096)
            return response.decode().strip()
        except socket.timeout:
            timeout *= 2 #Double the timeout for the next retry
            print(f"Timeout: {operation} request timed out, retrying...")
    print(f"{operation}Failed: The maximum number of retries") 
    return None
#Function to send and receive packets with a timeout mechanism

def download_file(socket: socket.socket, server_address: Tuple[str, int], filename: str) -> bool:
    """下载单个文件的完整流程"""
    print(f"开始下载文件: {filename}")
    
    download_msg = f"DOWNLOAD {filename}"
    response = send_and_receive(socket, server_address, download_msg.encode(), "DOWNLOAD")
    if not response:
        return False
    
    parts = response.split()
    if parts[0] == "ERR":
        print(f"错误: 文件不存在 - {filename}")
        return False
    if parts[0] != "OK" or parts[1] != filename:
        print(f"无效响应: {response}")
        return False
    #Send a DOWNLOAD request