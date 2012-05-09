hexameter
=========

Scripts for working with Greek epic hexameter, particularly the Iliad and
Odyssey, originally written as part of a project for a Homeric Greek class.

These utilities do several interesting things:
 * Convert `Beta Code <http://en.wikipedia.org/wiki/Beta_code>`_ to unicode.
   In particular, do this with the slightly nonstandard Beta Code produced
   by `Perseus <http://www.perseus.tufts.edu/>`_, inside of Perseus'
   `TEI <http://www.tei-c.org/>`_ files.
 * Perform metrical analysis on epic hexameter. These modules provide
   general functions for performing scansion and caesura identification, and
   in particular it can bulk-analyze Perseus-style TEI files, adding the
   scansion and caesura information to the file.
 * Load hexameter TEI files with scansion into an `apache solr
   <http://lucene.apache.org/solr/>`_ instance, and look for words in
   metrical context. For example::

     $ ./find_words.py http://server:8080/solr/hexameter/ 'ἕκτορος ἱπποδάμοιο'
     4 hits:
     Il.16.717 +--|++|++|+--|+--|++   ἀσίῳ, ὃς μήτρως // ἦν ἕκτορος ἱπποδάμοιο
     Il.22.161 +--|++|+--|+--|+--|++  ἀλλὰ περὶ ψυχῆς // θέον ἕκτορος ἱπποδάμοιο.
     Il.22.211 +--|++|++|+--|+--|++   τὴν μὲν ἀχιλλῆος, // τὴν δ' ἕκτορος ἱπποδάμοιο,
     Il.24.804 ++|+--|+--|+--|+--|++  ὣς οἵ γ' ἀμφίεπον // τάφον ἕκτορος ἱπποδάμοιο.

Full TEI-encoded Beta Code versions of The Iliad and The Oddyssey are
available from Perseus:

 * `The Iliad <http://www.perseus.tufts.edu/hopper/dltext?doc=Perseus%3Atext%3A1999.01.0133>`_
 * `The Odyssey <http://www.perseus.tufts.edu/hopper/dltext?doc=Perseus%3Atext%3A1999.01.0135>`_

Beta Code conversion
--------------------

The ``betacode.py`` module exports a ``betacode_to_unicode()`` function.
Pass it Greek betacode, and it returns unicode in `Normalization Form D
<http://en.wikipedia.org/wiki/Unicode_equivalence#Normalization>`_ (NFD). In
addition to hairier parts of betacode translation like selecting correctly
between final and medial sigma, this function handles some oddities specific
to the betacode stored by Perseus. For instance, Perseus encodes “Ἀχιλλεύς”
(Akilleus) as ``*)axilleu/s``, where a canonical representation would be
``*A)XILLEU/S``. Note, aside from the trivial capitalization difference, the
Perseus version places the breathing mark ``)`` *before* the ``A`` that it
modifies. This conversion function detects this encoding error and correctly
puts the Unicode breathing mark after the capital alpha.

The ``betacode_to_unicode_tei.py`` script takes filenames of TEI-encoded
betacode texts and converts the text only (not the English metadata in the
file header) to Unicode NFD.

Metrical analysis
-----------------

The ``scan.py`` module exports an ``analyze_line()`` function that scans
lines of epic hexameter, returning the most likely scansion. It handles
synizesis and correption, even together. This tends to make quite a few
possible scansions for many lines, and often they can get a bit silly. To
account for this, it's smart enough to reject scansions involving heavy
synizesis and correption when simpler scans are possible.

The metrical analyzer currently scans about 99% of the lines in The Iliad
and The Odyssey, and just short of 2% have multiple feasible scansion
alternatives. The analyzer also identifies the line's primary caesura.

``scan.py`` may also be called as a command-line script. Called with no
arguments, it will read lines from the terminal and output their scansion.
It may further be called with the filename of a Unicode TEI file (such as
one output by ``betacode_to_unicode_tei.py``). In this case, it adds
scansion information to that file, following the conventions for realized
metrical structure set forth in `Chapter 6 of the TEI documentation
<http://www.tei-c.org/release/doc/tei-p5-doc/en/html/VE.html#VEME>`_ and
caesurae `in the same chapter
<http://www.tei-c.org/release/doc/tei-p5-doc/en/html/VE.html#VESE>`_.

Indexing and searching
----------------------

The ``solr`` directory defines a simple configuration for an `apache solr
<http://lucene.apache.org/solr/>`_ server to allow quick searching of lines
and their metrical analysis.

The ``index_tei.py`` script reads hexameter from analyzed TEI files like
those produced by ``scan.py``, and it inserts them into a solr instance
configured with the provided configuration.

