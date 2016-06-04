from Messages import RequestVoteMessage
from Messages import AppendEntriesMessage

import Queue
import threading
import sys
import tcp
import Constants
import pickle
import time

port = 2000
addr_to_id = {('52.37.112.251', port): 0, ('52.40.128.229', port): 1, ('52.41.5.151', port): 2}
id_to_addr = {0: ('52.37.112.251', port), 1: ('52.40.128.229', port), 2: ('52.41.5.151', port)}
host_to_id = {'52.37.112.251': 0, '52.40.128.229': 1, '52.41.5.151': 2}
id_to_host = {0: '52.37.112.251', 1: '52.40.128.229', 2: '52.41.5.151'}



def start_server(port=80, id=None):
    queue = Queue.Queue()
    server = Server(queue, port, id)
    server.start()
    return queue


def addr_to_tuple(addr):
    tuple = (addr, port)
    return tuple


class Server(threading.Thread):

    def __init__(self, queue, port, id):
        self.port = port
        self.id = id
        self.queue = queue
        self.title = Constants.TITLE_FOLLOWER
        self.channel = tcp.Network(port, id)
        self.channel.start()
        self.leader = None
        self.connected_servers = []

        self.last_heartbeat = time.time()
        # TODO: Set random election timeout from a range
        self.election_timeout = 5   # Time to wait for heartbeat or voting for a candidate before calling election

        # Vote variables
        self.num_votes = 0          # Number of votes received in current election

        # Persistent state variables
        # TODO: PERSIST; On server boot, retrieve information from disk
        self.current_term = 0          # Latest term server has seen
        self.voted_for = None          # CandidateId that received vote in current term
        self.log = []

        self.running = True
        threading.Thread.__init__(self)

    def request_vote(self, server_id):
        if not self.log:
            # Log is empty
            last_log_index = -1
            last_log_term = -1
        else:
            last_log_index = self.log[-1].index
            last_log_term = self.log[-1].term

        request_vote_msg = RequestVoteMessage(self.id, self.current_term, last_log_index, last_log_term)
        data = pickle.dumps(request_vote_msg)
        self.channel.send(data, server_id)

    def check_status(self):
        current_time = time.time()

        if self.title == Constants.TITLE_LEADER:
            self.send_heartbeat()
        elif self.title == Constants.TITLE_FOLLOWER and current_time - self.last_heartbeat > self.election_timeout:
            # Election timeout passed as follower: Call for election
            self.start_election()
        elif self.title == Constants.TITLE_CANDIDATE and current_time - self.last_heartbeat > self.election_timeout:
            # Election timeout passed as candidate, without conclusion of election: Call for new election
            self.start_election()
        elif self.title == Constants.TITLE_CANDIDATE and current_time - self.last_heartbeat < self.election_timeout:
            # Election timeout has not passed as candidate
            print "As candidate, election timeout has not passed..., fix todo"
            # TODO: Do something
            pass

    def start_election(self):
        self.current_term += 1
        self.voted_for = self.id
        self.last_heartbeat = time.time()

        for server in self.connected_servers:
            

    def send_heartbeat(self):
        # TODO: Implement
        pass

    def run(self):

        while self.running:
            for server in list(addr_to_id.keys()):
                # if server not in self.connected_servers and not addr_to_id[server] == id:
                if server not in self.channel and not host_to_id[server[0]] == id:
                    connected = self.channel.connect(server)
                    if connected:
                        print str("Server: Connected to "+server[0])
                        self.connected_servers.append(server)
                    # print "Connected: ", connected
                message = self.channel.receive(4.0)
                if message:
                    for addr, msg in message:
                        self.process_msg(addr, msg)
                else:
                    self.check_status()
                    # msg = 'hearbeat from' + str(id)
                    # for server in self.connected_servers:
                    #     self.channel.send(msg, id=host_to_id[server[0]])
                    #     print "sent msg to", server[0]

    def process_msg(self, addr, msg):
        print "MSG: ", msg

id = int(sys.argv[1])
start_server(port=2000, id=id)




