from messages import RequestVoteMessage
from messages import AppendEntriesMessage
from messages import VoteReplyMessage
from messages import AcknowledgeMessage
from messages import TextMessage
from log import Entry
from log import Log

import storage
import messages
import Queue
import threading
import sys
import network
import constants
import time
from random import random

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
        self.title = constants.TITLE_FOLLOWER
        self.channel = network.Network(port, id)
        self.channel.start()
        self.leader = None
        self.running = True

        self.connected_servers = []

        self.last_heartbeat = 0
        self.heartbeat_timeout = 0
        self.process_heartbeat()
        self.heartbeat_frequency = 3
        self.election_start_time = 0
        self.election_timeout = 5 * random() + 5  # Time to wait for heartbeat or voting for a candidate before calling election

        # Election variables
        self.id_received_votes = set()      # Id of servers who granted you votes
        self.id_refused_votes = set()       # Id of servers who refused to vote for you
        self.num_received_votes = 0         # Number of votes received in current election

        # Persistent state variables
        # TODO: PERSIST; On server boot, retrieve information from disk
        self.current_term = 0          # Latest term server has seen
        self.voted_for = None          # CandidateId that received vote in current term
        self.log = Log()

        self.next_index = None          # For leader: indices for updating follower logs
        self.latest_index_term = None        # For leader: tuples of latest entry index and term for each follower. Used for commit

        # self.setup()
        threading.Thread.__init__(self)

    # Temp setup for testing purposes
    def setup(self):
        if self.id == 0:
            self.title = constants.TITLE_LEADER
        self.leader = 0

    def request_votes(self):
        if not self.log.data:
            # Log is empty
            last_log_index = -1
            last_log_term = -1
        else:
            last_log_index = self.log.get(-1).index
            last_log_term = self.log.get(-1).term

        msg = RequestVoteMessage(self.id, self.current_term, last_log_index, last_log_term)
        for server in self.connected_servers:
            self.channel.send(msg, id=host_to_id[server[0]])
            print "Requesting vote from server", host_to_id[server[0]]

    def check_status(self):
        current_time = time.time()

        if self.title == constants.TITLE_LEADER:
            # Send AppendEntries to update follower logs
            for server in self.connected_servers:
                server_id = host_to_id[server[0]]
                next_index = self.next_index[server_id]
                print "Server_id: ", server_id, "Next_index: ", next_index, "Last_log_index:", self.log.last_log_index()

                # Send entries that the server has not received yet, if any
                if self.log.last_log_index() >= next_index:
                    entries = self.construct_entries_list(next_index)
                    if next_index == 0:
                        prev_log_index = -1
                        prev_log_term = -1
                    else:
                        prev_log_index = self.log.get(next_index-1).index
                        prev_log_term = self.log.get(next_index-1).term
                    print "PREV_LOG_INDEX", prev_log_index
                    print self.log.get(next_index-1)
                    msg = AppendEntriesMessage(self.current_term, self.id, prev_log_index,
                                               prev_log_term, entries, self.log.last_commit_index)
                    print "SEND AppendEntries"
                    self.channel.send(msg, id=server_id)

            if current_time - self.last_heartbeat >= self.heartbeat_frequency:
                self.send_heartbeats()
        elif self.title == constants.TITLE_FOLLOWER and current_time - self.last_heartbeat > self.heartbeat_timeout:
            # Heartbeat timeout passed as follower: Start election
            print "Election timeout as follower. No heartbeat. Become candidate and start new election"
            self.start_election()
        elif self.title == constants.TITLE_CANDIDATE and current_time - self.election_start_time > self.election_timeout:
            # Election timeout passed as candidate, without conclusion of election: Start new election
            print "Election timeout as candidate. Election has not yet led to new leader. Starting new election"
            self.election_timeout = 6 * random() + 6
            self.start_election()
        elif self.title == constants.TITLE_CANDIDATE and current_time - self.election_start_time < self.election_timeout:
            # Election timeout has not passed as candidate
            print "As candidate, election timeout has not passed..., fix todo"
            # TODO: Resend vote requests to servers that have not responded?

    def construct_entries_list(self, index):
        entries = []
        for i in range(index, len(self.log)):
            entries.append(self.log.get(i))
        return entries

    def start_election(self):
        self.title = constants.TITLE_CANDIDATE
        self.reset_election_info()
        self.current_term += 1
        # TODO: Voted_for must persist
        self.voted_for = self.id
        print "Voted for self"
        self.update_votes(self.id, True)
        self.election_start_time = time.time()
        self.check_election_status()

        self.request_votes()

    def process_heartbeat(self):
        self.last_heartbeat = time.time()
        self.heartbeat_timeout = 6 * random() + 6

    def send_heartbeats(self):
        heartbeat = AppendEntriesMessage(self.current_term, self.id, -1, -1, [], -1)
        for server in self.connected_servers:
            self.channel.send(heartbeat, id=host_to_id[server[0]])
        self.process_heartbeat()

    def step_down(self):
        # Step down as leader or candidate, convert to follower
        # Reset various election variables
        if self.title == constants.TITLE_LEADER or self.title == constants.TITLE_CANDIDATE:
            self.title = constants.TITLE_FOLLOWER
            self.process_heartbeat()
            self.reset_election_info()
            print "Stepped down - converted to follower"

    def grant_vote(self, candidate_id):
        # TODO: Voted_for must persist
        self.voted_for = candidate_id
        print "Voted for", candidate_id
        self.channel.send(VoteReplyMessage(self.id, self.current_term, True), id=candidate_id)

    def refuse_vote(self, candidate_id):
        self.channel.send(VoteReplyMessage(self.id, self.current_term, False), id=candidate_id)
        print "Refused vote to", candidate_id

    def majority(self):
        return (len(self.connected_servers)+1) / 2 + 1

    def check_election_status(self):
        print "Majority is:", self.majority()
        if self.num_received_votes >= self.majority():
            # Become leader when granted majority of votes
            self.become_leader()

    def become_leader(self):
        self.title = constants.TITLE_LEADER
        self.leader = self.id
        print "Became LEADER"
        # TODO: Implement rest of leader initialization
        self.next_index = [len(self.log) for _ in range(len(addr_to_id))]

        latest_index = self.log.last_commit_index
        if self.log.contains_at_index(latest_index):
            latest_term = self.log.get(latest_index).term
        else:
            latest_term = 0

        self.latest_index_term = [(latest_index, latest_term) for _ in range(len(addr_to_id))]
        self.reset_election_info()
        self.send_heartbeats()

    def reset_election_info(self):
        self.id_received_votes = set()
        self.id_refused_votes = set()
        self.voted_for = None
        self.num_received_votes = 0

    # server_id: server that sent vote reply; vote_granted: True if vote granted
    def update_votes(self, server_id, vote_granted):
        if vote_granted:
            print "Received vote from", server_id
            self.id_received_votes.add(server_id)
            self.num_received_votes = len(self.id_received_votes)
            print "Number of received votes is now", self.num_received_votes
        else:
            print "Denied vote from", server_id
            self.id_refused_votes.add(server_id)

    def update_commits(self):
        print "Update commits"
        index = max(self.next_index)

        i_count = 0
        while i_count < self.majority():
            if index < 0:
                print "Error: Update_commits: index is less than 0"
            index -= 1
            t_count = 0
            i_count = 0
            for (i, t) in self.latest_index_term:
                if t == self.current_term:
                    t_count += 1
                if i >= index:
                    i_count += 1

        if self.log.last_commit_index < index:
            self.log.last_commit_index = index
        elif self.log.last_commit_index > index:
            print "Error: Update_commits: new commit index is lower than current commit_index"

        for entry in self.log.data:
            if not entry.client_ack_sent:
                # TODO: Send client ack
                ack_message = AcknowledgeMessage(ack=True, msg_id=entry.msg_id)
                self.channel.send(ack_message, id=entry.author)
                entry.client_ack_sent = True

    def run(self):
        print "Server with id=", self.id, " up and running"
        while self.running:
            self.update_connected_servers()
            for server in list(addr_to_id.keys()):
                # if server not in self.connected_servers and not addr_to_id[server] == id:
                if server not in self.channel and not host_to_id[server[0]] == self.id:
                    connected = self.channel.connect(server)
                    if connected:
                        print str("Server: Connected to "+server[0])
                        self.connected_servers.append(server)
                    # print "Connected: ", connected

                data = self.channel.receive(2.0)
                if data:
                    # print "There is data on channel"
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

    def process_msg(self, sender_id, msg):

        print "Processing message from", sender_id, "of type", msg.type
        if msg.type == constants.MESSAGE_TYPE_REQUEST_VOTE:
            self.process_request_vote(sender_id, msg)

        elif msg.type == constants.MESSAGE_TYPE_VOTE_REPLY:
            self.process_vote_reply(sender_id, msg)

        elif msg.type == constants.MESSAGE_TYPE_REQUEST_LEADER:
            msg = messages.RequestLeaderMessage(leader=self.leader)
            self.channel.send(msg, id=sender_id)

        elif msg.type == constants.MESSAGE_TYPE_LOOKUP:
            self.process_lookup(sender_id, msg)

        elif msg.type == constants.MESSAGE_TYPE_POST:
            self.process_post(sender_id, msg)

        elif msg.type == constants.MESSAGE_TYPE_APPEND_ENTRIES:
            self.process_append_entries(sender_id, msg)

        elif msg.type == constants.MESSAGE_TYPE_ACKNOWLEDGE:
            self.process_acknowledge(sender_id, msg)

        # Used for testing purposes
        elif msg.type == constants.MESSAGE_TYPE_TEXT:
            print "From", msg.sender_id, ":", msg.msg

        else:
            print "Error: Invalid message type"

    def process_lookup(self, sender_id, msg):
        if self.title == constants.TITLE_LEADER:
            msg = messages.LookupMessage(msg_id=msg.msg_id, post=self.log)
            self.channel.send(msg=msg, id=sender_id)
            print "lookup from client"
        else:
            msg = messages.RequestLeaderMessage(leader=self.leader)
            self.channel.send(msg=msg, id=sender_id)

    def process_post(self, sender_id, msg):
        if self.title == constants.TITLE_LEADER:
            entry = Entry(msg.post, sender_id, self.current_term, len(self.log)-1, msg_id=msg.msg_id)
            # TODO: PERSIST; implement in log class?
            self.log.append(entry)
            print "posting entry from client"
        else:
            msg = messages.RequestLeaderMessage(leader=self.leader)
            self.channel.send(msg=msg, id=sender_id)

    def process_request_vote(self, sender_id, msg):
        if not self.log:
            # Log is empty
            last_log_index = -1
            last_log_term = -1
        else:
            last_log_index = self.log.get(-1).index
            last_log_term = self.log.get(-1).term

        # Handle message
        if msg.term < self.current_term:
            # If candidate's term is less than my term then refuse vote
            print "Refuse vote to server", sender_id, "because I have higher term"
            self.refuse_vote(msg.candidate_id)

        if msg.term > self.current_term:
            # If candidate's term is greater than my term then update current_term (latest term I've encountered),
            # Step down if leader or candidate
            self.current_term = msg.term
            # TODO: Step down if leader or candidate
            self.step_down()

        if msg.term >= self.current_term:
            # If candidate's term is at least as new as mine and I have granted anyone else a vote
            # and candidate's log is at least as complete as mine
            # then grant vote
            if self.voted_for is None or self.voted_for is msg.candidate_id:
                if last_log_term < msg.last_log_term or (
                        last_log_term == msg.last_log_term and last_log_index <= msg.last_log_index):
                    self.grant_vote(msg.candidate_id)
        else:
            print "Cand term, current_term:", msg.term, self.current_term
            print "Voted for:", self.voted_for
            print "Cand log term, last_log_term", msg.last_log_term, last_log_term
            print "Cand log index, last_log_index", msg.last_log_index, last_log_index
            self.refuse_vote(msg.candidate_id)

    def process_vote_reply(self, sender_id, msg):
        if msg.term > self.current_term and not msg.vote_granted:
            # Step down if reply from someone with higher term
            # Extra condition for security.
            # If responder's term is higher, then vote should not be granted with correct execution
            self.current_term = msg.term
            print "Denied vote from", msg.follower_id
            self.step_down()
        else:
            # Take care of grant or refusal of vote
            self.update_votes(msg.follower_id, msg.vote_granted)
            self.check_election_status()

    def process_acknowledge(self, sender_id, msg):
        if msg.ack:
            print "Process Acknowledge from server. ACK == TRUE"
            print "MSG - NEXT INDEX:", msg.next_index
            self.next_index[sender_id] = msg.next_index
            self.latest_index_term[sender_id] = msg.latest_index_term
            self.update_commits()
        else:
            print "Process Acknowledge from server. ACK == FALSE"
            self.next_index[sender_id] -= 1
            if msg.term > self.current_term:
                self.current_term = msg.term
                self.step_down()

    def process_append_entries(self, sender_id, msg):
        print "LENGTH OF ENTRIES IN MSG:", len(msg.entries)
        if len(msg.entries) == 0:
            print "This is a heartbeat", msg.entries
            self.last_heartbeat = time.time()
            self.leader = sender_id
            print "Heartbeat received from server", sender_id

            if self.title == constants.TITLE_CANDIDATE or self.title == constants.TITLE_LEADER:
                self.step_down()

            elif self.title == constants.TITLE_LEADER:
                # TODO: If a "leader" receives a heartbeat,
                # it might have crashed and joined back in after an election (?)
                pass
        else:
            # TODO: Process AppendEntriesMessage
            print "Processing NON-HEARTBEAT Append Entries"
            # self.process_heartbeat()
            if msg.term > self.current_term:
                self.current_term = msg.term

            if self.title == constants.TITLE_CANDIDATE or self.title == constants.TITLE_LEADER:
                self.step_down()

            # Reject if my term is greater than leader term
            if self.current_term > msg.term:
                print "Error: Current term greater than leaders term"
                self.channel.send(AcknowledgeMessage(ack=False, term=self.current_term), id=sender_id)

            # Accept. Self.log is empty and leader is sending all entries
            elif self.log.is_empty() and msg.prev_log_index == -1:
                print "Appending entries"
                # First entry to append is at index 0
                self.log.append_entries(msg.entries)
                self.log.last_commit_index = msg.commit_index
                i = self.log.last_log_index()
                t = self.log.get(i).term
                self.channel.send(AcknowledgeMessage(
                    ack=True, next_index=len(self.log), latest_index_term=(i, t)), id=sender_id)

            # Accept. Check if self.log has an element at msg.prev_log_index
            elif self.log.contains_at_index(msg.prev_log_index):
                # Check if the term corresponds with msg.prev_log_term
                print "Prev_log_index:", msg.prev_log_index
                print self.log.get(msg.prev_log_index)
                if self.log.get(msg.prev_log_index).term == msg.prev_log_term:
                    self.log.append_entries(msg.entries)
                    self.log.last_commit_index = msg.commit_index
                    i = self.log.last_log_index()
                    t = self.log.get(i).term
                    self.channel.send(
                        AcknowledgeMessage(ack=True, next_index=len(self.log), latest_index_term=(i, t)), id=sender_id)
            else:
                self.channel.send(AcknowledgeMessage(ack=False),id=sender_id)

    def save_state(self):
        storage.save(self.id, self.voted_for, self.current_term, self.log)

    def load_state(self):
        self.voted_for, self.current_term, self.log = storage.load(self.id)

    def update_connected_servers(self):
        for addr in list(addr_to_id.keys()):
            if addr in self.channel.address_to_connection.keys() and addr not in self.connected_servers:
                self.connected_servers.append(id)

            if addr not in self.channel.address_to_connection.keys() and id in self.connected_servers:
                self.connected_servers.remove(id)



id = int(sys.argv[1])
start_server(port=2000, id=id)




