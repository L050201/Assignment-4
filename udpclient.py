import socket
import sys
import base64
import os
from typing import Optional, Tuple

MAX_RETRIES =5
INITIAL_TIMEOUT = 1.0
#Initial Timeout (Seconds)