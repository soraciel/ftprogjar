import socket
import sys
import os

host = 'localhost'
port = 50000
size = 1024
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host,port))
sys.stdout.write('> ')

while 1:
    # read from keyboard
    line = sys.stdin.readline()
    if line == '\n':
        break
    command = line.partition(" ")
    if command[0] == "STOR":
        if command[2] == "":
            s.send("STOR")
        else:
            file_path = os.path.join(os.getcwd(),command[2].rstrip())
            print file_path
            print os.path.exists(file_path)
            if os.path.exists(file_path):
                print "masuk"
                size = os.path.getsize(file_path) 
                buf = "send_data_to_server\n"
                buf += command[2].rstrip()+"\n"
                buf += str(size)+"\n"
                buf += '\n\n\n'
                size += len(buf)
                file_data = open(file_path,'rb')
                sentfile = file_data.read(1024)
                buf += sentfile
                while len(buf) < size:
                    sentfile = file_data.read(1024)
                    buf += sentfile
                s.send(buf)
                file_data.close()
            else:
                print "gagal"
                result = "File not found"
                print result
                s.send(result)
    else:
        s.send(line)

    data = s.recv(size)
    if data.rstrip() == "221 Goodbye":
    	sys.stdout.write(data+"\n")
    	print "Connection closed by server"
    	s.close()
    	break

    #ini masih salah
    if "send_data_to_client" in data:                 
        message_header = data.partition("\n\n\n")
        file_info = message_header[0].split("\n")
        file_name = os.path.join(os.getcwd(),file_info[1])
        file_size = file_info[2]
        size = int(file_size)+len(message_header[0])+len(message_header[1])
        
        # receive data from server
        buf = data
        while len(buf) < size:
            data = s.recv(size)
            buf += data
        
        # check if file already exist (delete if exist)
        if os.path.exists(file_name):
            os.remove(file_name)

        # get data file without message header
        data_file = buf.partition('\n\n\n\n')
        print data_file[2]
        
        # write buffer data to new file
        with open(file_name, 'wb') as file:
           file.write(data_file[2])
    else:
        sys.stdout.write(data+"\n")
    sys.stdout.write('> ')
s.close()
