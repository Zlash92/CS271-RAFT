from __future__ import print_function
import socket
import pickle
import sys

server_addresses = [socket.gethostbyname(socket.gethostname()), # Server0
                    socket.gethostbyname(socket.gethostname())] # Server1

client_ports = [18108, 19108]

class Client:
    # Sys arg input - 1: server id, 2: port
    def __init__(self, server_id=int(sys.argv[1])):
        print("Setting up client")
        self.s = socket.socket()
        self.host = server_addresses[server_id]
        self.connect_to_server(self.host, client_ports[server_id])
        self.connected_server_id = server_id

    def connect_to_server(self, host, port):
        connection = False
        print("Connecting to server")

        try:
            self.s.connect((host, port))
            connection = True

        except:
            print('Unable to connect to server')
            self.s.close()

        if connection:
            # Receive no more than 1024 bytes
            print(self.s.recv(1024))

            while True:
                msg = raw_input('Enter message: ')
                if msg == 'close':
                    self.s.send(msg)
                    break

                elif msg == 'lookup':
                    self.s.send(msg)
                    try:
                        recv = self.s.recv(4096)
                        log = pickle.loads(recv)
                        printLog(log)
                    except ValueError, e:
                        print("Error : Value Error : ", e)
                    except EOFError, e:
                        print("Error : EOFError : ", e)
                    except e:
                        print("Something unexpected happened, try again: ", e)

                else:
                    self.s.send(msg)
        self.s.close()


def printLog(log):
    if len(log) != 0:
        for entry in log:
            print(entry)
    else:
        print("Log is empty")

server_id = int(sys.argv[1])
# c = Client(host='128.111.43.37', port=12353)
#c = Client(host=socket.gethostname(), port=18852)
c = Client()

