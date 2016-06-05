from Messages import RequestVoteMessage
from Messages import AppendEntriesMessage
from Messages import VoteReplyMessage

import Messages
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
        self.running = True

        self.connected_servers = []

        self.last_heartbeat = time.time()
        # TODO: Set random election timeout from a range
        self.election_timeout = 5   # Time to wait for heartbeat or voting for a candidate before calling election

        # Election variables
        self.id_received_votes = set()      # Id of servers who granted you votes
        self.id_refused_votes = set()       # Id of servers who refused to vote for you
        self.num_received_votes = 0         # Number of votes received in current election

        # Persistent state variables
        # TODO: PERSIST; On server boot, retrieve information from disk
        self.current_term = 0          # Latest term server has seen
        self.voted_for = None          # CandidateId that received vote in current term
        self.log = []

        self.setup()
        threading.Thread.__init__(self)

    # Temp setup for testing purposes
    def setup(self):
        if self.id == 0:
            self.title = Constants.TITLE_LEADER
        self.leader = 0

    def request_vote(self, server_id):
        if not self.log:
            # Log is empty
            last_log_index = -1
            last_log_term = -1
        else:
            last_log_index = self.log[-1].index
            last_log_term = self.log[-1].term

        request_vote_msg = RequestVoteMessage(self.id, self.current_term, last_log_index, last_log_term)
        self.channel.send(request_vote_msg, server_id)

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
        # TODO: Voted_for must persist
        self.voted_for = self.id
        self.id_received_votes.add(self.id)
        self.num_received_votes = len(self.id_received_votes)
        self.last_heartbeat = time.time()

        for server in self.connected_servers:
            self.request_vote(host_to_id[server[0]])
            print "Requesting vote from server", host_to_id[server[0]]

    def send_heartbeat(self):
        # TODO: Implement
        pass

    def step_down(self):
        # Step down as leader or candidate, convert to follower
        # Reset various election variables
        if self.title == Constants.TITLE_LEADER or self.title == Constants.TITLE_CANDIDATE:
            self.title = Constants.TITLE_FOLLOWER
            self.id_received_votes = set()
            self.id_refused_votes = set()
            self.voted_for = None
            self.num_received_votes = 0
        print "Stepped down - converted to follower"

    def grant_vote(self, candidate_id):
        # TODO: Voted_for must persist
        self.voted_for = candidate_id
        self.channel.send(VoteReplyMessage(self.id, self.current_term, True), candidate_id)

    def majority(self):
        return len(self.connected_servers) / 2 + 1

    def check_election_status(self):
        if self.num_received_votes >= self.majority():
            # Become leader when granted majority of votes
            self.title = Constants.TITLE_LEADER
            # TODO: Implement rest of leader initialization

    # server_id: server that sent vote reply; vote_granted: True if vote granted
    def update_votes(self, server_id, vote_granted):
        if vote_granted:
            self.id_received_votes.add(server_id)
            self.num_received_votes = len(self.id_received_votes)
        else:
            self.id_refused_votes.add(server_id)

    def run(self):
        print "Server with id=", self.id, " up and running"
        while self.running:
            for server in list(addr_to_id.keys()):
                # if server not in self.connected_servers and not addr_to_id[server] == id:
                if server not in self.channel and not host_to_id[server[0]] == self.id:
                    connected = self.channel.connect(server)
                    if connected:
                        print str("Server: Connected to "+server[0])
                        self.connected_servers.append(server)
                    # print "Connected: ", connected

                data = self.channel.receive(4.0)
                if data:
                    for server_id, msg in data:
                        self.process_msg(server_id, msg)
                else:
                    self.check_status()

                    # MORTEN'S STUFF
                    # msg = 'hearbeat from ' + str(self.id)
                    # if self.role == 'leader':
                    #     for peer in self.connected_peers:
                    #         self.channel.send(msg, id=host_to_id[peer[0]])
                    #         print "sent msg to ", peer[0]

    def process_msg(self, server_id, msg):

        if msg.type == Constants.MESSAGE_TYPE_REQUEST_VOTE:
            if not self.log:
                # Log is empty
                last_log_index = -1
                last_log_term = -1
            else:
                last_log_index = self.log[-1].index
                last_log_term = self.log[-1].term

            # Handle message
            if msg.term < self.current_term:
                # If candidate's term is less than my term then refuse vote
                self.channel.send(VoteReplyMessage(self.id, self.current_term, False), msg.candidate_id)

            if msg.term > self.current_term:
                # If candidate's term is greater than my term then update current_term (latest term I've encountered),
                # Step down if leader or candidate
                self.current_term = msg.term
                # TODO: Step down if leader or candidate
                self.step_down()

            if msg.term >= self.current_term and self.voted_for is (None or msg.candidate_id) \
                    and (last_log_term < msg.last_log_term
                         or (last_log_term == msg.last_log_term and last_log_index <= msg.last_log_index)):
                # If candidate's term is at least as new as mine and I have granted anyone else a vote
                # and candidate's log is at least as complete as mine
                # then grant vote
                self.grant_vote(msg.candidate_id)

        elif msg.type == Constants.MESSAGE_TYPE_VOTE_REPLY:
            if msg.term > self.current_term and not msg.vote_granted:
                # Step down if reply from someone with higher term
                # Extra condition for security.
                # If responder's term is higher, then vote should not be granted with correct execution
                self.current_term = msg.term
                self.step_down()
            else:
                # Take care of grant or refusal of vote
                self.update_votes(msg.follower_id, msg.vote_granted)
                self.check_election_status()
        elif msg.type == Constants.MESSAGE_TYPE_APPEND_ENTRIES:
            pass

        elif msg.type == Constants.MESSAGE_TYPE_REQUEST_LEADER:
            msg = Messages.RequestLeaderMessage(leader=self.leader)
            self.channel.send(msg, id=server_id)

        elif msg.type == Constants.MESSAGE_TYPE_LOOKUP:
            self.process_lookup(server_id, msg)

        elif msg.type == Constants.MESSAGE_TYPE_POST:
            self.process_post(server_id, msg)

        else:
            print "Error: Invalid message type"

    def process_lookup(self, id, msg):
        pass

    def process_post(self, id, msg):
        pass

    def process_msg_number2(self, id, msg):
        if not msg:
            return
        print msg
        if msg == 'request_leader':
            response_msg = str(self.leader)
            print "Sending leader response msg: ", response_msg
            self.channel.send(response_msg, id=id)


id = int(sys.argv[1])
start_server(port=2000, id=id)




