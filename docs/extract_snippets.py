# -*- coding: utf-8 -*-

import os

from docutils.core import publish_doctree
from docutils.nodes import literal_block


def extract_snippets(filename):
    with open(filename, 'r') as fp:
        doctree = publish_doctree(fp.read())

    for part in doctree.traverse(literal_block):
        if not part.attributes.get('classes', None) == ['code', 'python']:
            continue
        yield part.rawsource


def main(doc_folder=None):
    if doc_folder is None:
        doc_folder = os.getcwd()

    join = os.path.join

    snippet_folder = join(doc_folder, '_snippets')

    print('Scanning %s' % doc_folder)
    print('Extracting snippets to %s' % snippet_folder)

    for root, dirs, files in os.walk(doc_folder, topdown=True):
        dirs[:] = [d for d in dirs
                   if d[0] != '_' and d not in ('drivers', 'api')]

        dst_folder = join(snippet_folder, root[(len(doc_folder)+1):])

        try:
            os.mkdir(dst_folder)
        except:
            pass

        for name in files:
            if not name.endswith('.rst'):
                continue

            for ndx, snippet in enumerate(extract_snippets(join(root, name))):
                with open(join(dst_folder, '%s_%02d.py' % (name, ndx)), 'w', encoding='utf-8') as fo:
                    fo.write(snippet)

if __name__ == '__main__':
    main()
