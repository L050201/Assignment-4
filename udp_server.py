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