import os
import socket
import threading
import time
from FtpServer import FtpServer, log

PORT_CONTROL = 20021
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT_CONTROL)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "DISC"
users = {
    "roja": "1234",
    "sara": "12345",
    "mohsen": "123456",
    "not found": ""
}
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)


def handle_client(conn, addr):
    cmd = str(addr) + " connected"
    log("NEW CONNECTION", cmd)
    ftp = FtpServer(conn, SERVER, users, os.getcwd())
    ftp.run()


def start():
    server.listen()
    cmd = "server is listening on " + SERVER
    log("LISTENING", cmd)
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        cmd = threading.active_count() - 1
        log("ACTIVE CONNECTIONS", cmd)


log("STARTING", "server is starting...")
start()
