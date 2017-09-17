"""Takes array of filenames as input, concatenates their contents into a string
and prints this string to stdout.
"""


if __name__ == '__main__':
    import sys
    filenames = sys.argv[1:]
    parts = []
    for filename in filenames:
        with open(filename, 'r') as f:
            if filename.split('/')[-1] == 'toc.md':
                parts.append('## Contents\n' + f.read())
            else:
                parts.append(f.read())
    content = '\n\n'.join(parts)
    if content[-1] == '\n':  # redirection will automatically add a trailing new-line to file
        content = content[:-1]
    print(content)
