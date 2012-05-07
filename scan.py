#!/usr/bin/env python3

import re
import unicodedata
import hexameter

_CONSONANT = 0
_VOWEL = 1
_DIACRITICAL = 2
_OTHER = -1

_SHORT = 1
_LONG = 2

_CONSONANTS = [
    '\u03b2', # beta
    '\u03b3', # gamma
    '\u03b4', # delta
    '\u03b6', # zeta
    '\u03b8', # theta
    '\u03ba', # kappa
    '\u03bb', # lambda
    '\u03bc', # mu
    '\u03bd', # nu
    '\u03be', # xi
    '\u03c0', # pi
    '\u03c1', # rho
    '\u03c2', # final sigma
    '\u03c3', # medial sigma
    '\u03c4', # tau
    '\u03c6', # phi
    '\u03c7', # chi
    '\u03c8', # psi
    '\u03dd', # digamma
    '\u03f2', # lunate sigma
    ]
_VOWELS = [
    '\u03b1', # alpha
    '\u03b5', # epsilon
    '\u03b7', # eta
    '\u03b9', # iota
    '\u03bf', # omicron
    '\u03c5', # upsilon
    '\u03c9', # omega
    ]
_DIACRITICALS = [
    '\u0313', # smooth breathing
    '\u0314', # rough breathing
    '\u0301', # acute
    '\u0342', # circumflex
    '\u0300', # grave
    '\u0308', # diaeresis
    '\u0345', # iota subscript
    '\u0323', # dot below
    ]
_CHAR_TYPE_MAP = {}
_CHAR_TYPE_MAP.update({c: _CONSONANT for c in _CONSONANTS})
_CHAR_TYPE_MAP.update({c.upper(): _CONSONANT for c in _CONSONANTS})
_CHAR_TYPE_MAP.update({c: _VOWEL for c in _VOWELS})
_CHAR_TYPE_MAP.update({c.upper(): _VOWEL for c in _VOWELS})
_CHAR_TYPE_MAP.update({c: _DIACRITICAL for c in _DIACRITICALS})

def _get_char_type(c):
    return _CHAR_TYPE_MAP.get(c, _OTHER)

def _get_glyph_type(g):
    return _get_char_type(g[0])

def _get_cluster_type(g):
    return _get_char_type(g[0])

def _glyphs(s):
    glyphs = []
    for c in s:
        if _get_char_type(c) == _DIACRITICAL:
            glyphs[-1] += c
        else:
            glyphs.append(c)
    return glyphs

def _strip_diacriticals(cluster):
    return ''.join(c for c in cluster
                   if _get_char_type(c) != _DIACRITICAL)

_VOWEL_LENGTH_MAP = {
    '\u03b5': hexameter.SHORT, # epsilon
    '\u03b7': hexameter.LONG, # eta
    '\u03bf': hexameter.SHORT, # omicron
    '\u03c9': hexameter.LONG, # omega
}

_LONG_CONSONANTS = [
    '\u03b6', # zeta
    '\u03be', # xi
    '\u03c8', # psi
    ]

_DIPHTHONGS = [
    '\u03b1\u03b9', # alpha iota
    '\u03b1\u03c5', # alpha upsilon
    '\u03b5\u03b9', # epsilon iota
    '\u03b5\u03c5', # epsilon upsilon
    '\u03b7\u03c5', # eta upsilon
    '\u03bf\u03b9', # omicron iota
    '\u03bf\u03c5', # omicron upsilon
    '\u03c5\u03b9', # upsilon iota
    ]

def _valid_diphthong(glyph1, glyph2):
    unaccented = glyph1[0] + glyph2[0]
    return (unaccented in _DIPHTHONGS)

def _cluster(glyphs):
    clusters = []
    for g in glyphs:
        if not clusters:
            clusters.append(g)
            continue

        last_glyph_type = _get_glyph_type(clusters[-1])
        glyph_type = _get_glyph_type(g)
        if glyph_type != last_glyph_type:
            clusters.append(g)
            continue

        if glyph_type != _VOWEL:
            clusters[-1] += g
            continue

        # otherwise we have a vowel. is it a diphthong?
        if len(clusters[-1]) > 1:
            # if the vowel cluster in progress has accents or multiple
            # letters, then it doesn't combine with this glyph as a
            # diphthong.
            clusters.append(g)
        elif '\u0308' in g: # diaeresis
            # if the current glyph contains a diaeresis, then it doesn't
            # combine with the cluster in progress as a diphthong.
            clusters.append(g)
        elif _valid_diphthong(clusters[-1], g):
            # create diphthongs out of recognized vowel clusters
            clusters[-1] += g
        else:
            # otherwise this isn't a diphthong. make it a separate cluster.
            clusters.append(g)
    return clusters

