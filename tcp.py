import socket
import select
import thread
import errno
import pickle
import uuid


# port = 1780
# address_to_id = {('52.37.112.251', port): 0, ('52.40.128.229', port): 1, ('52.41.5.151', port): 2}
# id_to_address = {0: ('52.37.112.251', port), 1: ('52.40.128.229', port), 2: ('52.41.5.151', port)}
host_to_id = {'52.37.112.251': 0, '52.40.128.229': 1, '52.41.5.151': 2}
id_to_host = {0: '52.37.112.251', 1: '52.40.128.229', 2: '52.41.5.151'}


class Network(object):

    def __init__(self, port, id):
        self.port = port
        self.id = id
        self.connections = []
        self.connection_to_id = {}
        self.connection_to_address = {}
        self.address_to_connection = {}
        self.id_to_connection = {}

    def __contains__(self, id):
        return id in self.id_to_connection

    def start(self):

        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("", self.port))
        thread.start_new_thread(self.accept, ())

    def map_connection(self, connection, address):
        if address[0] in host_to_id.keys():
            id = host_to_id[address[0]]
        else:
            id = self.getUniqueID()
        self.connection_to_id[connection] = id
        self.connection_to_address[connection] = address
        self.address_to_connection[address] = connection
        self.id_to_connection[id] = connection

    def getUniqueID(self):
        id = uuid.uuid1()
        return id


    def accept(self):
        self.server_socket.listen(5)
        while self.running:
            try:
                connection, address = self.server_socket.accept()
                print "Accepted connection from ", address[0]
                self.map_connection(connection, address)
                connection.setblocking(0)
                # self.add_unknown(connection)
            except socket.error as e:
                if e.errno == errno.ECONNABORTED:
                    continue

    def connect(self, address):
        if address in self.address_to_connection:
            return
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            connection.connect(address)
        except socket.error as e:
            if e.errno == errno.ECONNREFUSED:
                return False
        connection.setblocking(0)
        self.map_connection(connection, address)

        return True

    def receive(self, timeout=0):
        try:
            incoming, _, _ = select.select(list(self.connection_to_id.keys()), [], [], timeout)
        except select.error as e:
            if e.args[0] == errno.EINTR:
                print e
                return
            raise
        received = []
        for connection in incoming:
            connection_messages = self.read_msg(connection)
            if connection_messages is not None:
                id = self.connection_to_id[connection]
                received.append((id, connection_messages))
        return received

    def read_msg(self, connection):
        try:
            data = connection.recv(4096)
        except socket.error:
            return
        # TODO: processing of msg
        msg = pickle.loads(data)
        return msg

    def send(self, msg, address=None, id=-1):
        data = pickle.dumps(msg)

        try:
            if id == -1:
                connection = self.address_to_connection[address]
            else:
                connection = self.id_to_connection[id]
        except KeyError:
            return

        try:
            connection.send(data)

        except socket.error as e:
            print e
