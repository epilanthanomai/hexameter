#!/usr/bin/env python

'''Find words from hexameter sources in solr.'''
# NB: assumes solr was populated by index_tei.py or equivalent

import unicodedata
import sunburnt

def report_results(base_query):
    ROWS = 10
    start = 0

    query = base_query.sort_by('work_name').sort_by('book_num') \
                      .sort_by('line_num')
    response = query.paginate(start=start, rows=ROWS).execute()
    print('%d hits:' % (response.result.numFound,))
    
    while list(response):
        for match in response:
            scans = match.get('scansion', None)
            if not scans:
                scans = ['']

            if 'before_caesura' in match and 'after_caesura' in match:
                line = '%s // %s' % (match['before_caesura'].strip(),
                                     match['after_caesura'].strip())
            else:
                line = match['line_text']

            print('%-9s %-22s %s' % (match['lineid'], scans[0], line)) 
            for scan in scans[1:]:
                print('%-9s %-22s %s' % ('', scan, '  alternate scansion'))
        start += ROWS
        response = query.paginate(start=start, rows=ROWS).execute()


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print('Usage: %s solr_url word ...')
    solr_url = sys.argv[1]
    solr = sunburnt.SolrInterface(solr_url)
    query = solr # not really, but it will after the first iteration of:
    for word in sys.argv[2:]:
        query = query.query(unicode(word, 'utf-8'))
    report_results(query)
