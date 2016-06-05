import Queue
import threading

import sys

import tcp

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
        self.role = 'follower'
        self.channel = tcp.Network(port, id)
        self.channel.start()
        self.leader = None
        self.connected_peers = []
        self.setup()
        threading.Thread.__init__(self)

    #Temp setup for testing purposes
    def setup(self):
        if self.id == 1:
            self.role = 'leader'
        self.leader = 1


    def run(self):

        print "Server with id=", self.id, " up and running"
        self.running = True
        while self.running:
            for peer in list(addr_to_id.keys()):
                # if peer not in self.connected_peers and not addr_to_id[peer] == id:
                if peer not in self.channel and not host_to_id[peer[0]] == self.id:
                    connected = self.channel.connect(peer)
                    if connected:
                        print str("Server: Connected to "+peer[0])
                        self.connected_peers.append(peer)
                    # print "Connected: ", connected
                message = self.channel.receive(2.0)
                if message:
                    for id, msg in message:
                        self.process_msg(id, msg)
                else:
                    msg = 'hearbeat from ' + str(self.id)
                    if self.role == 'leader':
                        for peer in self.connected_peers:
                            self.channel.send(msg, id=host_to_id[peer[0]])
                            print "sent msg to ", peer[0]

    def process_msg(self, id, msg):
        if not msg:
            return
        print msg
        if msg=='request_leader':
            response_msg = str(self.leader)
            print "Sending leader response msg: ", response_msg
            self.channel.send(response_msg, id=id)

id = int(sys.argv[1])
start_server(port=2000, id=id)




