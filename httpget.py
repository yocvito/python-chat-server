import sys
import socket

max_buff_len = 1024

host = sys.argv[1]
port = 80

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect((host, port))
except Exception as e:
    print(e)
    exit(1)

request = "GET / HTTP/1.1\r\n"  \
    "Host: " + host + "\r\n"    \
    "Connection: close\r\n\r\n"

s.sendall(request.encode("utf-8"))
while True:
    data = s.recv(max_buff_len)
    if data == b'':
        break
    print(data.decode("utf-8"), end="")


