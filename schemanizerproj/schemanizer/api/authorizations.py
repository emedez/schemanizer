from tastypie.authorization import ReadOnlyAuthorization

class ChangesetAuthorization(ReadOnlyAuthorization):
    def __init__(self):
        super(ChangesetAuthorization, self).__init__()