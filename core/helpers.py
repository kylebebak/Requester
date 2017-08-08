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
