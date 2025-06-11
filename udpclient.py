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

def download_file(socket: socket.socket_address: Tuple[str, int], filename: str) -> bool:
#The complete process of downloading a single file from the server