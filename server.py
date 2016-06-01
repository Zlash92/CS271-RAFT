from __future__ import print_function
import socket
import sys
import threading
import pickle
import time


CONST_FOLLOWER = "follower"
CONST_LEADER = "leader"
CONST_CANDIDATE = "candidate"

server_addresses = [socket.gethostbyname(socket.gethostname()), # Server 0
                    socket.gethostbyname(socket.gethostname())] # Server 1

server_ports = [17760, 17761]
client_ports = [18860, 18861]

class Server:

    def __init__(self, server_id=int(sys.argv[1]), port=int(sys.argv[2])):
        self.server_id = server_id
        self.s = socket.socket()
        self.host = socket.gethostname()
        self.server_port = server_ports[server_id]
        self.client_port = client_ports[server_id]
        self.s.bind((self.host, self.port))
        self.log = []
        self.current_term = 0
        self.voted_for = 0
        self.type = CONST_FOLLOWER
        self.threads = []
        self.current_leader = None
        self.time_last_heartbeat = time.time()
        self.connected_servers = []
        self.s.settimeout(0)

        self.init_connection()

    def init_connection(self):
        self.s.listen(8)
        print("Server with id=", self.server_id, " is running and listening for incoming connections", sep="")
        close_socket = False

        while True:
            try:
                c, addr = self.s.accept()
                print("Connected to", addr)
                c.send("Connection to server was successful")
                client = ClientHandler(c, addr, self)
                client.start()
                self.threads.append(client)
            except socket.timeout:
                print("Listen accept TIMEOUT!")
                for server in server_addresses:
                    self.s.connect(())

        if close_socket:
            self.s.close()
            for client in self.threads:
                client.join()

    def lookup(self, c):
        package = pickle.dumps(self.data)
        c.send(package)

class ClientHandler(threading.Thread):
    def __init__(self, client, address, parent_server):
        threading.Thread.__init__(self)
        self.client = client
        self.address = address
        self.parent_server = parent_server

    def run(self):
        while True:
            recv = self.client.recv(4096)
            inp = recv.split(' ', 1)
            if recv == 'close':
                print("Closing client connection")
                self.client.close()
                break
            elif inp[0] == 'post':
                self.parent_server.post(inp[1], self.address)
            elif inp[0] == 'lookup':
                self.parent_server.lookup(self.client)
            elif inp[0] == 'sync' and len(inp)>1:
                sync_server = int(inp[1])
                self.parent_server.sync(sync_server)
            elif recv == "update_contents_on_my_server":
                id = server_addresses.index(self.address[0])
                self.parent_server.received_sync(self.client, id)
            elif len(recv)>0:
                print("Received message:", recv)


server = Server()