from collections import defaultdict

LONG = '+'
SHORT = '-'
INDETERMINATE = '?' # could be long or short
LONG_CORREPTION = 'C' # long and positionally candidate for correption
INDETERMINATE_CORREPTION = 'c' # indeterminate length but positionally
                               # candidate for correption if long
SHORT_SYNIZESIS = ',' # short and positionally candidate for synizesis

# these three are not used in input, but are used in output analysis:
SKIPPED = '.'
FOOT = '|'

# A basic hexameter foot has a simplified state diagram something like this:
#
#                ,----- -L- -----,
#   (0) -L- (1) <                 >- (7)
#                '- -s- (2) -s- -'
#
# This diagram ignores important features like indeterminate-length
# syllables, correption, and synizesis; those will be added shortly. We
# start at state (0) and accept only a long (-L-) syllable, which
# transitions us to (1). We may then accept either another long or two
# shorts. Either transitions us to (7), either directly (via a -L-) or by
# way of (2) (through two -s- transitions). We can chain this five times for
# the first five feet of the meter, with each foot starting on the end state
# of the last, and then the last foot is a simplified version that accepts a
# long followed by any syllable (represented here as -X-):
#
#   (35) -L- (36) -X- (37)
#
# To account for syllables in the poem that could be either long or short,
# we extend the -L-, -s-, and -X- transitions to accept indeterminate length
# syllables. Correption is handled similarly: Either of the correption
# candidate syllables defined above could serve as either a -L-, -s-, or -X-
# transition.
#
# Synizesis essentially allows us to fuse certain short syllables together
# with a following syllable to produce a long. That means that any -L- or
# -X- transition in our simplified diagram above could also be satisfied by
# a SHORT_SYNIZESIS syllable followed by any other single syllable. And in
# fact this fused syllable may be affected by correption (as in Il. 1.15),
# so any -s- transition could be satisfied by a SHORT_SYNIZESIS followed by
# a correption candidate. This adds some complexity to the simplified
# diagram above. Using -z- for a synizesis transition and -C- for any
# transition representing a correptible syllable, the first foot looks like
# this:
#
#                                 ,-------------- -L- --------------,
#                                /                                   \
#        ,---- -L- ----,        /------------ -z- (4) -X- ------------\
#   (0) <               > (1) -<                                       > (7)
#        ' -z- (3) -X- '        \  ,--- -s- ---,       ,--- -s- ---,  /
#                                '<             > (2) <             >'
#                                  '-z- (5) -C-'       '-z- (6) -C-'
#
# And the sixth foot examds to:
#
#        ,----- -L- ----,        ,----- -L- ----,
#  (35) <                > (36) <                > (37)
#        ' -z- (38) -X- '        ' -z- (39) -X- '
#
# This gets us far, but an unweighted algorithm can't distinguish between a
# scan free of any synizesis or correption and a line that contains many of
# those exceptions. We want to favor scans with as few of these features as
# possible, and so we add a cost to transitions involving synizesis and
# correption. Specifically, additional cost/weight is given to the transitions
# where LONG_CORREPTION transitions in the -s- group (that is, where correption
# occurs), and where SHORT_SYNIZESIS transitions participate in the replacement
# of a long syllable. Note that this cost is not applied when a LONG_CORREPTION
# transitions along a -L- path: This is the normal case of a long syllable
# functioning as a long syllable. The cost is also not applied for an
# INDETERMINATE_CORREPTION syllable in any case: This is a syllable that could
# be either short or long naturally, and so no correption is necessary to
# explain its use as short. Since SHORT_SYNIZESIS is just a short syllable
# normally, its transition along a -s- path similarly has no additional cost.
# Our machine collects all possible matches and reports each with its cost so
# that calling software can report any and all appropriate scansions.
#
# Note that frequently (~1300 lines, e.g., Il. 1.33) won't scan unless we
# scan short syllables as long. Some of these can be explained with a
# dropped digamma, but not all of them. In order to provide some sensible
# scansion, we allow SHORT_SYLLABLES to fill in for LONG_SYLLABLES. We give
# this an arbitrarily high cost so that the path is only taken as a last
# resort.

