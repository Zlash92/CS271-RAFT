import socket
import sys
import time
import threading

# s = socket.socket()
# host = socket.gethostbyname(socket.gethostname())
# print host
#
# print sys.argv[1]
# print sys.argv[2]

# print time.time()


s = socket.socket()
s.bind((socket.gethostname(), 19991))

# f = socket.socket()
# f.bind((socket.gethostname(), 18888))
#
# s.listen(3)
#
# s.accept()
# print "Connected"
# s.close()
# print "s closed"
#
# f.listen(3)
#
# f.accept()
#
# f.close()
# print "f closed"


# class ThreadTester(threading.Thread):
#
#     def __init__(self, name, sleep_time):
#         threading.Thread.__init__(self)
#         self.t = time.time()
#         self.count = 0
#         self.name = name
#         self.sleep_time = sleep_time
#
#     def run(self):
#         while True:
#             print(self.name, self.count)
#             self.count += 1
#             time.sleep(self.sleep_time)
#
# t1 = ThreadTester("Thread1", 2)
# t2 = ThreadTester("Thread2", 10)
#
# t1.start()
# t2.start()

log = []