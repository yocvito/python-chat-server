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
        if nick is not None:
            self.nick = nick
        else:
            addr, port = socket.getpeername()
            self.nick = str(addr) + ":" + str(port)

    def getsocket(self):
        return self.socket

    def getnick(self):
        return str(self.nick)

    def setsocket(self, socket):
        self.socket = socket

    def setnick(self, nick):
        self.nick = nick


class Channel:
    """
        class Channel of tcp chat server
        id      the id number of the channel
        admin   the administrator of the channel
        clients the list of the channel connected clients
    """

    def __init__(self, id, admin):
        self.id = id
        self.admin = admin
        self.clients = [admin]

    def getid(self):
        return self.id

    def getadmin(self):
        return self.admin

    def getclients(self):
        return self.clients

    def setid(self, id):
        self.id = id

    def setadmin(self, admin):
        self.admin = admin

    def addclient(self, client):
        self.clients.append(client)

    def delclient(self, client):
        self.clients.remove(client)

    def ismember(self, client):
        return self.clients.count(client) != 0

    def isadmin(self, client):
        return self.admin == client


class Server:

    def __init__(self, socket):
        self.socket = socket.getsocket()
        self.clients = [socket]
        self.channels = {}

    def getsocket(self):
        return self.socket

    def getclients(self):
        return self.clients

    def getclient(self, nick):
        for c in self.clients:
            if c.getnick() == nick:
                return c
        return None

    def getchannels(self):
        return self.channels

    def getclientchannels(self, client):
        ret = []
        for key in self.channels:
            if self.channels[key].ismember(client):
                ret.append(self.channels[key])
        return ret

    def iscotochannel(self, client, id):
        if id.isnumeric():
            if self.chanexist(id):
                return self.getclients()[id].ismember(client)
            else:
                self.send(client, "channel {} doesn't exit".format(id))
        else:
            self.send(client, "channel id isn't a numeric value")
        return False

    def addchannel(self, channel):
        print("channel created => channel {}".format(channel.getid()))
        self.channels[channel.getid()] = channel

    def delchannel(self, channel):
        del self.channels[channel.getid()]

    def addclient(self, client):
        self.clients.append(client)

    def delclient(self, client):
        chnls = self.getclientchannels(client)
        for ch in chnls:
            self.channels[ch.getid()].delclient(client)
        self.clients.remove(client)

    def chanexist(self, id):
        return self.getchannels().get(id) is not None

    def send(self, client, msg):
        client.getsocket().sendall("[server] {}\n".format(msg).encode("utf-8"))


def disconnect(server, client, msg, broadcast):
    """
    disconnect a client from the server and send a message to all other clients
    :param server: server object
    :param client: client to disconnect
    :param msg: array containing all words of the message
    :param broadcast: specify if msg will be send to all client or not
    :return: list without the disconnected Client object
    """
    if broadcast:
        for oc in server.getclients():
            if oc.getsocket() != server.getsocket() and oc != client:
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
    server.delclient(client)
    client.getsocket().close()
    print("client disconnected \"{}\"".format(client.getnick()))
    return server.getclients()


