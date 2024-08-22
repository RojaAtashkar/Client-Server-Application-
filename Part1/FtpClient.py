import os
import socket
import time
import json

LENGTH = 1000000
PORT_CONTROL = 20021
FORMAT = 'utf-8'
SERVER = socket.gethostbyname(socket.gethostname())


def log(func, cmd):
    log_msg = time.strftime("%Y-%m-%d %H-%M-%S [-] " + func)
    print("\033[31m%s\033[0m: \033[32m%s\033[0m" % (log_msg, cmd))


class FtpClient:
    def __init__(self, client):
        self.clientDataSock = None
        self.client = client

    def start_data_socket(self, dataSockPort):
        try:
            dataAddr = (SERVER, dataSockPort)
            self.clientDataSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.clientDataSock.connect(dataAddr)
            log("NEW DATA CONNECTION ON PORT ", dataSockPort)

        except socket.error as err:
            log('START DATA CHANNEL', err)

    def stop_data_socket(self):
        log('STOP DATA CHANNEL', 'Closing a data channel')
        try:
            self.clientDataSock.close()
        except socket.error as err:
            log('STOP DATA CHANNEL', err)

    def LIST(self):
        Client_String = {
            "Cmd": "LIST"
        }
        json_string = json.dumps(Client_String)
        self.send_msg(json_string)
        response = self.client.recv(LENGTH).rstrip().decode(FORMAT)
        response = json.loads(response)
        log("SERVER'S RESPOND", response["Description"])
        if response["StatusCode"] == 150:
            self.start_data_socket(response["DataPort"])
            file_data = self.clientDataSock.recv(LENGTH)

            # Open a new file and write the received data into it
            with open('ls.txt', 'wb') as file:
                file.write(file_data)
            response = self.client.recv(LENGTH).rstrip().decode(FORMAT)
            response = json.loads(response)
            log("SERVER'S RESPOND", response["Description"])
            self.stop_data_socket()

    def run(self):
        while True:
            msg = input().rstrip()
            words = msg.split()
            if msg == "QUIT":
                self.QUIT()
                break
            elif msg == "ls":
                try:
                    self.LIST()
                except IndexError:
                    log("ERROR SENDING TO SERVER", 'Syntax error in parameters or arguments.\r\n')
            elif words[0] == "get":
                try:
                    self.GET(words[1])
                except IndexError:
                    log("ERROR SENDING TO SERVER", 'Syntax error in parameters or arguments.\r\n')
            elif words[0] == "put":
                try:
                    self.PUT(words[1])
                except IndexError:
                    log("ERROR SENDING TO SERVER", 'Syntax error in parameters or arguments.\r\n')
            elif words[0] == "delete":
                try:
                    self.DELETE(words[1])
                except IndexError:
                    log("ERROR SENDING TO SERVER", 'Syntax error in parameters or arguments.\r\n')
            elif words[0] == "AUTH":
                try:
                    self.AUTH(words[1], words[2])
                except IndexError:
                    log("ERROR SENDING TO SERVER", 'Syntax error in parameters or arguments.\r\n')
            elif words[0] == "mput":
                try:
                    self.MPUT(words[1])
                except IndexError:
                    log("ERROR SENDING TO SERVER", 'Syntax error in parameters or arguments.\r\n')
            else:
                log("ERROR SENDING TO SERVER", "Invalid command")

    def AUTH(self, username, password):
        Client_String = {
            "Cmd": "AUTH",
            "User": username,
            "Password": password
        }
        json_string = json.dumps(Client_String)
        self.send_msg(json_string)
        response = self.client.recv(LENGTH).rstrip().decode(FORMAT)
        response = json.loads(response)
        log("SERVER'S RESPOND", response["Description"])

    def QUIT(self):
        Client_String = {
            "Cmd": "QUIT"
        }
        self.client.close()
        json_string = json.dumps(Client_String)
        self.send_msg(json_string)

    def send_msg(self, msg):
        message = msg.encode(FORMAT)
        self.client.send(message)
        log("SENT MESSAGE", message)

    def GET(self, file_name):
        # The client sends the get command
        Client_String = {
            "Cmd": "GET",
            "FileName": file_name
        }
        json_string = json.dumps(Client_String)
        self.send_msg(json_string)
        response = self.client.recv(LENGTH).rstrip().decode(FORMAT)
        response = json.loads(response)
        log("SERVER'S RESPOND", response["Description"])
        if response["StatusCode"] == 150:
            self.start_data_socket(response["DataPort"])
            file_data = self.clientDataSock.recv(LENGTH)

            # Open a new file and write the received data into it
            with open(file_name, 'wb') as file:
                file.write(file_data)
            response = self.client.recv(LENGTH).rstrip().decode(FORMAT)
            response = json.loads(response)
            log("SERVER'S RESPOND", response["Description"])
            self.stop_data_socket()

    def PUT(self, file_name):
        # The client sends the PUT command
        current_dir = os.getcwd()  # Get the current working directory
        file_path = os.path.join(current_dir, file_name)  # Construct the full file path

        if os.path.exists(file_path):
            Client_String = {
                "Cmd": "PUT",
                "FileName": file_name
            }
            json_string = json.dumps(Client_String)
            self.send_msg(json_string)
            response = self.client.recv(LENGTH).rstrip().decode(FORMAT)
            response = json.loads(response)
            log("SERVER'S RESPOND", response["Description"])
            if response["StatusCode"] == 150:
                self.start_data_socket(response["DataPort"])
                self.send_data(file_name)
                response = self.client.recv(LENGTH).rstrip().decode(FORMAT)
                response = json.loads(response)
                self.stop_data_socket()
                log("SERVER'S RESPOND", response["Description"])

        else:
            log("PUT DATA ERROR", "the file doesn't exists.")

    def send_data(self, file_name):
        with open(file_name, 'rb') as file:
            file_data = file.read()
        self.clientDataSock.sendall(file_data)

    def DELETE(self, file_name):

        Client_String = {
            "Cmd": "DELE",
            "FileName": file_name
        }
        json_string = json.dumps(Client_String)
        self.send_msg(json_string)
        response = self.client.recv(LENGTH).rstrip().decode(FORMAT)
        response = json.loads(response)
        log("SERVER'S RESPOND", response["Description"])

    def MPUT(self, names):
        file_names = names.split(',')
        current_dir = os.getcwd()  # Get the current working directory
        Client_String = {
            "Cmd": "MPUT",
        }
        all_files_exist = True
        for i in range(len(file_names)):
            file_path = os.path.join(current_dir, file_names[i])
            if not os.path.exists(file_path):
                all_files_exist = False
                break
            key = f"file_name_{i + 1}"
            Client_String[key] = file_names[i]
        if all_files_exist:
            json_string = json.dumps(Client_String)
            print(json_string)
            self.send_msg(json_string)
            response = self.client.recv(LENGTH).rstrip().decode(FORMAT)
            response = json.loads(response)
            log("SERVER'S RESPOND", response["Description"])
            if response["StatusCode"] == 150:
                self.start_data_socket(response["DataPort"])
                for i in range(len(file_names)):
                    self.send_data(file_names[i])
                    response = self.client.recv(LENGTH).rstrip().decode(FORMAT)
                    response = json.loads(response)
                    log("SERVER'S RESPOND", response["Description"])
                self.stop_data_socket()

        else:
            log("MPUT DATA ERROR", "one of the files doesn't exists.")


