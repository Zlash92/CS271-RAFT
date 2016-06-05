import constants

"""
type: identifies the type of message
"""


class RequestVoteMessage:

    """
    Invoked by candidates to gather votes

    candidate_id: candidate requesting vote
    term: candidate's term
    last_log_index: index of candidate's last log entry
    last_log_term: term of candidate's last log entry
    """

    def __init__(self, candidate_id, term, last_log_index, last_log_term):
        self.type = constants.MESSAGE_TYPE_REQUEST_VOTE
        self.candidate_id = candidate_id
        self.term = term
        self.last_log_index = last_log_index
        self.last_log_term = last_log_term


class AppendEntriesMessage:

    """
    Invoked by leader to replicate log entries and discover inconsistencies; also used as heartbeat

    term: leader's term
    leader_id: so follower can redirect clients
    prev_log_index: index of log entry immediately preceding new ones
    prev_log_term: term of prev_log_index entry
    entries: log entries to store (empty for heartbeat)
    commit_index: last entry known to be committed

    """

    def __init__(self, term, leader_id, prev_log_index, prev_log_term, entries, commit_index):
        self.type = constants.MESSAGE_TYPE_APPEND_ENTRIES
        self.term = term
        self.leader_id = leader_id
        self.prev_log_index = prev_log_index
        self.prev_log_term = prev_log_term
        self.entries = entries
        self.commit_index = commit_index

    def is_heartbeat(self):
        if not self.entries:
            return True
        else:
            return False


class VoteReplyMessage:

    """
    Sent by followers to candidates who send RequestVoteMessage

    term: for candidate to update itself if necessary
    vote_granted: true means candidate received vote
    """

    def __init__(self, follower_id, term, vote_granted):
        self.type = constants.MESSAGE_TYPE_VOTE_REPLY
        self.follower_id = follower_id
        self.term = term
        self.vote_granted = vote_granted

class RequestLeaderMessage:

    """
    Sent by clients to connected server to get know which server is the leader
    """

    def __init__(self, msg_id=None, leader=-1):
        self.type = constants.MESSAGE_TYPE_REQUEST_LEADER
        self.msg_id = msg_id
        self.leader = leader


class LookupMessage:
    """
    Sent by client to request the blog post from the connected server (leader)
    """
    def __init__(self, msg_id, entry=None):
        self.type = constants.MESSAGE_TYPE_LOOKUP
        self.msg_id = msg_id
        self.entry = entry


class PostMessage:
    """
    Sent by client to post blog post on the connected server (leader)
    """
    def __init__(self, msg_id, post):
        self.type = constants.MESSAGE_TYPE_POST
        self.msg_id = msg_id
        self.post = post


class AcknowledgeMessage:
    """
    Message awknowledging the receive of a message
    """
    def __init__(self, ack=True):
        self.type = constants.MESSAGE_TYPE_ACKNOWLEDGE
        self.ack = ack

class TextMessage:

    def __init__(self, sender_id, msg):
        self.type = constants.MESSAGE_TYPE_TEXT
        self.sender_id = sender_id
        self.msg = msg
