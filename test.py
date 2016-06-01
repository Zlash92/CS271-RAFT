import socket
import sys
import time

# s = socket.socket()
# host = socket.gethostbyname(socket.gethostname())
# print host
#
# print sys.argv[1]
# print sys.argv[2]

# print time.time()


s = socket.socket()
s.bind((socket.gethostname(), 19991))

f = socket.socket()
f.bind((socket.gethostname(), 18888))

s.listen(3)

s.accept()
print "Connected"
s.close()
print "s closed"

f.listen(3)

f.accept()

f.close()
print "f closed"