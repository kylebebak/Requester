"""Takes filename as input, creates a Markdown table of contents from its Markdown
headers, and prints TOC to stdout.
"""
import re


def get_headers(s):
    """Returns header tuples with text and indentation level.
    """
    PATTERN = '###* (?=\w)'
    matches = []
    for line in s.splitlines():
        m = re.match(PATTERN, line)
        if m is None:
            continue
        indent = m.group().count('#') - 2
        text = line[m.end():]
        matches.append((text, indent))
    return matches


def get_contents(s):
    """Parses string to create a Markdown table of contents pointing to heading
    anchors.
    """
    matches = get_headers(s)
    headers = []
    list_chars = ['-', '+', '*']
    for text, indent in matches:
        link_text = re.sub(r'[^\w ]', '', text)
        link_text = re.sub(r' +', '-', link_text).lower()
        header = '{}{} [{}](#{})'.format('  '*indent, list_chars[indent % 3], text, link_text)
        headers.append(header)
    return '\n'.join(headers)


if __name__ == '__main__':
    import sys
    filename = sys.argv[1]
    contents = '## Contents\n'
    with open(filename, 'r') as f:
        contents += get_contents(f.read())
        print(contents)