def _metrical_length(clusters, i):
    c = clusters[i]
    if _get_cluster_type(c) != _VOWEL:
        # if you're not a vowel, you don't get counted directly in
        # metrical analysis.
        return (c, '')

    unaccented = _strip_diacriticals(c)
    # natural length
    if len(unaccented) > 1:
        # diphthong
        length = hexameter.LONG
    else:
        length = _VOWEL_LENGTH_MAP.get(unaccented, hexameter.INDETERMINATE)

    # circumflex is always on a long
    if '\u0342' in c: # circumflex
        length = hexameter.LONG

    # take position into account
    if _followed_by_multiple_consonants(clusters, i):
        length = hexameter.LONG
    if _followed_by_vowel_in_next_word(clusters, i):
        # correption.
        if length == hexameter.LONG:
            length = hexameter.LONG_CORREPTION
        elif length == hexameter.INDETERMINATE:
            length = hexameter.INDETERMINATE_CORREPTION
    if (_synizesis_candidate(c) and
            _followed_by_vowel_in_same_word(clusters, i)):
        length = hexameter.SHORT_SYNIZESIS

    return (c, length)

# FIXME: is this the best way to check for synizesis?
_SYNIZESIS_CANDIDATES = [
    '\u03b5', # unaccented epsilon
    '\u03b5\u0301', # epsilon with acute
    ]

def _synizesis_candidate(cluster):
    return (cluster in _SYNIZESIS_CANDIDATES)

def _followed_by_multiple_consonants(clusters, i):
    consonant_count = 0
    i += 1
    while i < len(clusters):
        cluster_type = _get_cluster_type(clusters[i])
        if cluster_type == _VOWEL:
            return False
        elif cluster_type == _CONSONANT:
            stripped = _strip_diacriticals(clusters[i])
            for c in stripped:
                if c in _LONG_CONSONANTS:
                    consonant_count += 2
                elif consonant_count and c == '\u03c1': # rho
                    # consonant clusters with rho don't always lengthen the
                    # preceding vowel. e.g., Il. 1.201
                    pass
                else:
                    consonant_count += 1
            if consonant_count > 1:
                return True
        # skip "other" (space, punctuation) clusters.
        i += 1

    # if we haven't found them yet, they're not there.
    return False

def _followed_by_vowel_in_next_word(clusters, i):
    # there must be at least two more clusters: an other (space) and a vowel
    if i + 2 >= len(clusters):
        return False

    next_cluster_type = _get_cluster_type(clusters[i+1])
    following_cluster_type = _get_cluster_type(clusters[i+2])
    return (next_cluster_type == _OTHER and
            following_cluster_type == _VOWEL)

def _followed_by_vowel_in_same_word(clusters, i):
    # there must be at least one more cluster: a vowel
    if i + 1 >= len(clusters):
        return False

    next_cluster_type = _get_cluster_type(clusters[i+1])
    return (next_cluster_type == _VOWEL)


def scan(line):
    line = unicodedata.normalize('NFD', line)
    line = line.lower()
    glyphs = _glyphs(line)
    clusters = _cluster(glyphs)
    metrical_analysis = [_metrical_length(clusters, i)
                         for i in range(len(clusters))]
    analysis_s = ''.join(m[1] for m in metrical_analysis)
    normalizations = hexameter.normalize(analysis_s)
    if not normalizations:
        return []

    best_cost = normalizations[0][0]
    return [n[1] for n in normalizations
            if n[0] == best_cost]


def process_tei_file(fname, stats):
    from xml.etree import ElementTree
    with open(fname) as inf:
        in_s = inf.read()
    tei = ElementTree.XML(in_s)
    text = tei.find('text')
    for line_node in text.iter('l'):
        line = ''.join(line_node.itertext())
        stats['total_lines'] += 1
        scansion = scan(line)
        if not scansion:
            stats['no_match'] += 1
            print('ERROR: Failed to scan: ' + line)
        elif len(scansion) > 1:
            stats['multi_match'] += 1
            print(line + ' ' + ' OR '.join(scansion))
        else:
            stats['scanned'] += 1
            print(line + ' ' + scansion[0])


def process_line_stream(inf, stats):
    for line in inf:
        stats['total_lines'] += 1
        line = line.strip() # strip whitespace
        scansion = scan(line)
        if not scansion:
            stats['no_match'] += 1
            print('ERROR: Failed to scan: ' + line)
        elif len(scansion) > 1:
            stats['multi_match'] += 1
            print(' OR '.join(scansion))
        else:
            stats['scanned'] += 1
            print(scansion[0])

def report_stats(stats):
    print('Total lines scanned: %d' % (stats['total_lines'],))
    print('Success:             %s (%.1f%%)' % (stats['scanned'], stats_pct(stats, 'scanned')))
    print('Failed:              %s (%.1f%%)' % (stats['no_match'], stats_pct(stats, 'no_match')))
    print('Multiple matches:    %s (%.1f%%)' % (stats['multi_match'], stats_pct(stats, 'multi_match')))

def stats_pct(stats, field):
    percent = float(stats[field]) / float(stats['total_lines'])
    return percent * 100

if __name__ == '__main__':
    import sys
    args = sys.argv[1:]
    stats = {
        'total_lines': 0,
        'scanned': 0,
        'no_match': 0,
        'multi_match': 0,
    }
    if args:
        for fname in args:
            process_tei_file(fname, stats)
    else:
        process_line_stream(sys.stdin, stats)
    report_stats(stats)
