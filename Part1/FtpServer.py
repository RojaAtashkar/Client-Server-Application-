import os
import random
import threading
import time
import socket
import json
import stat

# import grp
# import pwd

DISCONNECT_MESSAGE = "DISC"
LENGTH = 1000000
PORT_CONTROL = 20021
PORT_DATA = 20020
FORMAT = 'utf-8'
VALID_CMDS = ["DISC", "AUTH", "LIST", "GET", "PUT", "DELE", "MPUT"]


def log(func, cmd):
    log_msg = time.strftime("%Y-%m-%d %H-%M-%S [-] " + func)
    print("\033[31m%s\033[0m: \033[32m%s\033[0m" % (log_msg, cmd))


def fileProperty(filepath):
    """
    return information from given file, like this "-rw-r--r-- 1 User Group 312 Aug 1 2014 filename"
    """
    st = os.stat(filepath)
    fileMessage = []

    def _getFileMode():
        modes = [
            stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR,
            stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP,
            stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH,
        ]
        mode = st.st_mode
        fullmode = ''
        fullmode += os.path.isdir(filepath) and 'd' or '-'

        for i in range(9):
            fullmode += bool(mode & modes[i]) and 'rwxrwxrwx'[i] or '-'
        return fullmode

    def _getFilesNumber():
        return str(st.st_nlink)

    def _getSize():
        return str(st.st_size)

    def _getLastTime():
        return time.strftime('%b %d %H:%M', time.gmtime(st.st_mtime))

    for func in ('_getFileMode()', '_getFilesNumber()', '_getSize()', '_getLastTime()'):
        fileMessage.append(eval(func))
    fileMessage.append(os.path.basename(filepath))
    return ' '.join(fileMessage)


