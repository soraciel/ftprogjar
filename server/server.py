import select
import socket
import sys
import threading
import os
import shutil
import errno

CodeNo230 = "230 Logged on"
CodeNo250 = "250 File deleted successfully"
CodeNo500 = "500 Syntax error, command unrecognized"
CodeNo501 = "501 Syntax error"
CodeNo503 = "503 Bad sequence of commands!"
CodeNo530_1 = "530 Login or password incorrect!"
CodeNo530_2 = "530 Please log in with USER and PASS first."

# mengubah direktori aktif
def CWD(active_directory, command):
    if os.path.isdir(os.path.join(active_directory,command)):
        return os.path.join(active_directory,command)
    else:
        return active_directory

def RNFR(active_directory, command):
    if os.path.isdir(os.path.join(active_directory,command)):
        return "350 Directory exists, ready for destination name."
    elif os.path.exists(os.path.join(active_directory,command)):
        return "350 File exists, ready for destination name."
    else:
        return "550 file/directory not found"

def RNTO(active_directory, rename_from, command):
    try:
        os.rename(rename_from,os.path.join(active_directory,command))
        return "250 file renamed successfully"
    except OSError as exception:
        if exception.errno == errno.EEXIST:
            return "553 file exists"
        else:
            return "553 Filename invalid"

# menghapus file
def DELE(file_path):
    result = ""
    try:
        os.remove(file_path)
        return CodeNo250
    except OSError as exception:
        if exception.errno==errno.ENOENT or exception.errno==errno.EACCES or exception.errno==errno.EISDIR or exception.errno==errno.ENOENT:
            return "550 File not found"

# membuat direktori
def MKD(active_directory, command, base_directory):
    try:
        os.makedirs(os.path.join(active_directory,command))
        command = os.path.join(active_directory,command).split(base_directory)
        return "257 \""+ command[1] +"\" created successfully"
    except OSError as exception:
        #something wrong here
        #bisa membuat folder dengan nama apapun
        if exception.errno != errno.EEXIST:
            return "550 Directoryname not valid"
        return "550 Directory already exists"

# menghapus direktori
def RMD(active_directory, command):
    try:
        os.rmdir(os.path.join(active_directory,command))
        return "250 Directory deleted successfully"
    except OSError as exception:
        if exception.errno == errno.ENOTEMPTY:
            return "550 Directory not empty."
        else:
            return "550 Directory not found"

# mendaftar file dan direktori
def LIST(active_directory):
    data = ".\n..\n"
    for filename in os.listdir(active_directory):
        print  filename
        data += filename+"\n"
    return data

def HELP(command):
    result = ""
    if command == "":
        result += "214-The following commands are recognized:\n"
        result += "USER PASS CWD QUIT RETR STOR RNFR\n"
        result += "RNTO DELE RMD MKD PWD LIST HELP\n"
        result += "214 Have a nice day"
    elif command=="USER" or command=="PASS" or command=="QUIT" or command=="PWD" or command=="LIST" or command=="CWD" or command=="RETR" or command=="STOR" or command=="RNFR" or command=="RNTO" or command=="DELE" or command=="RMD" or command=="MKD" or command=="HELP":
        result += "214 Command " + command + " is supported by FTProgjar Server"
    else:
        result += "502 Command " + command + " is not recognized or supported by FTProgjar Server"
    return result

