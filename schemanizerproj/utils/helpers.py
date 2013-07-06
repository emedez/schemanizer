import difflib
import hashlib
import random
import string
import time


# ref: http://stackoverflow.com/questions/712460/interpreting-number-ranges-in-python
#
# return a set of selected values when a string in the form:
# 1-4,6
# would return:
# 1,2,3,4,6
# as expected...
def parse_int_set(nputstr=""):
    selection = set()
    invalid = set()
    # tokens are comma seperated values
    tokens = [x.strip() for x in nputstr.split(',')]
    for i in tokens:
        if len(i) > 0:
            if i[:1] == "<":
                i = "1-%s" % (i[1:])
        try:
            # typically tokens are plain old integers
            selection.add(int(i))
        except:
            # if not, then it might be a range
            try:
                token = [int(k.strip()) for k in i.split('-')]
                if len(token) > 1:
                    token.sort()
                    # we have items seperated by a dash
                    # try to build a valid range
                    first = token[0]
                    last = token[len(token)-1]
                    for x in range(first, last+1):
                        selection.add(x)
            except:
                # not an int and not a range...
                invalid.add(i)
    # Report invalid tokens before returning valid selection
    #if len(invalid) > 0:
    #    print "Invalid set: " + str(invalid)
    return selection
# end parse_int_set


def random_string(size=8):
    return ''.join(random.choice(string.letters + string.digits) for x in range(size))


def get_model_instance(obj, model_class):
    """Helper function to return a model instance if the given obj is a primary key."""

    if type(obj) in (int, long):
        return model_class.objects.get(pk=obj)
    else:
        return obj


def generate_delta(from_string, to_string, fromfile='from', tofile='to'):
    from_string_lines = from_string.splitlines(True)
    to_string_lines = to_string.splitlines(True)
    delta = [
        line for line in difflib.context_diff(
            from_string_lines, to_string_lines,
            fromfile=fromfile, tofile=tofile)]
    return ''.join(delta)


def generate_request_id(request):
    """Create a unique ID for the request."""

    s = hashlib.sha1()
    s.update(str(time.time()))
    s.update(request.META['REMOTE_ADDR'])
    s.update(request.META['SERVER_NAME'])
    s.update(request.get_full_path())
    h = s.hexdigest()
    #l = long(h, 16)

    # shorten ID
    #tag = struct.pack('d', l).encode('base64').replace('\n', '').strip('=')
    return h