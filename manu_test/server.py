from __future__ import print_function
import socket
import sys
import threading
import pickle
import time
from entry import Entry

server_addresses = [socket.gethostbyname(socket.gethostname()), # Server 0
                    socket.gethostbyname(socket.gethostname())] # Server 1

server_ports = [18005, 19005]
client_ports = [18105, 19105]

CONST_FOLLOWER = "follower"
CONST_LEADER = "leader"
CONST_CANDIDATE = "candidate"

total_number_of_servers = len(server_addresses)

class Server:

    def __init__(self, id=int(sys.argv[1]), port=int(sys.argv[2])):
        self.id = id
        self.client_socket = socket.socket()
        self.host = server_addresses[self.id]
        self.server_port = server_ports[self.id]  # For other servers to communicate RAFT stuff with this server?
        self.client_port = client_ports[self.id]  # For clients to connect to this server
        self.client_socket.bind((self.host, self.client_port))
        self.threads = []

        self.log = []
        # TODO: Decide how to initialize log


        self.current_term = 0
        self.voted_for = 0
        self.election_votes = 0 # Number of votes received in current election
        self.role = CONST_FOLLOWER
        self.current_leader = None
        self.time_last_heartbeat = time.time()
        self.connected_servers = []
        self.connected_to_all_servers = False
        # self.s.settimeout()

        self.total_num_connections = 0
        self.close_socket = False

        self.init_connection()

    def init_connection(self):
        self.log.append(Entry(0, 0, self.id, 0))

        incoming_rpc_handler = IncomingRPCHandler(self)
        incoming_rpc_handler.start()
        self.threads.append(incoming_rpc_handler)

        outgoing_rpc_handler = OutgoingRPCHandler(self)
        outgoing_rpc_handler.start()
        self.threads.append(outgoing_rpc_handler)

        # thread.start_new_thread(handle_RPC_send, ("Running try_handle", self))

        self.client_socket.listen(8)
        print("Server with id=", self.id, " is running and listening for incoming connections", sep="")


        while True:
            c, addr = self.client_socket.accept()
            print("Connected to", addr)
            c.send("Connection to server was successful")
            client = ClientHandler(c, addr, self)
            client.start()
            self.threads.append(client)
            self.total_num_connections += 1

        close_socket = True
        if close_socket:
            self.client_socket.close()
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
                self.parent_server.total_num_connections -= 1
                self.client.close()
                if self.parent_server.total_num_connections == 0:
                    self.parent_server.close_socket = True
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

class OutgoingRPCHandler(threading.Thread):
    def __init__(self, parent_server):
        threading.Thread.__init__(self)
        self.parent_server = parent_server

    def request_votes(self):
        candidate_id = self.parent_server.id
        term = self.parent_server.current_term
        last_log_index = len(self.parent_server.log) - 1
        last_log_term = self.parent_server.log[-1].get_term()

        print("Start vote requests")
        for server_id in range(len(server_ports)):
            if server_id != self.parent_server.id:

                failed = True

                while failed:
                    try:
                        print("Trying to connect")
                        sock = socket.socket()
                        port = server_ports[server_id]
                        sock.connect((server_addresses[server_id], port))

                    except:
                        print("Unable to connect and do RPC. Trying again")
                        time.sleep(2)
                        continue

                    failed = False
                    sock.send("Yo from server", candidate_id)
                    sock.close()


        print("Request vote done")


    def run(self):
        print("Running Outgoing RPC handler")

        while True:
            if self.parent_server != CONST_LEADER and (time.time() - self.parent_server.time_last_heartbeat) > 5:
                print("Heartbeat timeout")
                self.parent_server.current_term += 1
                self.parent_server.role = CONST_CANDIDATE
                self.parent_server.voted_for = self.parent_server.id

                self.request_votes()
                self.parent_server.time_last_heartbeat = time.time()
                break


class IncomingRPCHandler(threading.Thread):

    def __init__(self, parent_server):
        threading.Thread.__init__(self)
        self.parent_server = parent_server
        self.host = parent_server.host

    def run(self):
        sock = socket.socket()
        sock.bind((self.host, self.parent_server.server_port))
        sock.listen(10)

        while True:
            c, addr = sock.accept()
            print("Incoming server connection successful")
            self.parent_server.total_num_connections += 1

            recv = c.recv(4096)
            print(recv)

server = Server()