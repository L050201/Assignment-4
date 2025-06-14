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

        with open(filename, 'rb') as f:
            buffer_size = 4096
            while True:
                try:
                    request, _ = data_socket.recvfrom(buffer_size)
                    request_str = request.decode().strip()
                    print(f"收到数据请求: {request_str} from {client_address}")
                    
                    parts = request_str.split()
                    if not parts or parts[0] != "FILE" or parts[1] != filename:
                        print(f"无效数据请求: {request_str}")
                        continue
                    # Receive client request 

                    if parts[2] == "CLOSE":
                        close_msg = f"FILE {filename} CLOSE_OK"
                        data_socket.sendto(close_msg.encode(), client_address)
                        print(f"文件传输完成: {filename} (客户端: {client_address})")
                        break
                    # Handle closure requests

                    elif parts[2] == "GET":
                        try:
                            start = int(parts[4])
                            end = int(parts[6])
                            block_size = end - start + 1
                         # Process data block requests

                            f.seek(start)
                            file_data = f.read(block_size)
                            
                            if len(file_data) == block_size:
                               # Encode the data in Base64 and construct the response.
                                base64_data = base64.b64encode(file_data).decode()
                                response = f"FILE {filename} OK START {start} END {end} DATA {base64_data}"
                                data_socket.sendto(response.encode(), client_address)
                            else:
                                print(f"Failed to read the data block: Expectation {block_size}B, Actual {len(file_data)}B (location: {start})")
                        except (IndexError, ValueError) as e:
                            print(f"Request parsing failed: {e}, request: {request_str}") 

                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Data transmission anomaly: {e}")
                    break
        
    except Exception as e:
        print(f"Data thread exception: {e}")
    finally:
        try:
            data_socket.close()
        except:
            pass
        # Close the data socket and release the port.
def main():
    """Main function: Start the server and listen for client requests"""
    if len(sys.argv) != 2:
        print("Usage: python3 udp_server.py <Listening port>")
        sys.exit(1)
    
    server_port = int(sys.argv[1])
    try:
        #Create a welcome socket and start listening.
        welcome_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        welcome_socket.bind(('0.0.0.0', server_port))
        welcome_socket.settimeout(1.0)  # Set a timeout for receiving requests
        print(f"Server started: Listening on port {server_port}") 

        while True:
            try:
                data, client_address = welcome_socket.recvfrom(1024)
                request = data.decode().strip()
                #Create a new thread for each client request.
                client_thread = threading.Thread(
                    target=handle_client_request,
                    args=(welcome_socket, request, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Server exception: {e}") 
                # Main loop: Receive client requests and allocate threads for processing. 
                 
    except Exception as e:
        print(f"Program exception: {e}")
    finally:
        try:
            welcome_socket.close()
        except:
            pass

if __name__ == "__main__":
    main() 
 # When the script is run as the main program, call the main() function                  