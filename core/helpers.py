import sublime

import os


def truncate(s, l, ellipsis='…'):
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
    """Get absolute path to `filename` relative to view.
    """
    if os.path.isabs(filename):
        return filename
    file_path = view.file_name()
    if file_path:
        return os.path.join(os.path.dirname(file_path), filename)
    return None


def get_transfer_indicator(filename, transferred, total, spaces=50):
    """Returns progress indicator for byte stream transfer.
    """
    if not total:
        return '{}, ?'.format(filename)
    transferred = min(transferred, total)
    spaces_filled = int(spaces * transferred/total)
    return '{}, [{}] {}kB'.format(
        filename, '·'*spaces_filled + ' '*(spaces-spaces_filled-1), transferred//1024,
    )


def prepend_scheme(url):
    """Prepend scheme to URL if necessary.
    """
    if isinstance(url, str) and len(url.split('://')) == 1:
        scheme = sublime.load_settings('Requester.sublime-settings').get('scheme', 'http')
        return scheme + '://' + url
    return url


def is_instance(obj, s):
    """Is object an instance of class named `s`?
    """
    return s in str(type(obj))


def is_auxiliary_view(view):
    """Was view opened by a Requester command? This is useful, e.g., to
    avoid resetting `env_file` and `env_string` on these views.
    """
    if view.settings().get('requester.response_view', False):
        return True
    if view.settings().get('requester.test_view', False):
        return True
    return False
