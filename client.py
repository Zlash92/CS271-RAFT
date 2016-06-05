import tcp

port = 2000
addr_to_id = {('52.37.112.251', port): 0, ('52.40.128.229', port): 1, ('52.41.5.151', port): 2}
id_to_addr = {0: ('52.37.112.251', port), 1: ('52.40.128.229', port), 2: ('52.41.5.151', port)}
host_to_id = {'52.37.112.251': 0, '52.40.128.229': 1, '52.41.5.151': 2}
id_to_host = {0: '52.37.112.251', 1: '52.40.128.229', 2: '52.41.5.151'}


class Client(object):

    def __init__(self):
        self.server_connection = tcp.Network(0, 'client')
        self.server_connection.start()
        self.connected_to_id = None
        self.leader = None
        self.running = True
        self.connect_to_leader()
        self.run()

    def run(self):
        while self.running:
            pass

    def connect_to_leader(self):
        for server in list(addr_to_id.keys()):
            success = self.server_connection.connect(server)
            if success:
                self.connected_to_id = addr_to_id[server]
                self.leader = addr_to_id[server]
                print "Connected to server with id=", addr_to_id[server], " and address ", server
                break

        print "Request leader"
        msg = 'request_leader'
        self.send(msg, 0)
        ans = int(self.wait_for_ans(2.5))
        print ans
        if ans != self.leader:
            self.leader = ans
            self.server_connection.connect(id_to_addr[self.leader])
            print "Connected to leader with id=", self.leader

    def send(self, msg, id):
        self.server_connection.send(msg, id=id)

    def wait_for_ans(self, timeout=0.0):
        message = self.server_connection.receive(timeout)
        if message:
            print "Length msg: ", len(message)
            for id, msg in message:
                print id, " : ", msg
                return msg



client = Client()






