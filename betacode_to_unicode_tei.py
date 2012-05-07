#!/usr/bin/env python3

import sys
from xml.etree import ElementTree
from betacode import betacode_to_unicode

if __name__ == '__main__':
    with open(sys.argv[1]) as in_f:
        in_s = in_f.read()
    tei = ElementTree.XML(in_s)
    text = tei.find('text')
    for node in text.iter():
        if node.text:
            node.text = betacode_to_unicode(node.text)
        if node.tail:
            node.tail = betacode_to_unicode(node.tail)
    out_s = ElementTree.tostring(tei, encoding='unicode')
    sys.stdout.write(out_s)
