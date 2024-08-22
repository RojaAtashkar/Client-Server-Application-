import socket
from FtpClient import FtpClient
PORT_CONTROL = 20021
FORMAT = 'utf-8'
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT_CONTROL)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

ftp = FtpClient(client)
ftp.run()
