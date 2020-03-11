import socket
import sys
import select


class Client:
    """
    class Client of tcp chat server
    socket  the socket connection with client
    nick    the nickname of the client
    """

    def __init__(self, socket, nick):
        """
        init CLient object
        :param socket: the socket connection with client
        :param nick: the nickname of the client, (default = socket addr:port)
        """
        self.socket = socket
        if nick:
            self.nick = nick
        else:
            self.nick = socket.getpeername()

    def getsocket(self):
        return self.socket

    def getnick(self):
        return self.nick

    def setsocket(self, socket):
        self.socket = socket

    def setnick(self, nick):
        self.nick = nick


def usage(cmd):
    print("Usage: {} <mode=tcp|udp>".format(cmd))


def tcp_serv(port):
    server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(('', port))
    except Exception as e:
        print(e)
        exit(1)

    inputs = [server]
    outputs = []

    server.listen(10)
    try:
        while True:
            r_list, w_list, x_list = select.select(inputs, [], [])
            for t in r_list:
                if t is server:
                    client, addr = t.accept()
                    print("{} connected".format(addr))
                    client.setblocking(0)
                    inputs.append(client)
                else:
                    payload = t.recv(max_buff_len)
                    if payload != b"":
                        cmd = payload.decode().split()
                        try:
                            # command match cases
                            if cmd[0].upper() == "MSG":
                                # send message to all sockets except socket source
                                for oc in inputs:
                                    # concatenate all msg and send data
                                    if oc != server and oc != t:
                                        data = ""
                                        for i in range(len(cmd)):
                                            if i != 0:
                                                if i == 1:
                                                    data = cmd[i]
                                                else:
                                                    data = data + " " + cmd[i]
                                        data = data + "\n"
                                        oc.sendall(data.encode("utf-8"))
                            else:
                                t.sendall("Invalid command\n".encode("utf-8"))
                        except IndexError:
                            continue
                    else:
                        print("{} disconnected".format(t.getpeername()))
                        for oc in inputs:
                            if oc != server and oc != t:
                                oc.sendall("Client {} disconnected".format(t.getpeername()).encode("utf-8"))
                        inputs.remove(t)
                        t.close()
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