def tcp_serv(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(('', port))
    except Exception as e:
        print(e)
        exit(1)

    serv = Server(Client(server, "server"))

    server.listen(10)
    try:
        while True:
            inputs = serv.getclients()
            r_list, w_list, x_list = select.select([x.getsocket() for x in inputs], [], [])
            for t in r_list:
                current_client = None
                for cs in inputs:
                    if cs.getsocket() is t:
                        current_client = cs
                if t is server:
                    # accept client connection & add client object to client list
                    client, addr = t.accept()
                    cli = Client(client, None)
                    print("client connected {}".format(cli.getnick()))
                    client.setblocking(0)
                    serv.addclient(cli)
                else:
                    # data reception
                    payload = t.recv(max_buff_len)
                    if payload != b"":
                        cmd = payload.decode().split()
                        try:
                            data = ""
                            # command match cases
                            if cmd[0].upper() == "MSG":
                                if len(cmd) >= 2:
                                    if cmd[1].isnumeric():
                                        if len(serv.getclientchannels(current_client)) != 0:
                                            # send message to all sockets except socket source
                                            for oc in serv.getchannels()[eval(cmd[1])].getclients():
                                                # concatenate all msg and send data
                                                if oc.getsocket() != server and oc.getsocket() != t:
                                                    for i in range(len(cmd)):
                                                        if i > 1 and serv.getchannels()[eval(cmd[1])] \
                                                                .ismember(current_client):
                                                            if i == 2:
                                                                # put name at line beginning
                                                                data = "[{}] ".format(current_client.getnick())
                                                                data = data + cmd[i]
                                                            else:
                                                                data = data + " " + cmd[i]
                                                    data = data + "\n"
                                                    oc.getsocket().sendall(data.encode("utf-8"))
                                        else:
                                            serv.send(current_client, "you are not connected to a channel, please "
                                                                      "connect using JOIN before trying to talk")
                                    else:
                                        serv.send(current_client, "bad command usage\nUsage: MSG <channel> <msg>")
                                else:
                                    serv.send(current_client, "bad command usage\nUsage: MSG <channel> <msg>")
                            elif cmd[0].upper() == "NICK":
                                # change name of current client
                                for i in range(len(cmd)):
                                    if i != 0:
                                        if i == 1:
                                            data = cmd[i]
                                        else:
                                            data = data + " " + cmd[i]
                                current_client.setnick(data)
                                print("client \"{}\" => \"{}\"".format(current_client.getsocket().getpeername(),
                                                                       current_client.getnick()))
                            elif cmd[0].upper() == "WHO":
                                # send all connected client names to current client
                                for oc in inputs:
                                    if oc.getsocket() is not server:
                                        data += oc.getnick() + " "
                                serv.send(current_client, data)
                            elif cmd[0].upper() == "QUIT":
                                msg = ""
                                for i in range(len(cmd)):
                                    if i != 0:
                                        msg += " " + cmd[i]
                                inputs = disconnect(serv, current_client, msg, True)
                            elif cmd[0].upper() == "KILL":
                                if len(cmd) >= 2:
                                    msg = "[{}] ".format(current_client.getnick())
                                    print(len(cmd))
                                    for i in range(len(cmd)):
                                        print(i)
                                        if i > 1:
                                            if i != len(cmd):
                                                msg += cmd[i] + " "
                                            else:
                                                msg += cmd[i]
                                    for oc in inputs:
                                        if oc.getnick() == cmd[1]:
                                            ctodisc = oc
                                            inputs = disconnect(serv, ctodisc, msg, False)
                                else:
                                    serv.send(current_client, "command bad usage\nUsage: KILL <nick> <message>")
                            elif cmd[0].upper() == "JOIN":
                                if len(cmd) != 1:
                                    if serv.chanexist(eval(cmd[1])):
                                        serv.getchannels().get(eval(cmd[1])).addclient(current_client)
                                    else:
                                        serv.addchannel(Channel(eval(cmd[1]), current_client))
                                else:
                                    serv.send(current_client, "command bad usage\nUsage: JOIN <channel>")
                            elif cmd[0].upper() == "PART":
                                if len(cmd) != 1:
                                    if serv.chanexist(eval(cmd[1])):
                                        serv.getchannels().get(eval(cmd[1])).delclient(current_client)
                                        print("client {} leave channel {}".format(current_client.getnick(), cmd[1]))
                                    else:
                                        serv.send(current_client, "channel doesn't exist")
                                else:
                                    serv.send(current_client, "command bad usage\nUsage: PART <channel>")
                            elif cmd[0].upper() == "LIST":
                                if len(serv.getchannels()) != 0:
                                    data = "channels :\n"
                                    for key in serv.getchannels():
                                        data += "\tchannel {}\n".format(serv.getchannels()[key].getid())
                                    serv.send(current_client, data)
                                else:
                                    serv.send(current_client, "no channel opened")
                            elif cmd[0].upper() == "KICK":
                                cli_cnls = serv.getclientchannels(current_client)
                                ctokick = serv.getclient(cmd[1])
                                for ch in cli_cnls:
                                    if ch.isadmin(current_client):
                                        if ch.ismember(ctokick):
                                            serv.getchannels()[ch.getid()].delclient(ctokick)
                                            serv.send(ctokick, "you have been kicked from channel {}"
                                                      .format(ch.getid()))
                                        else:
                                            serv.send(current_client, "you cannot kick clients that aren't "
                                                                      "in same channel as you")
                                    else:
                                        serv.send(current_client,
                                                  "you must be administrator of the channel to kick clients")
                            else:
                                serv.send(current_client, "Invalid command")
                        except IndexError:
                            continue
                    else:
                        inputs = disconnect(serv, current_client, "", True)
    except KeyboardInterrupt:
        exit(1)


tcp_serv(port)
