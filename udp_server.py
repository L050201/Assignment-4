import socket
import base64
import os
import sys
import threading
import random
from typing import Tuple, Optional

DATA_PORT_RANGE = (50000, 51000)  # range of ports to use for data transfer