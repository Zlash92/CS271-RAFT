import pickle


class Storage:

    def __init__(self, voted_for, term, log):
        self.voted_for = voted_for
        self.term = term
        self.log = log


def save(server_id, voted_for, term, log):
    state = Storage(voted_for, term, log)
    pfile = "raft-state-server-%d.pickle" % server_id

    with open(pfile, 'wb') as handle:
        pickle.dump(state, handle)


def load(server_id):
    pfile = "raft-state-server-%d.pickle" % server_id
    try:
        with open(pfile, 'rb') as handle:
            state = pickle.load(handle)

        return state.voted_for, state.term, state.log

    except IOError:
        pass

    return None, 0, None


def reset_server(server_id):
    state = Storage(None, 0, None)
    pfile = "raft-state-server-%d.pickle" % server_id

    with open(pfile, 'wb') as handle:
        pickle.dump(state, handle)
