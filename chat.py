import threading as th
import socket

def handle(socket):
    


t = th.Thread(None, handle, None, (sc,))
t.start()

