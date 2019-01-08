#!/usr/bin/env python3
import re
import sys


FMT_BPO_URL = 'https://bugs.python.org/issue%s'
FMT_COMMIT_URL = 'https://github.com/python/cpython/commit/%s'
FMT_PEP_URL = 'https://www.python.org/dev/peps/pep-%04d/'
FMT_RAW_PEP_URL = 'https://raw.githubusercontent.com/python/peps/master/pep-%04d.txt'


def replace_bpo(regs):
    text = regs.group(0)
    bpo_id = regs.group(1)
    url = FMT_BPO_URL % bpo_id
    return '`%s <%s>`__' % (text, url)


def replace_commit(regs):
    commit_id = regs.group(1)
    url = FMT_COMMIT_URL % commit_id
    text = commit_id[:8]
    return '`commit %s <%s>`__' % (text, url)


def replace_pep(regs):
    text = regs.group(0)
    number = int(regs.group(1))
    url = FMT_PEP_URL % number
    raw_url = FMT_RAW_PEP_URL % number
    content = requests.get(raw_url).text
    title = None
    for line in content.splitlines():
        if line.startswith('Title: '):
            title = line[7:].strip()
            break
    else:
        raise Exception("failed to find PEP title from %s" % raw_url)
    return '`%s "%s" <%s>`__' % (text, title, url)


def main():
    filename = sys.argv[1]
    with open(filename, encoding='utf8') as fp:
        content = fp.read()

    old_content = content
    content = re.sub(r'(?<!    )(?<!`)bpo-([0-9]{2,6})', replace_bpo, content)
    content = re.sub(r'(?<!  )commit ([0-9a-f]{40})', replace_commit, content)
    content = re.sub(r'(?<!`)PEP ([0-9]{1,4})', replace_pep, content)

    if content != old_content:
        print("Write %s" % filename)
        with open(filename, 'w', encoding='utf8') as fp:
            fp.write(content)
            fp.flush()
    else:
        print("No change")


if __name__ == "__main__":
    main()
