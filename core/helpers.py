import os


def truncate(s, l, ellipsis='...'):
    """Truncates string to length `l` if need be and adds `ellipsis`.
    """
    try:
        _l = len(s)
    except:
        return s

    if _l > l:
        try:
            return s[:l] + ellipsis  # in case s is a byte string
        except:
            return s[:l]
    return s


def clean_url(url):
    """Remove trailing slash and query string from `url`.
    """
    url = url.split('?')[0]
    if url and url[-1] == '/':
        return url[:-1]
    return url


def absolute_path(filename, view):
    if os.path.isabs(filename):
        return filename
    file_path = view.file_name()
    if file_path:
        return os.path.join(os.path.dirname(file_path), filename)
    return None


def get_transfer_indicator(filename, transferred, total, spaces=50):
    if not total:
        return '{}, ?'.format(filename)
    transferred = min(transferred, total)
    spaces_filled = int(spaces * transferred/total)
    return '{}, [{}] {}kB'.format(
        filename, '·'*spaces_filled + ' '*(spaces-spaces_filled-1), transferred//1024
    )
