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
            self.nick = str(socket.getpeername())

    def getsocket(self):
        return self.socket

    def getnick(self):
        return str(self.nick)

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

    inputs = [Client(server, "server")]
    outputs = []

    server.listen(10)
    try:
        while True:
            r_list, w_list, x_list = select.select([x.getsocket() for x in inputs], [], [])
            for t in r_list:
                for cs in inputs:
                    if cs.getsocket() is t:
                        current_client = cs
                if t is server:
                    client, addr = t.accept()
                    print("{} connected".format(addr))
                    client.setblocking(0)
                    c = Client(client, addr)
                    inputs.append(c)
                else:
                    payload = t.recv(max_buff_len)
                    if payload != b"":
                        cmd = payload.decode().split()
                        try:
                            data = ""
                            # command match cases
                            if cmd[0].upper() == "MSG":
                                # send message to all sockets except socket source
                                for oc in inputs:
                                    # concatenate all msg and send data
                                    if oc.getsocket() != server and oc.getsocket() != t:
                                        for i in range(len(cmd)):
                                            if i != 0:
                                                if i == 1:
                                                    # put name at line beginning
                                                    data = "{}: ".format(current_client.getnick())
                                                    data = data+cmd[i]
                                                else:
                                                    data = data + " " + cmd[i]
                                        data = data + "\n"
                                        oc.socket.sendall(data.encode("utf-8"))
                            elif cmd[0].upper() == "NICK":
                                for oc in inputs:
                                    if oc.getsocket() is t:
                                        for i in range(len(cmd)):
                                            if i != 0:
                                                if i == 1:
                                                    data = cmd[i]
                                                else:
                                                    data = data + " " + cmd[i]
                                        oc.setnick(data)
                            elif cmd[0].upper() == "WHO":
                                data = "List of connected users:\n"
                                for oc in inputs:
                                    if oc.getsocket() is not server:
                                        data += oc.getnick()+"\n"
                                t.sendall(data.encode("utf-8"))
                            elif cmd[0].upper() == "QUIT":


                            else:
                                t.sendall("Invalid command\n".encode("utf-8"))
                        except IndexError:
                            continue
                    else:
                        print("{} disconnected".format(t.getpeername()))
                        for oc in inputs:
                            if oc.getsocket() != server and oc != t:
                                oc.getsocket().sendall("Client {} disconnected\n".format(current_client.getnick()).encode("utf-8"))
                        inputs.remove(current_client)
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
