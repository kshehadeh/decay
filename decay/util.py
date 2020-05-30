
def remove_leading_trailing_slashes(path):
    """
    This will change strings like these examples:
        /my/path/   >   my/path
        /my/path    >   my/path
        my/path     >   my/path
        /           >   /
        thispath/   >   thispath
        /thispath   >   thispath

    :param path:
    :return:
    """
    if not path or len(path) == 1:
        return path

    if path[0] == "/":
        path = path[1:]

    if path[-1] == "/":
        path = path[0:-1]

    return path
