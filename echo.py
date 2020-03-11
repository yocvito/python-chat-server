import socket
import sys

def usage(cmd):
    print("Usage: {} <mode=tcp|udp>".format(cmd))


def tcp_serv(port):
    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(('', port))
    except Exception as e:
        print(e)
        exit(1)

    s.listen(5)
    try:
        while True:
            client, addr = s.accept()
            print("{} is connected on port {}".format(addr, port))
            while True:
                data = client.recv(max_buff_len)
                if data != b"":
                    client.send(data)
                else:
                    print("{} disconnected".format(addr))
                    client.close()
                    break
    except KeyboardInterrupt:
        exit(1)

def udp_serv(port):
    s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, 0)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(('', port))
    except Exception as e:
        print(e)
        exit(1)
    try:
        while True:
            data, addr = s.recvfrom(max_buff_len)
            print("data from {}".format(addr))
            s.sendto(data, addr)
    except KeyboardInterrupt:
        exit(1)

max_buff_len = 1500

port = 7777

if len(sys.argv) > 2 or len(sys.argv) < 1:
    usage(sys.argv[0])

if len(sys.argv) == 1:
    tcp_serv(port)
else:
    mode = sys.argv[1]
    if sys.argv[1] == "tcp":
        tcp_serv(port)
    elif sys.argv[1] == "udp":
        udp_serv(port)
    else:
        usage(sys.argv[0])