


class Log:

    # TODO: Add persistence support when operating on log
    def __init__(self):
        self.data = []
        self.last_commit_index = 0      # Index of last entry known to have committed

    def append(self, entry):
        self.data.append(entry)

    def get(self, index):
        return self.data[-1]

    def last_log_index(self):
        return len(self.data)-1

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

    def __init__(self, post, author, term, index, msg_id):
        self.post = post
        self.author = author

        self.term = term
        self.index = index
        self.msg_id = msg_id

