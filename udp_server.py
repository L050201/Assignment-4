import socket
import base64
import os
import sys
import threading
import random
from typing import Tuple, Optional

DATA_PORT_RANGE = (50000, 51000)  # range of ports to use for data transfer

def handle_client_request(welcome_socket: socket.socket, request: str, client_address: Tuple[str, int]):
    #Handle the client's download request and create a new thread to manage data transfer.
    parts = request.split()
    if not (parts and parts[0] == "DOWNLOAD" and len(parts) >= 2):
        print(f"无效请求: {request} from {client_address}")
        return
    
    filename = parts[1]
    file_path = os.path.abspath(filename)

    if not os.path.exists(file_path) or os.path.isdir(file_path):
        error_msg = f"ERR {filename} NOT_FOUND"
        welcome_socket.sendto(error_msg.encode(), client_address)
        print(f"文件不存在: {filename} (请求来自: {client_address})")
        return
    #Check if the file exists

    data_port = random.randint(*DATA_PORT_RANGE)
    file_size = os.path.getsize(file_path)
    ok_msg = f"OK {filename} SIZE {file_size} PORT {data_port}"
    welcome_socket.sendto(ok_msg.encode(), client_address)
    
    print(f"Ready to send the document: {filename} (Size:{file_size}B,Data port : {data_port}, Client: {client_address})")
    data_thread = threading.Thread(
        target=handle_data_transmission,
        args=(filename, client_address, data_port)
    )
    data_thread.daemon = True
    data_thread.start()
    #Assign random data ports and start data transmission threads.

def handle_data_transmission(filename: str, client_address: Tuple[str, int], data_port: int):
    """Thread function for handling file data transmission"""
    try:
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data_socket.bind(('0.0.0.0', data_port))
        print(f"Data thread started: Port {data_port}, Document {filename}") 
        # Create a UDP socket for the data port   