#!/usr/bin/env python3
import re
import sys


FMT_BPO_URL = 'https://bugs.python.org/issue%s'
FMT_COMMIT_URL = 'https://github.com/python/cpython/commit/%s'


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


def main():
    filename = sys.argv[1]
    with open(filename, encoding='utf8') as fp:
        content = fp.read()

    old_content = content
    content = re.sub(r'(?<!    )(?<!`)bpo-([0-9]{2,6})', replace_bpo, content)
    content = re.sub(r'(?<!    |`)commit ([0-9a-f]{3,40})', replace_commit, content)

    if content != old_content:
        print("Write %s" % filename)
        with open(filename, 'w', encoding='utf8') as fp:
            fp.write(content)
            fp.flush()
    else:
        print("No change")


if __name__ == "__main__":
    main()
