import difflib
import hashlib
import time


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