import pickle

class Storage:

    def __init__(self, voted_for, term, log):
        self.voted_for = voted_for
        self.term = term
        self.log = log


def save(server_id, voted_for, term, log):
    state = Storage(voted_for, term, log)
    file = "/tmp/state-server-%d.pickle" % server_id

    with open(file, 'wb') as handle:
        pickle.dump(state, handle)


def load(server_id):
    file = "/tmp/state-server-%d.pickle" % server_id
    with open(file, 'rb') as handle:
        state = pickle.load(handle)

    return state.voted_for, state.term, state.log