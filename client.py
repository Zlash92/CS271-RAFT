import network
import messages
import constants
import uuid
import log

from aws_instances import id_to_addr
from aws_instances import addr_to_id
from aws_instances import host_to_id
from aws_instances import id_to_host
from aws_instances import port


class Client(object):

    def __init__(self):
        self.server_connection = network.Network(0, 'client')
        self.server_connection.start()
        self.connected_to_id = None
        self.leader = None
        self.running = True
        self.connect_to_leader()
        self.run()

    def run(self):
        while self.running:
            msg = raw_input('Enter message: ')
            inp = msg.split(' ', 1)
            if msg == 'close':
                self.running = False
                break
            elif inp[0] == 'lookup':
                msg_id = uuid.uuid1()
                if len(inp) == 2 and int(inp[1]) in id_to_addr.keys():
                    send_id = int(inp[1])
                    self.lookup(msg_id=msg_id, send_id=send_id)
                else:
                    self.lookup(msg_id=msg_id)
            elif msg[:5] == 'post ':
                msg_id = uuid.uuid1()
                self.post(msg=msg[5:], msg_id=msg_id)
            else:
                print "Invalid input. Try again."
        self.close()

    def connect_to_leader(self):
        for server in list(addr_to_id.keys()):
            success = self.server_connection.connect(server)
            if success:
                self.connected_to_id = addr_to_id[server]
                self.leader = addr_to_id[server]
                print "Connected to server with id=", self.leader, " and address ", server
                break

        print "Request leader"
        print self.leader
        msg = messages.RequestLeaderMessage()
        self.send(msg)
        msg = self.wait_for_ans(2.0)
        if not msg:
            print "No msg"
            self.connect_to_leader()

        elif msg.type != constants.MESSAGE_TYPE_REQUEST_LEADER:
            print "error: ", msg.type

        elif msg.leader != self.leader:
            print "response leader: ", msg.leader
            self.connect(msg.leader)
        else:
            print "Already connected to leader"

    def connect(self, leader_id):
        self.leader = leader_id
        success = self.server_connection.connect(id_to_addr[self.leader])
        if success:
            print "Connected to leader with id=", self.leader

        else:
            self.connect_to_leader()

    def connect_to_other(self, server_id):
        success = self.server_connection.connect(id_to_addr[server_id])
        if success:
            print "Connected to server with id=", server_id
        else:
            print "Failed to connect"

    def send(self, msg, send_id=None):
        if send_id:
            self.server_connection.send(msg, id=send_id)
        else:
            self.server_connection.send(msg, id=self.leader)

    def wait_for_ans(self, timeout=0.0):
        message = self.server_connection.receive(timeout)
        if message:
            for id, msg in message:
                return msg

    def close(self):
        self.server_connection.close()

    def lookup(self, msg_id, send_id=None):

        if send_id is not None:
            msg = messages.LookupMessage(msg_id, override=True)
            if send_id not in self.server_connection:
                print "noe"
                self.connect_to_other(send_id)
            print "sent to ", send_id
            self.send(msg, send_id=send_id)
        else:
            msg = messages.LookupMessage(msg_id)
            self.send(msg)

        response = self.wait_for_ans(1.0)
        if not response:
            self.lookup(msg_id, send_id)
            print "Timeout. Trying again ..."
        elif response.type == constants.MESSAGE_TYPE_REQUEST_LEADER:
            self.connect(response.leader)
            print "Not leader. Connecting to leader and trying again ..."
            self.lookup(msg_id, send_id)
        elif response.type == constants.MESSAGE_TYPE_LOOKUP:
            #TODO : Show print from correct server
            posts = response.post
            server = response.server_id
            print "-------------------------------"
            print "Showing posts from server = ", server
            for i in range(len(posts)):
                print i, " : ", posts[i]
        else:
            print "ELSE: ", response

    def post(self, msg, msg_id):
        data = messages.PostMessage(msg_id, msg)
        self.send(data)
        ack = self.wait_for_ans(3.0)

        if not ack:
            print "Timeout! Trying again ... "
            self.post(msg, msg_id)  # Try again

        elif ack.type == constants.MESSAGE_TYPE_REQUEST_LEADER:
            self.connect(msg.leader)
            print "Not leader. Connecting to leader and trying again ..."
            self.post(msg, msg_id)

        else:
            print "Ack: ", ack.ack


client = Client()






