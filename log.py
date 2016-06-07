

class Log:

    # TODO: Add persistence support when operating on log
    def __init__(self):
        self.data = []
        # TODO: Commit index
        self.last_commit_index = -1      # Index of last entry known to have committed
        self.msg_ids = set()               # Msg_ids of entries that have been appended. Used for avoiding duplicate entries

    def append(self, entry):
        # TODO PERSIST
        self.data.append(entry)
        self.msg_ids.add(entry.msg_id)

    def get(self, index):
        if index >= len(self.data):
            print "Error: Index out of bounds. Index is too high"
            return -1
        else:
            return self.data[index]

    # If an element is removed, remove all succeeding elements as well
    # (should already have been removed recursively)
    def remove(self, index):
        for i in range(index, len(self.data)):
            del self.data[i]

    def last_log_index(self):
        # If log is empty, last log index will be -1
        # If log contains one element, last log index will be 0
        return len(self.data)-1

    # Return True if there is an element at this index
    def contains_at_index(self, index):
        try:
            if self.data[index]:
                return True
        except:
            return False

    # Append entries from list
    def append_entries(self, entries):
        # TODO: PERSIST
        for e in entries:
            # TODO: Check if entry is new?
            self.data.append(e)

    def id_in_log(self, msg_id):
        if msg_id in self.msg_ids:
            return True
        else:
            return False

    def is_empty(self):
        if not self.data:
            return True
        else:
            return False

    def show_data(self):
        print "---------------------------"
        for entry in self.data:
            print "Post:", entry.post, ", Index:", entry.index
        print "---------------------------"

    def show_committed_entries(self):
        print "Show committed entries", "Last commit index for log is:", self.last_commit_index
        if self.is_empty():
            print "--- Blog is empty ---"
            return
        print "---------------------------"
        for i in range(self.last_commit_index+1):
            print "Post:", self.data[i].post, ", Index:", self.data[i].index
        print "---------------------------"

    def __len__(self):
        return len(self.data)

    def __nonzero__(self):
        return len(self.data) != 0


class Entry:

    """
    post: the blog post
    author: client socket address something
    term: in what term this entry was added
    index: index of entry in log
    msg_id: id of message, the entry is associated with. Client re-sends same message if no response
    """

    def __init__(self, post, author, term, index, msg_id, client_ack_sent=False):
        self.post = post
        self.author = author

        self.term = term
        self.index = index
        self.msg_id = msg_id
        self.client_ack_sent = client_ack_sent


