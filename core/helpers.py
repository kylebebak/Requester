def truncate(s, l, ellipsis='...'):
    """Truncates string to length `l` if need be and adds `ellipsis`.
    """
    if len(s) > l:
        return s[:l] + ellipsis
    return s


def clean_url(url):
    """Remove trailing slash and query string from `url`.
    """
    url = url.split('?')[0]
    if url and url[-1] == '/':
        return url[:-1]
    return url
