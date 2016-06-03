


class Entry:

    def __init__(self, post, author, parent_server_id, term):
        self.post = post
        self.author = author
        self.parent_server_id = parent_server_id
        self.term = term


    def get_term(self):
        return self.term