LONG_SYLLABLES = [ LONG, INDETERMINATE, LONG_CORREPTION, INDETERMINATE_CORREPTION ]
SHORT_SYLLABLES = [ SHORT, INDETERMINATE, INDETERMINATE_CORREPTION, SHORT_SYNIZESIS ]
CORREPTED_SYLLABLES = [ LONG_CORREPTION ]
CORREPTED_SYNIZESIS = [ LONG_CORREPTION, INDETERMINATE_CORREPTION ]
SYNIZESIS_SYLLABLES = [ SHORT_SYNIZESIS ]
ALL_SYLLABLES = [ LONG, SHORT, INDETERMINATE, LONG_CORREPTION, INDETERMINATE_CORREPTION, SHORT_SYNIZESIS ]

class ScansionNFA:
    TRANSITION_TABLE = [
        #(from_state, accept_syllables,    to_state, cost, scan_as)

        ###
        ### first foot
        ###

        # long first syllable
        ( 0,          LONG_SYLLABLES,      1,        0,    LONG),
        ( 0,          SHORT_SYLLABLES,     1,        15,   LONG),
        # synizesis producing long first syllable
        ( 0,          SYNIZESIS_SYLLABLES, 3,        1,    SKIPPED),
        ( 3,          ALL_SYLLABLES,       1,        0,    LONG),
        # long second syllable of spondee
        ( 1,          LONG_SYLLABLES,      7,        0,    LONG + FOOT),
        ( 1,          SHORT_SYLLABLES,     7,        15,   LONG + FOOT),
        # synizesis producing long second syllable of spondee
        ( 1,          SYNIZESIS_SYLLABLES, 4,        1,    SKIPPED),
        ( 4,          ALL_SYLLABLES,       7,        0,    LONG + FOOT),
        # short second syllable of dactyl
        ( 1,          SHORT_SYLLABLES,     2,        0,    SHORT),
        ( 1,          CORREPTED_SYLLABLES, 2,        1,    SHORT),
        # synizesis and correption producing short second syllable of dactyl
        ( 1,          SYNIZESIS_SYLLABLES, 5,        1,    SKIPPED),
        ( 5,          CORREPTED_SYNIZESIS, 2,        1,    SHORT),
        # short third syllable of dactyl
        ( 2,          SHORT_SYLLABLES,     7,        0,    SHORT + FOOT),
        ( 2,          CORREPTED_SYLLABLES, 7,        1,    SHORT + FOOT),
        # synizesis and correption producins short third syllable of dactyl
        ( 2,          SYNIZESIS_SYLLABLES, 6,        1,    SKIPPED),
        ( 6,          CORREPTED_SYNIZESIS, 7,        1,    SHORT + FOOT),

        ###
        ### second foot
        ###

        # long first syllable
        ( 7,          LONG_SYLLABLES,      8,        0,    LONG),
        ( 7,          SHORT_SYLLABLES,     8,        15,   LONG),
        # synizesis producing long first syllable
        ( 7,          SYNIZESIS_SYLLABLES, 10,       1,    SKIPPED),
        ( 10,         ALL_SYLLABLES,       8,        0,    LONG),
        # long second syllable of spondee
        ( 8,          LONG_SYLLABLES,      14,       0,    LONG + FOOT),
        ( 8,          SHORT_SYLLABLES,     14,       15,   LONG + FOOT),
        # synizesis producing long second syllable of spondee
        ( 8,          SYNIZESIS_SYLLABLES, 11,       1,    SKIPPED),
        ( 11,         ALL_SYLLABLES,       14,       0,    LONG + FOOT),
        # short second syllable of dactyl
        ( 8,          SHORT_SYLLABLES,     9,        0,    SHORT),
        ( 8,          CORREPTED_SYLLABLES, 9,        1,    SHORT),
        # synizesis and correption producing short second syllable of dactyl
        ( 8,          SYNIZESIS_SYLLABLES, 12,       1,    SKIPPED),
        ( 12,         CORREPTED_SYNIZESIS, 9,        1,    SHORT),
        # short third syllable of dactyl
        ( 9,          SHORT_SYLLABLES,     14,       0,    SHORT + FOOT),
        ( 9,          CORREPTED_SYLLABLES, 14,       1,    SHORT + FOOT),
        # synizesis and correption producins short third syllable of dactyl
        ( 9,          SYNIZESIS_SYLLABLES, 13,       1,    SKIPPED),
        ( 13,         CORREPTED_SYNIZESIS, 14,       1,    SHORT + FOOT),

        ###
        ### third foot
        ###

        # long first syllable
        ( 14,         LONG_SYLLABLES,      15,       0,    LONG),
        ( 14,         SHORT_SYLLABLES,     15,       15,   LONG),
        # synizesis producing long first syllable
        ( 14,         SYNIZESIS_SYLLABLES, 17,       1,    SKIPPED),
        ( 17,         ALL_SYLLABLES,       15,       0,    LONG),
        # long second syllable of spondee
        ( 15,         LONG_SYLLABLES,      21,       0,    LONG + FOOT),
        ( 15,         SHORT_SYLLABLES,     21,       15,   LONG + FOOT),
        # synizesis producing long second syllable of spondee
        ( 15,         SYNIZESIS_SYLLABLES, 18,       1,    SKIPPED),
        ( 18,         ALL_SYLLABLES,       21,       0,    LONG + FOOT),
        # short second syllable of dactyl
        ( 15,         SHORT_SYLLABLES,     16,       0,    SHORT),
        ( 15,         CORREPTED_SYLLABLES, 16,       1,    SHORT),
        # synizesis and correption producing short second syllable of dactyl
        ( 15,         SYNIZESIS_SYLLABLES, 19,       1,    SKIPPED),
        ( 19,         CORREPTED_SYNIZESIS, 16,       1,    SHORT),
        # short third syllable of dactyl
        ( 16,         SHORT_SYLLABLES,     21,       0,    SHORT + FOOT),
        ( 16,         CORREPTED_SYLLABLES, 21,       1,    SHORT + FOOT),
        # synizesis and correption producins short third syllable of dactyl
        ( 16,         SYNIZESIS_SYLLABLES, 20,       1,    SKIPPED),
        ( 20,         CORREPTED_SYNIZESIS, 21,       1,    SHORT + FOOT),

        ###
        ### fourth foot
        ###

        # long first syllable
        ( 21,         LONG_SYLLABLES,      22,       0,    LONG),
        ( 21,         SHORT_SYLLABLES,     22,       15,   LONG),
        # synizesis producing long first syllable
        ( 21,         SYNIZESIS_SYLLABLES, 24,       1,    SKIPPED),
        ( 24,         ALL_SYLLABLES,       22,       0,    LONG),
        # long second syllable of spondee
        ( 22,         LONG_SYLLABLES,      28,       0,    LONG + FOOT),
        ( 22,         SHORT_SYLLABLES,     28,       15,   LONG + FOOT),
        # synizesis producing long second syllable of spondee
        ( 22,         SYNIZESIS_SYLLABLES, 25,       1,    SKIPPED),
        ( 25,         ALL_SYLLABLES,       28,       0,    LONG + FOOT),
        # short second syllable of dactyl
        ( 22,         SHORT_SYLLABLES,     23,       0,    SHORT),
        ( 22,         CORREPTED_SYLLABLES, 23,       1,    SHORT),
        # synizesis and correption producing short second syllable of dactyl
        ( 22,         SYNIZESIS_SYLLABLES, 26,       1,    SKIPPED),
        ( 26,         CORREPTED_SYNIZESIS, 23,       1,    SHORT),
        # short third syllable of dactyl
        ( 23,         SHORT_SYLLABLES,     28,       0,    SHORT + FOOT),
        ( 23,         CORREPTED_SYLLABLES, 28,       1,    SHORT + FOOT),
        # synizesis and correption producins short third syllable of dactyl
        ( 23,         SYNIZESIS_SYLLABLES, 27,       1,    SKIPPED),
        ( 27,         CORREPTED_SYNIZESIS, 28,       1,    SHORT + FOOT),

        ###
        ### fifth foot
        ###

        # NOTE: We tend to prefer a dactylic fifth foot, so raise the cost
        # of spondees for this foot only.

        # long first syllable
        ( 28,         LONG_SYLLABLES,      29,       0,    LONG),
        ( 28,         SHORT_SYLLABLES,     29,       15,   LONG),
        # synizesis producing long first syllable
        ( 28,         SYNIZESIS_SYLLABLES, 31,       1,    SKIPPED),
        ( 31,         ALL_SYLLABLES,       29,       0,    LONG),
        # long second syllable of spondee
        ( 29,         LONG_SYLLABLES,      35,       1,    LONG + FOOT), # raised spondee cost
        ( 29,         SHORT_SYLLABLES,     35,       16,   LONG + FOOT),
        # synizesis producing long second syllable of spondee
        ( 29,         SYNIZESIS_SYLLABLES, 32,       1,    SKIPPED),
        ( 32,         ALL_SYLLABLES,       35,       1,    LONG + FOOT), # raised spondee cost
        # short second syllable of dactyl
        ( 29,         SHORT_SYLLABLES,     30,       0,    SHORT),
        ( 29,         CORREPTED_SYLLABLES, 30,       1,    SHORT),
        # synizesis and correption producing short second syllable of dactyl
        ( 29,         SYNIZESIS_SYLLABLES, 33,       1,    SKIPPED),
        ( 33,         CORREPTED_SYNIZESIS, 30,       1,    SHORT),
        # short third syllable of dactyl
        ( 30,         SHORT_SYLLABLES,     35,       0,    SHORT + FOOT),
        ( 30,         CORREPTED_SYLLABLES, 35,       1,    SHORT + FOOT),
        # synizesis and correption producins short third syllable of dactyl
        ( 30,         SYNIZESIS_SYLLABLES, 34,       1,    SKIPPED),
        ( 34,         CORREPTED_SYNIZESIS, 35,       1,    SHORT + FOOT),

        ###
        ### sixth foot
        ###

        # long first syllable
        ( 35,         LONG_SYLLABLES,      36,       0,    LONG),
        ( 35,         SHORT_SYLLABLES,     36,       15,   LONG),
        # synizesis producing long first syllable
        ( 35,         SYNIZESIS_SYLLABLES, 38,       1,    SKIPPED),
        ( 38,         ALL_SYLLABLES,       36,       0,    LONG),
        # any second syllable
        ( 36,         ALL_SYLLABLES,       37,       0,    LONG),
        # synizesis producing long second syllable
        ( 36,         SYNIZESIS_SYLLABLES, 39,       1,    SKIPPED),
        ( 39,         ALL_SYLLABLES,       37,       0,    LONG),
    ]
    START_STATE = 0
    ACCEPT_STATE = 37 # only at end of input

    transitions = defaultdict(list)
    for from_state, syllables, to_state, cost, scan_as in TRANSITION_TABLE:
        for syllable in syllables:
            transitions[(from_state, syllable)].append((to_state, cost, scan_as))

    def __init__(self):
        self.states = [ (self.START_STATE, 0, '') ] # state, cost, scansion

    def input(self, syllables):
        for syllable in syllables:
            self.transition(syllable)

    def transition(self, syllable):
        new_states = []
        for old_state, old_cost, old_scansion in self.states:
            transitions = self.transitions[(old_state, syllable)]
            for new_state, path_cost, path_scansion in transitions:
                new_cost = old_cost + path_cost
                new_scansion = old_scansion + (path_scansion or '')
                new_states.append((new_state, new_cost, new_scansion))

        self.states = new_states

    def results(self):
        return sorted([(s[1], s[2]) for s in self.states
                      if s[0] == self.ACCEPT_STATE])


def normalize(scansion):
    nfa = ScansionNFA()
    nfa.input(scansion)
    return nfa.results()
