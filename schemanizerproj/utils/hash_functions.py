import mmh3


def generate_hash(s):
    """Generates hash for the string argument."""

    k1, k2 = mmh3.hash64(s)
    anded = 0xFFFFFFFFFFFFFFFF
    return '%016x%016x' % (k1 & anded, k2 & anded)
