import difflib


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
