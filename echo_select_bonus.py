import socket
import sys
import select

# GLOBAL VARS
max_buff_len = 1500
port = 7777


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


def connect():
    pass


def disconnect(client, all_clients, msg, broadcast):
    """
    disconnect a client from the server and send a message to all other clients
    :param client: the client to disconnect
    :param all_clients: list of all clients on server
    :param msg: array containing all words of the message
    :param broadcast: specify if msg will be send to all client or not
    :return: list without the disconnected Client object
    """
    print("{} disconnected".format(client.getsocket().getpeername()))
    if broadcast:
        for oc in all_clients:
            if oc.getsocket() != all_clients[0].getsocket() and oc != client:
                if len(msg) == 0:
                    oc.getsocket().sendall("client \"{}\" disconnected\n".format(client.getnick()).encode("utf-8"))
                else:
                    oc.getsocket().sendall("[{}] {}\n".format(client.getnick(), msg).encode("utf-8"))
    else:
        if len(msg) == 0:
            client.getsocket().sendall(
                "You have been disconnected from the server\n".encode("utf-8"))
        else:
            client.getsocket().sendall("{}\n".format(msg).encode("utf-8"))
    all_clients.remove(client)
    client.getsocket().close()
    print("client disconnected \"{}\"".format(client.getnick()))
    return all_clients


def tcp_serv(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
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
                current_client = None
                for cs in inputs:
                    if cs.getsocket() is t:
                        current_client = cs
                if t is server:
                    client, addr = t.accept()
                    print("client connected {}".format(addr))
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
                                                    data = "[{}] ".format(current_client.getnick())
                                                    data = data + cmd[i]
                                                else:
                                                    data = data + " " + cmd[i]
                                        data = data + "\n"
                                        oc.socket.sendall(data.encode("utf-8"))
                            elif cmd[0].upper() == "NICK":
                                for i in range(len(cmd)):
                                    if i != 0:
                                        if i == 1:
                                            data = cmd[i]
                                        else:
                                            data = data + " " + cmd[i]
                                current_client.setnick(data)
                                print("client \"{}\" => {}".format(current_client.getsocket().getpeername(), current_client.getnick()))
                            elif cmd[0].upper() == "WHO":
                                data = "[server] "
                                for oc in inputs:
                                    if oc.getsocket() is not server:
                                        data += oc.getnick() + " "
                                data += "\n"
                                t.sendall(data.encode("utf-8"))
                            elif cmd[0].upper() == "QUIT":
                                msg = ""
                                for i in range(len(cmd)):
                                    if i != 0:
                                        msg += " " + cmd[i]
                                inputs = disconnect(current_client, inputs, msg, True)
                            elif cmd[0].upper() == "KILL":
                                if len(cmd) >= 3:
                                    msg = "[{}] ".format(current_client.getnick())
                                    for i in range(len(cmd)):
                                        if i > 1:
                                            if i != len(cmd) - 1:
                                                msg += cmd[i] + " "
                                            else:
                                                msg += cmd[i]
                                    for oc in inputs:
                                        if oc.getnick() == cmd[1]:
                                            ctodisc = oc
                                            inputs = disconnect(ctodisc, inputs, msg, False)
                                else:
                                    current_client.getsocket().sendall(
                                        "Error: command bad usage\nUsage: KILL <nick> <message>\n".encode("utf-8"))
                            else:
                                t.sendall("Invalid command\n".encode("utf-8"))
                        except IndexError:
                            continue
                    else:
                        inputs = disconnect(current_client, inputs, "", True)
    except KeyboardInterrupt:
        exit(1)


tcp_serv(port)
