import socket

max_buf_len = 1024
host = "time-c.nist.gov"
port = 13

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))
data = s.recv(max_buf_len)
print(data)

s.close()