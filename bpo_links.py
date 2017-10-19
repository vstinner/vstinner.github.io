#!/usr/bin/env python3
import re
import sys


FMT_BPO_URL = 'https://bugs.python.org/issue%s'


def replace_bpo(regs):
    text = regs.group(0)
    bpo_id = regs.group(1)
    url = FMT_BPO_URL % bpo_id
    return '`%s <%s>`__' % (text, url)


def main():
    filename = sys.argv[1]
    with open(filename, encoding='utf8') as fp:
        content = fp.read()

    content = re.sub('bpo-([0-9]{2,6})', replace_bpo, content)

    with open(filename, 'w', encoding='utf8') as fp:
        fp.write(content)
        fp.flush()


if __name__ == "__main__":
    main()