Once the files have been indexed, they may examine the indexes directly to
see, for instance, that the most common line meter between the Iliad and the
Odyssey (5957 lines, 22%) is entirely dactylic in the first five feet.
The second most common (4501 lones, 16%) has only a single spondee on the
second foot. Scolars can easily compare word frequencies or limit by work
and book, and of course technical scholars can modify the software to try
alternate algorithms for scansion or to bring in additional data.

The ``find_words.py`` script provides easy searching of words in their
metrical context, which isn't quite as easy to see directly in the technical
index interface. It can be used from a command line to quickly find details
about the uses of particular words and phrases in the corpus, serving as a
springboard for broad algorithmic examinations of Parry's formulaic model of
oral tradition::

  $ ./find_words.py http://troll:8080/solr/hexameter/ 'ἄναξ ἀνδρῶν'
  52 hits:
  Il.1.7    +--|+--|++|++|+--|++   ἀτρεί̈δης τε ἄναξ // ἀνδρῶν καὶ δῖος ἀχιλλεύς.
  [...many results elided...]
  Il.19.199 +--|++|+--|++|+--|++   ἀτρεί̈δη κύδιστε // ἄναξ ἀνδρῶν ἀγάμεμνον
  Il.23.49  ++|++|+--|++|+--|++    ἠῶθεν δ' ὄτρυνον // ἄναξ ἀνδρῶν ἀγάμεμνον
            ++|+--|++|++|+--|++      alternate scansion
  Il.23.161 +--|+--|+--|++|+--|++  αὐτὰρ ἐπεὶ τό γ' ἄκουσεν // ἄναξ ἀνδρῶν ἀγαμέμνων,
  Il.23.288 +--|++|+--|++|++|++    ὦρτο πολὺ πρῶτος // μὲν ἄναξ ἀνδρῶν εὔμηλος
  Il.23.895 +--|+--|+--|++|+--|++  ὣς ἔφατ', οὐδ' ἀπίθησεν // ἄναξ ἀνδρῶν ἀγαμέμνων·
  Od.11.397 +--|++|+--|++|+--|++   ἀτρεί̈δη κύδιστε, // ἄναξ ἀνδρῶν ἀγάμεμνον,
  Od.24.121 +--|++|+--|++|+--|++   ἀτρεί̈δη κύδιστε, // ἄναξ ἀνδρῶν ἀγάμεμνον,

Further work
------------

The tools in this project provide a toolkit for beginning to examine Greek
epic hexameter in metrical context. As suggested above, the tools have
direct application in broadening examinations of Parry's classic work.

Additionally, the tools still have some rough spots. This is understandable:
They were originally produced as a single-student project in a one-semester
undergraduate course. More work can improve them, though, and the open
source world opens that opportunity to anyone who finds the code. The
betacode tools could benefit from being generalized into reusable components
for any project that needs to work with scholarly communication in betacode.
The metrical analysis tools have some rules to handle lengthening of vowels
by position, but they do not completely handle all exceptions to this. The
tools remain unable to scan a few hundred lines: They could be improved to
allow complete coverage of the poems, or to improve the algorithms for
picking between divergent scans. They haven't yet been used for scansion of
other Greek hexameter; further work could determine their suitability for
this and improve it if necessary.

And of course, the technical form of these tools is not accessible to many
scholars of Homer. Expanding the tools' interfaces to improve their
accessibility could open the doors for metrical and formula research to many
scholars who don't have the high technical skills demanded by these tools.

Appendix: Technical details of metrical analysis
------------------------------------------------

Metrical analysis of a line happens in four stages:

 1. Split the line into consonant clusters, vowels, diphthongs, and
    other characters such as space and punctuation. This stage is
    responsible for determining from accentuation and other guides what
    vowel clusters should be scanned as diphthongs and which as single
    consonants.
 2. Categorizing vowels according to their potential metrical role by
    looking at the surrounding characters in the line. This step does not
    yet take into account the full context of the line: It identifies, for
    instance, that a particular epsilon is short and may be a candidate for
    synizesis if necessary. It identifies that a particular alpha is long by
    position. It identifies that a particular diphthong meets the conditions
    for correption if it should be appropriate for the scansion of the line.
 3. Matching these local metrical categorizations against the complex
    line patterns available to the poet in epic hexameter. This processing
    is performed by a `nondeterministic finite automaton
    <http://en.wikipedia.org/wiki/Nondeterministic_finite_automaton>`_ 
    implemented and more thoroughly explained in ``hexameter.py``. This
    phase identifies all possible scansions of the the line and prioritizes
    them according to complexity.
 4. Locating the line's primary caesura. Conventionally this is the first
    caesura in the third foot, or in the fourth if the third has none. If a
    line has multiple equally-likely scansions then a separate caesura is
    calculated for each.

After these four stages, the line has been analyzed. The analysis is
returned to the calling program, entered into the TEI file, or output to the
console, according to how the analysis was called.
