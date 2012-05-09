#!/usr/bin/env python

'''Index hexameter lines from a TEI file in solr.'''

import unicodedata
from xml.etree import ElementTree
import sunburnt

def index_file(fname, solr_url):
    solr = sunburnt.SolrInterface(solr_url)

    with open(fname) as inf:
        in_s = inf.read()
    tei = ElementTree.XML(in_s)
    work_name, work_abbrev = identify_work(tei)

    text = tei.find('text')
    book_num = None
    line_num = 0
    for node in text.iter():
        if node.tag == 'div1' and node.get('type') == 'Book':
            # new book. update our location.
            book_num = node.get('n')
            print('Indexing %s book %s' % (work_name, book_num))
            line_num = 0
        elif node.tag == 'l':
            # line. index it.
            if node.get('n'):
                line_num = int(node.get('n'))
            else:
                line_num += 1

            scansion_val = node.get('real')
            if scansion_val:
                scansion = scansion_val.split(' OR ')
            else:
                scansion = []

            line_text = ''.join(node.itertext())
            caesura_node = node.find('caesura')
            if caesura_node is not None:
                after_caesura = caesura_node.tail
                before_caesura = line_text[:-len(after_caesura)]
            else:
                after_caesura = None
                before_caesura = None

            # FIXME: having a lot of difficulty getting solr to index and
            # search this text unless it's NFC all the way through, even if
            # the appropriate filters are set in the solr schema. for now,
            # convert it all to NFC herE.
            line_text = unicodedata.normalize('NFC', line_text)
            if before_caesura:
                before_caesura = unicodedata.normalize('NFC', before_caesura)
            if after_caesura:
                after_caesura = unicodedata.normalize('NFC', after_caesura)

            line_data = {
                'lineid': '%s.%s.%d' % (work_abbrev, book_num, line_num),
                'work_name': work_name,
                'book_num': book_num,
                'line_num': line_num,
                'line_text': line_text,
                'scansion': scansion,
                'before_caesura': before_caesura,
                'after_caesura': after_caesura,
            }

            solr.add(line_data)
    solr.commit()

# FIXME: either find a better way to identify the title, or else make the
# user enter them at the command line
def identify_work(tei):
    title_node = tei.find('teiHeader/fileDesc/titleStmt/title')
    title = title_node.text

    if 'Iliad' in title:
        return ('Iliad', 'Il')
    elif 'Odyssey' in title:
        return ('Odyssey', 'Od')


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print('Usage: %s solr_url file.xml ...')
    solr_url = sys.argv[1]
    fnames = sys.argv[2:]
    for fname in fnames:
        index_file(fname, solr_url)