class Server:
    def __init__(self):
        self.host = ''
        self.port = 50000
        self.backlog = 5
        self.size = 1024
        self.server = None
        self.threads = []

    def open_socket(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((self.host,self.port))
            self.server.listen(5)
        except socket.error, (value,message):
            if self.server:
                self.server.close()
            print "Could not open socket: " + message
            sys.exit(1)

    def run(self):
        self.open_socket()
        input = [self.server,sys.stdin]
        print input
        running = 1
        while running:
            inputready,outputready,exceptready = select.select(input,[],[])
            for s in inputready:
                print s

                if s == self.server:
                    # handle the server socket
                    c = Client(self.server.accept(),"razi")
                    c.start()
                    self.threads.append(c)

                elif s == sys.stdin:
                    # handle standard input
                    junk = sys.stdin.readline()
                    print junk
                    running = 0 

        # close all threads

        self.server.close()
        for c in self.threads:
            c.join()

class Client(threading.Thread):
    def __init__(self,(client,address),user):
        threading.Thread.__init__(self)
        self.client = client
        self.address = address
        self.size = 1024
        self.users = {'razi':'razi', 'ggwp':'glhf'}
        self.user = ""
        self.base_directory = os.getcwd()
        self.active_directory = ""
        self.auth = False
        self.rename = ""

    def run(self):
        running = 1
        while running:
            data = self.client.recv(self.size)
            #print data
            print self.active_directory
            print self.base_directory
            if data:
                data = data.rstrip()
                command = data.partition(" ")
                
                #print command
                
                if command[0] == "HELP":
                    result = HELP(command[2])
                    print result
                    self.client.send(result)

                elif command[0] == "QUIT":
                    result = "221 Goodbye"
                    print result
                    self.client.send(result)
                    self.client.close()
                    running = 0

                elif command[0] == "USER" and self.user == "":
                    if command[2] == "":
                        print CodeNo501
                        self.client.send(CodeNo501)
                    else:
                        self.user = command[2]
                        result = "331 Password required for " + self.user
                        self.auth = False
                        print result
                        self.client.send(result)
                
                elif command[0] == "PASS" and self.user != "":
                    if command[2] == "":
                        print CodeNo501
                        self.client.send(CodeNo501)
                    else:
                        find = False
                        if self.user in self.users:
                            find = True
                        if find and self.users[self.user]==command[2]:
                            self.auth = True
                            tmp = os.getcwd()
                            try:
                                os.chdir(os.getcwd() + "/" + self.user)
                            except OSError as exception:
                                os.makedirs(os.getcwd() + "/" + self.user)
                                os.chdir(os.getcwd() + "/" + self.user)
                            self.active_directory = os.getcwd()
                            self.base_directory = os.path.join(self.base_directory, self.user)
                            self.user = ""
                            os.chdir(tmp)
                            print CodeNo230
                            self.client.send(CodeNo230)
                        else:
                            print CodeNo530_1
                            self.client.send(CodeNo530_1)
                
                elif command[0] == "PASS" and self.user == "":
                    print CodeNo503
                    self.client.send(CodeNo503)
                
                elif (command[0]=="CWD" or command[0]=="RETR" or command[0]=="STOR" or command[0]=="RNFR" or command[0]=="RNTO" or command[0]=="DELE" or command[0]=="RMD" or command[0]=="MKD") and self.auth==False:
                    if command[2] == "":
                        print CodeNo501
                        self.client.send(CodeNo501)
                    else:
                        print CodeNo530_2
                        self.client.send(CodeNo530_2)

                elif (command[0]=="PWD" or command[0]=="LIST") and self.auth==False:
                    print CodeNo530_2
                    self.client.send(CodeNo530_2)

                elif self.auth:
                    if command[0] == "RETR":
                        if command[2] == "":
                            print CodeNo501
                            self.client.send(CodeNo501)
                        else:
                            file_path = os.path.join(self.active_directory,command[2])
                            if os.path.exists(file_path):
                                size = os.path.getsize(file_path) 
                                buf = "send_data_to_client\n"
                                buf += command[2]+"\n"
                                buf += str(size)+"\n"
                                buf += '\n\n\n'
                                size += len(buf)
                                file_data = open(file_path,'rb')
                                sentfile = file_data.read(1024)
                                buf += sentfile
                                while len(buf) < size:
                                    sentfile = file_data.read(1024)
                                    buf += sentfile
                                self.client.send(buf)
                                file_data.close()
                            else:
                                result = "File not found"
                                print result
                                self.client.send(result)

                    elif "send_data_to_server" in data:                 
                        message_header = data.partition("\n\n\n")
                        print "message_header : " + message_header[0]
                        file_info = message_header[0].split("\n")
                        file_name = os.path.join(self.active_directory,file_info[1])
                        file_size = file_info[2]
                        print "file_name: " + file_name
                        print "file_size: " + file_size
                        size = int(file_size)+len(message_header[0])+len(message_header[1])
                        
                        # receive data from server
                        buf = data
                        while len(buf) < size:
                            data = self.client.recv(size)
                            buf += data
                        
                        # check if file already exist (delete if exist)
                        if os.path.exists(file_name):
                            os.remove(file_name)

                        # get data file without message header
                        data_file = buf.partition('\n\n\n\n')
                        #print data_file[2]
                        
                        # write buffer data to new file
                        with open(file_name, 'wb') as file:
                           file.write(data_file[2])
                        self.client.send("ok")

                    # CWD belum bisa menangani .. (back folder), . (current folder), dan / (cwd dari root)
                    elif command[0] == "CWD":
                        if command[2] == "":
                            print CodeNo501
                            self.client.send(CodeNo501)
                        else:
                            tmp = self.active_directory
                            self.active_directory = CWD(self.active_directory, command[2])
                            if len(self.active_directory) < len(self.base_directory):
                                self.active_directory = self.base_directory
                            print self.active_directory
                            now = self.active_directory.split(self.base_directory)
                            print now
                            if now[1] == "":
                                now[1] = "/"
                            result = ""
                            if tmp == self.active_directory and command[2] != "..":
                                result += "550 CWD failed. \"" + now[1] + "\": directory not found."
                            else:
                                result += "250 CWD successful. \"" + now[1] + "\" is current directory."
                            print result
                            self.client.send(result)

                    #udah tapi gak tau kalau masih nge bug
                    elif command[0] == "PWD":
                        now = self.active_directory.split(self.base_directory)
                        if now[1] == "":
                            now[1] = "/"
                        result = "257 \"" + now[1] + "\" is current directory."
                        print result
                        self.client.send(result)

                    #emmm
                    elif command[0] == "RNFR":
                        if command[2] == "":
                            print CodeNo501
                            self.client.send(CodeNo501)
                        else:
                            result = RNFR(self.active_directory,command[2])
                            print result
                            if not ("550 file/directory not found" in result):
                                self.rename = os.path.join(self.active_directory,command[2])
                            self.client.send(result)

                    #kaya e ini benar2 fix
                    elif command[0] == "RNTO" and self.rename == "":
                        if command[2] == "":
                            print CodeNo501
                            self.client.send(CodeNo501)
                        else:
                            print CodeNo503
                            self.client.send(CodeNo503)

                    #emmm
                    elif command[0] == "RNTO":
                        if command[2] == "":
                            print CodeNo501
                            self.client.send(CodeNo501)
                        else:
                            result = RNTO(self.active_directory,self.rename,command[2])
                            print result
                            self.client.send(result)
                            self.rename = ""

                    #udah tapi gak tau kalau masih nge bug
                    elif command[0] == "DELE":
                        if command[2] == "":
                            print CodeNo501
                            self.client.send(CodeNo501)
                        else:
                            result = DELE(self.active_directory + "/" + command[2])
                            print result
                            self.client.send(result)

                    #udah tapi gak tau kalau masih nge bug
                    elif command[0] == "MKD":
                        if command[2] == "":
                            print CodeNo501
                            self.client.send(CodeNo501)
                        else:
                            result = MKD(self.active_directory, command[2], self.base_directory)
                            print result
                            self.client.send(result)

                    #udah tapi gak tau kalau masih nge bug
                    elif command[0] == "RMD":
                        if command[2] == "":
                            print CodeNo501
                            self.client.send(CodeNo501)
                        else:
                            result = RMD(self.active_directory, command[2])
                            print result
                            self.client.send(result)
                    
                    #udah tapi gak tau kalau masih nge bug. perbaiki tampilannya
                    elif command[0] == "LIST":
                        result = LIST(self.active_directory)
                        print result
                        self.client.send(result)

                    else:
                        print CodeNo500
                        self.client.send(CodeNo500)
                else:
                    print CodeNo500
                    self.client.send(CodeNo500)
            else:
                print "221 Goodbye"
                self.client.send("221 Goodbye")
                self.client.close()
                running = 0

if __name__ == "__main__":
    s = Server()
    s.run()