class FtpServer(threading.Thread):
    def __init__(self, conn, SERVER, users, cwd):
        threading.Thread.__init__(self)
        self.dataSockPort = None
        self.dataConn = None
        self.clientDataSock = None
        self.serverDataSock = None
        self.authenticated = False
        self.conn = conn
        self.SERVER = SERVER
        self.username = None
        self.password = None
        self.users = users
        self.cwd = cwd

    def run(self):
        """
        receive commands from client and execute commands
        """
        connected = True
        while connected:
            try:
                msg = self.conn.recv(LENGTH).decode(FORMAT)
                msg = json.loads(msg)
                if not msg or "Cmd" not in msg or msg["Cmd"] not in VALID_CMDS:
                    Server_String = {"Description": 'Syntax error, command unrecognized.This may include errors such '
                                                    'as command line too long.\r\n'}
                    json_string = json.dumps(Server_String)
                    self.send_msg(json_string)

                else:
                    arg = msg
                    func = getattr(self, msg["Cmd"])
                    log('RECEIVED DATA', msg)
                    func(arg)

            except socket.error as err:
                pass
                # log('Receive', err)

        self.conn.close()

    def send_welcome(self):
        pass

    def send_msg(self, cmd):
        self.conn.send(cmd.encode(FORMAT))

    def send_data(self, file_name):
        with open(file_name, 'rb') as file:
            file_data = file.read()
        self.dataConn.sendall(file_data)
        pass

    def AUTH(self, msg):
        Server_String = {
            "StatusCode": 230,
            "Description": " Successfully logged in. Proceed "
        }
        Server_String_failed = {
            "StatusCode": 430,
            "Description": " Failure in granting root accessibility "
        }

        try:
            username = msg["User"]
            password = msg["Password"]
            if self.users.get(username, "not found") == password:
                log("USER", username)
                self.username = username
                self.password = password
                self.authenticated = True
                log("AUTH", Server_String["Description"])
                json_string = json.dumps(Server_String)
            else:
                log("AUTH", Server_String_failed["Description"])
                json_string = json.dumps(Server_String_failed)

        except:
            log("AUTH", Server_String_failed["Description"])
            json_string = json.dumps(Server_String_failed)
        self.send_msg(json_string)

    def QUIT(self):
        self.conn.close()

    def start_data_socket(self):
        try:
            self.dataSockPort = random.randint(50000, 60000)
            dataAddr = (self.SERVER, self.dataSockPort)
            self.serverDataSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.serverDataSock.bind(dataAddr)
            self.serverDataSock.listen(1)
            string = 'Opening a data channel on port ' + str(self.dataSockPort)
            log('START DATA CHANNEL', string)

        except socket.error as err:
            log('START DATA CHANNEL', err)

    def stop_data_socket(self):
        log('STOP DATA CHANNEL', 'Closing a data channel')
        try:
            self.serverDataSock.close()
        except socket.error as err:
            log('STOP DATA CHANNEL', err)

    def LIST(self, msg):
        pathname = os.path.abspath(os.path.join(self.cwd, '.'))
        if len(os.listdir(pathname)) == 0:
            Server_String = {
                "StatusCode": 210,
                "Description": "Empty"
            }
            json_string = json.dumps(Server_String)
            self.send_msg(json_string)
        else:

            self.start_data_socket()
            Server_String = {
                "StatusCode": 150,
                "Description": "PORT command successful",
                "DataPort": self.dataSockPort
            }
            json_string = json.dumps(Server_String)
            self.send_msg(json_string)
            self.dataConn, addr = self.serverDataSock.accept()
            cmd = str(addr) + " connected"
            log("NEW DATA CONNECTION", cmd)
            with open('ls.txt', 'w') as file:
                for f in os.listdir(pathname):
                    fileMessage = fileProperty(os.path.join(pathname, f))
                    file.write(fileMessage + '\n')
            self.send_data('ls.txt')
            self.stop_data_socket()
            Server_String = {
                "StatusCode": 226,
                "Description": " Directory send OK"
            }
            json_string = json.dumps(Server_String)
            self.send_msg(json_string)

    def GET(self, msg):

        file_name = msg["FileName"]
        current_dir = os.getcwd()  # Get the current working directory
        file_path = os.path.join(current_dir, file_name)  # Construct the full file path

        if os.path.exists(file_path):
            self.start_data_socket()
            Server_String = {
                "StatusCode": 150,
                "Description": "OK to send data ",
                "DataPort": self.dataSockPort
            }
            json_string = json.dumps(Server_String)
            self.send_msg(json_string)
            self.dataConn, addr = self.serverDataSock.accept()
            cmd = str(addr) + " connected"
            log("NEW DATA CONNECTION", cmd)
            self.send_data(file_name)
            self.stop_data_socket()
            Server_String = {
                "StatusCode": 226,
                "Description": "Transfer complete"
            }
            json_string = json.dumps(Server_String)
            self.send_msg(json_string)
        else:
            Server_String = {
                "StatusCode": 550,
                "Description": " File doesn’t exist "
            }
            json_string = json.dumps(Server_String)
            self.send_msg(json_string)

    def PUT(self, msg):
        if self.authenticated:
            file_name = msg["FileName"]
            self.start_data_socket()
            Server_String= {
                "StatusCode": 150,
                "Description": "OK to send data",
                "DataPort": self.dataSockPort
            }
            json_string = json.dumps(Server_String)
            self.send_msg(json_string)
            self.dataConn, addr = self.serverDataSock.accept()
            cmd = str(addr) + " connected"
            log("NEW DATA CONNECTION", cmd)
            file_data = self.dataConn.recv(LENGTH)
            # Open a new file and write the received data into it
            with open(file_name, 'wb') as file:
                file.write(file_data)
            self.stop_data_socket()
            Server_String = {
                "StatusCode": 226,
                "Description": "Transfer complete"
            }
            json_string = json.dumps(Server_String)
            self.send_msg(json_string)
        else:
            Server_String = {
                "StatusCode": 434,
                "Description": "The client doesn’t have the root access . File transfer aborted."
            }
            json_string = json.dumps(Server_String)
            self.send_msg(json_string)

    def DELE(self, msg):
        if self.authenticated:
            file_name = msg["FileName"]
            current_dir = os.getcwd()  # Get the current working directory
            file_path = os.path.join(current_dir, file_name)  # Construct the full file path

            if os.path.exists(file_path):
                os.remove(file_path)
                Server_String = {
                    "StatusCode": 200,
                    "Description": " Successfully deleted "
                }
                json_string = json.dumps(Server_String)
                self.send_msg(json_string)
            else:
                Server_String = {
                    "StatusCode": 550,
                    "Description" : "File doesn’t exist "
                }
                json_string = json.dumps(Server_String)
                self.send_msg(json_string)

        else:
            Server_String = {
                "StatusCode": 434,
                "Description" : " The client doesn ’t have the root access ."
            }
            json_string = json.dumps(Server_String)
            self.send_msg(json_string)

    def MPUT(self, msg):
        if self.authenticated:
            file_names = []
            l = len(msg) - 1
            for i in range(l):
                key = f"file_name_{i + 1}"  # Start numbering from 1
                file_names.append(msg[key])
            self.start_data_socket()
            Server_String = {
                "StatusCode": 150,
                "Description": "OK to send data",
                "DataPort": self.dataSockPort
            }
            json_string = json.dumps(Server_String)
            self.send_msg(json_string)
            self.dataConn, addr = self.serverDataSock.accept()
            cmd = str(addr) + " connected"
            log("NEW DATA CONNECTION", cmd)
            # Open a new file and write the received data into it
            for i in range(l):
                with open(file_names[i], 'wb') as file:
                    file_data = self.dataConn.recv(LENGTH)
                    file.write(file_data)
                    Server_String = {
                        "StatusCode": 226,
                        "Description": "Transfer complete"
                    }
                    json_string = json.dumps(Server_String)
                    self.send_msg(json_string)
            self.stop_data_socket()


        else:
            Server_String = {
                "StatusCode": 434,
                "Description": " The client doesn’t have the root access ."
            }
            json_string = json.dumps(Server_String)
            self.send_msg(json_string)
