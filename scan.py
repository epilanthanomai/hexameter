#!/usr/bin/env python3

import re
import unicodedata
from xml.etree import ElementTree

import hexameter

###
### constants and handy definitions
###

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

_SYNIZESIS_CANDIDATES = [
    '\u03b5', # unaccented epsilon
    '\u03b5\u0301', # epsilon with acute
    ]

###
### utility functions
###

def _get_char_type(c):
    return _CHAR_TYPE_MAP.get(c, _OTHER)

def _get_glyph_type(g):
    return _get_char_type(g[0])

def _get_cluster_type(g):
    return _get_char_type(g[0])

def _strip_diacriticals(cluster):
    return ''.join(c for c in cluster
                   if _get_char_type(c) != _DIACRITICAL)

def _valid_diphthong(glyph1, glyph2):
    unaccented = glyph1[0] + glyph2[0]
    return (unaccented in _DIPHTHONGS)

###
### initial clustering
###

def _glyphs(s):
    glyphs = []
    for c in s:
        if _get_char_type(c) == _DIACRITICAL:
            glyphs[-1] += c
        else:
            glyphs.append(c)
    return glyphs

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

###
### syllable length analysis
###

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
                    # preceding vowel. e.g., Il. 1.201.
                    # FIXME: but sometimes they do. e.g., Od. 14.540
                    # "epese prosthe"
                    # FIXME: sigma + consonant also frequently doesn't
                    # lengthen preceding vowel. e.g., Il. 2.465 "skamandrion"
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

###
### identify ceasura
###

def _merge_scansion(metrical_analysis, scansion):
    '''Merge preliminary metrical analysis from this module with a scansion
    provided by :func:`scan.normalize`. 

    :param metrical_analysis: list of tuples containing a character
        cluster and the preliminary metrical analysis of that cluster prior
        to final line-based scansion.
    :param scansion: string representing a final scansion for the line. It
        contains one metrical marking (+-.) for each vowel cluster plus |
        for foot markers.
    :rtype: list of tuples containing a character cluster, preliminary
        metrical analysis, and final metrical analysis from scansion.
    '''
    # we approach this like a zipper with a few missing teeth: pull items
    # from the front of each input, matching them up where they fit.
    result = []
    while metrical_analysis and scansion:
        if scansion[0] == hexameter.FOOT:
            # squeeze it into the output. it has no matching letter cluster.
            result.append(('', '', scansion[0]))
            scansion = scansion[1:] # consume that character
            continue

        cluster, prelim = metrical_analysis[0]
        # if there was a preliminary analysis of this cluster, then the
        # scansion has a character for it.
        if prelim:
            result.append((cluster, prelim, scansion[0]))
            metrical_analysis = metrical_analysis[1:]
            scansion = scansion[1:]
            continue

        # otherwise this cluster is a consonant or space and doesn't
        # contribute to scansion. copy it to the result without a scansion.
        result.append((cluster, prelim, ''))
        metrical_analysis = metrical_analysis[1:]

    # after the loop, either metrical_analysis or scansion is empty. it
    # should be impossible for metrical_analysis to go empty with items
    # still in scansion, but do something sane here in case that condition
    # ever changes
    for s in scansion:
        result.append(('', '', s))

    # on the other hand, it's quite possible for metrical_analysis to
    # contain consonants and punctuation after the final scansion element.
    # copy them to the result without scansion.
    for cluster, prelim in metrical_analysis:
        result.append((cluster, prelim, ''))

    return result

# FIXME: this is hexameter specific. it probably belongs in hexameter.py
def _locate_caesura(metrical_analysis):
    '''Find the primary caesura in a line. We start in the third foot and
    look for the first word break that's not at foot boundary.

    :param metrical_analysis: list of tuples contiaining a character
        cluster, a preliminary metrical analysis, and a final scansion
    :rtype: the index of the caesura, or None if none could be found
    '''
    foot = 1 # start in the first foot
    foot_boundary = True
    for i in range(len(metrical_analysis)):
        cluster, prelim, scansion = metrical_analysis[i]
        if scansion == '|':
            foot += 1
            foot_boundary = True
            continue
        elif scansion:
            # once we see a scanned syllable, we're inside the next foot
            foot_boundary = False

        if ' ' in cluster:
            # this cluster is a word boundary
            if foot >=3 and not foot_boundary:
                return i

    # otherwise, we didn't find a caesura.
    return None

