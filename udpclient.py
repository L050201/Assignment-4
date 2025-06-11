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
    #The complete process of downloading a single file from the server
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

    file_size = int(parts[3])
    data_port = int(parts[5])
    data_address = (server_address[0], data_port)
    print(f"文件大小: {file_size} 字节, 数据端口: {data_port}")
    # The parsing response gets the file size and data port

    with open(filename, 'wb') as f:
        block_size = 1000
        total_received = 0
        progress = 0
        
        while total_received < file_size:
            start = total_received
            end = min(total_received + block_size - 1, file_size - 1)
            #Create a file for writing

            get_msg = f"FILE {filename} GET START {start} END {end}"
            response = send_and_receive(socket, data_address, get_msg.encode(), "FILE GET")
            if not response:
                OS.remove(filename) #Delete the partially downloaded file
                return False
            #Send a FILE GET request to the data port

            parts = response.split()
            if parts[0] != "FILE" or parts[1] != filename or parts[2] != "OK":
                print(f"Invalid data response: {response}")
                continue
            #SEND A FILE GET REQUEST TO THE DATA PORT

            try:
                data_index = parts.index("DATA") + 1
                base64_data = ' '.join(parts[data_index:])
                file_data = base64.b64decode(base64_data)
                f.write(file_data)
                total_received += len(file_data)

                new_progress = int((total_received / file_size) * 20)
                while progress < new_progress:
                    print("*", end='', flush=True)
                    progress += 1
            except (ValueError, base64.binascii.Error) as e:
                print(f"Data decoding failed: {e}")
        
        print(f"\nThe file download is complete: {filename}")
        #Extract and decode Base64 data and write to file

        close_msg = f"FILE {filename} CLOSE"
        response = send_and_receive(socket, data_address, close_msg.encode(), "CLOSE")
        if not response or not response.startswith(f"FILE {filename} CLOSE_OK"):
            print("Warning: No CLOSE_OK response was received and the connection may not be closed gracefully")
        else:
            print("The connection has been closed gracefully")
        return True
        #Send a FILE CLOSE request to the data port and check the response