def _split_line(metrical_analysis, caesura_idx):
    '''Split the analyzed line into two strings, split at the identified
    caesura.
    
    :param metrical_analysis: list of tuples containing a character cluster,
        preliminary metrical analysis, and final scansion
    :param caesura_idx: index of the caesura
    :rtype: tuple of two strings
    '''
    pre_parts = metrical_analysis[:caesura_idx]
    caesura_part = metrical_analysis[caesura_idx]
    post_parts = metrical_analysis[caesura_idx+1:]
    pre_s = ''.join(p[0] for p in pre_parts)
    caesura_s = caesura_part[0]
    post_s = ''.join(p[0] for p in post_parts)

    # the caesura part should be a of type _OTHER and probably contains a
    # space, though it may contain other punctuation. we need to figure out
    # exactly where inside that part to split
    before, space, after = caesura_s.partition(' ')
    if space:
        pre_s = pre_s + before + space
        post_s = after + post_s
    else:
        # no space, so arbitrarily shove all the punctuation before the
        # caesura.
        pre_s = pre_s + caesura_s
    return (pre_s, post_s)


###
### tie it all together and scan a line
###

def _local_metrical_analysis(line):
    line = unicodedata.normalize('NFD', line)
    line = line.lower()
    glyphs = _glyphs(line)
    clusters = _cluster(glyphs)
    metrical_analysis = [_metrical_length(clusters, i)
                         for i in range(len(clusters))]
    return metrical_analysis

def _scan(metrical_analysis):
    analysis_s = ''.join(m[1] for m in metrical_analysis)
    normalizations = hexameter.normalize(analysis_s)
    if not normalizations:
        return []

    best_cost = normalizations[0][0]
    scansions = [n[1] for n in normalizations
                 if n[0] == best_cost]
    return scansions

def analyze_line(line):
    '''Analyze scansion and caesura placement for a single line of epic
    hexameter.

    :param line: string
    :rtype: list of tuples. Each tuple contains a possible scansion and a
        list of line parts, split at the caesura. If no caesura could be
        found, the list will contain only a single part.
    '''
    metrical_analysis = _local_metrical_analysis(line)
    scansions = _scan(metrical_analysis)
    result = []
    for scansion in scansions:
        merge = _merge_scansion(metrical_analysis, scansion)
        caesura = _locate_caesura(merge)
        if caesura is not None:
            line_parts = _split_line(merge, caesura)
        else:
            line_parts = [line]
        result.append((scansion, line_parts))
    return result

###
### file/stream processing
###

def process_tei_file(fname, stats):
    with open(fname) as inf:
        in_s = inf.read()
    tei = ElementTree.XML(in_s)
    text = tei.find('text')
    for line_node in text.iter('l'):
        line = ''.join(line_node.itertext())
        stats['total_lines'] += 1
        analyses = analyze_line(line)
        if not analyses:
            stats['no_match'] += 1
            continue
        if len(analyses) > 1:
            stats['multi_match'] += 1
        else:
            stats['scanned'] += 1
        update_line_node(line_node, analyses)


    out_s = ElementTree.tostring(tei, encoding='utf-8')
    out_fname = output_file_name(fname)
    with open(out_fname, 'w+b') as outf:
        outf.write(out_s)

def update_line_node(line_node, analyses):
    # add scansions
    scansions = [a[0] for a in analyses]
    scansion_s = ' OR '.join(scansions)
    line_node.set('real', scansion_s)

    # add caesura
    caesurae = set(tuple(a[1]) for a in analyses)
    if len(caesurae) != 1:
        # not representing differential caesurae, and nothing to do if none
        # found.
        return
    line_parts = list(caesurae)[0]
    if len(line_parts) != 2:
        # no caesura found for this analysis, or too many (which should be
        # impossible)
        return

    # two types of TEI lines in our sample text: those with a milesone node
    # inside at the front and those without. for the former, etree puts the
    # line text in milestone.tail. for the latter, it's in line_node.text.
    if line_node.text:
        line_node.text = line_parts[0]
    else:
        child_nodes = list(line_node)
        if len(child_nodes) != 1:
            # this doesn't look like we expect. bail.
            return
        milestone = child_nodes[0]
        if not milestone.tail:
            # this doesn't look like we expect. bail.
            return
        milestone.tail = line_parts[0]
    caesura_node = ElementTree.SubElement(line_node, 'caesura')
    caesura_node.tail = line_parts[1]


def output_file_name(fname):
    import os.path
    base, ext = os.path.splitext(fname)
    if ext.lower() in ('.tei', '.xml'):
        return base + '.scanned' + ext
    else:
        return fname + '.scanned'

def process_line_stream(inf, stats):
    for line in inf:
        stats['total_lines'] += 1
        line = line.strip() # strip whitespace
        analyses = analyze_line(line)
        if not analyses:
            stats['no_match'] += 1
            print('ERROR: Failed to scan: ' + line)
        elif len(analyses) > 1:
            stats['multi_match'] += 1
            scansions = [a[0] for a in analyses]
            print(' OR '.join(scansions))
        else:
            stats['scanned'] += 1
            print(analyses[0][0])

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
