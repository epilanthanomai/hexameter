import unicodedata

class Converter:
    def __init__(self):
        self.result_chunks = []
        self.capitalize_next = False
        self.last_is_letter = False
        self.hold = []

    def input(self, betacode):
        i = 0
        while i < len(betacode):
            c = betacode[i]
            if c == '*':
                self.capitalize_next = True
                i += 1
                continue
            if c.upper() == 'S':
                if i == len(betacode) - 1:
                    self.append_out('\u03c2') # final sigma
                    i += 1
                    continue
                c2 = betacode[i + 1]
                if c2 in map_b2u_sigma:
                    self.append_out(map_b2u_sigmal[c2])
                    i += 2
                    continue
                if c2 == "'":
                    self.append_out('\u03c3') # medial sigma
                    i += 1
                    continue

                if self.is_letter(c2):
                    self.append_out('\u03c3') # medial sigma
                    i += 1
                    continue
                else:
                    self.append_out('\u03c2') # final sigma
                    i += 1
                    continue

            self.append_out(map_b2u.get(c.upper(), c))
            i += 1

    def append_out(self, c):
        if self.is_letter(c):
            self.last_is_letter = True
            if self.capitalize_next:
                c = c.upper()
                self.capitalize_next = False
            self.result_chunks.append(c)
            # if any held accents, they go on this letter
            self.result_chunks.extend(self.hold)
            self.hold = []
        elif self.is_nonspacing_mark(c):
            if self.last_is_letter:
                self.result_chunks.append(c)
            else:
                # accents after a non-letter. hold them for the next letter
                self.hold.append(c)
        else:
            self.last_is_letter = False
            self.result_chunks.append(c)

    def is_letter(self, c):
        return unicodedata.category(c)[0] == 'L'

    def is_nonspacing_mark(self, c):
        return unicodedata.category(c) == 'Mn'

    def __str__(self):
        return ''.join(self.result_chunks)

def betacode_to_unicode(betacode):
    c = Converter()
    c.input(betacode)
    return str(c)

map_b2u = {
    'A':  '\u03b1', # alpha
    'B':  '\u03b2', # beta
    'C':  '\u03be', # xi
    'D':  '\u03b4', # delta
    'E':  '\u03b5', # epsilon
    'F':  '\u03c6', # phi
    'G':  '\u03b3', # gamma
    'H':  '\u03b7', # eta
    'I':  '\u03b9', # iota
    'K':  '\u03ba', # kappa
    'L':  '\u03bb', # lambda
    'M':  '\u03bc', # mu
    'N':  '\u03bd', # nu
    'O':  '\u03bf', # omicron
    'P':  '\u03c0', # pi
    'Q':  '\u03b8', # theta
    'R':  '\u03c1', # rho
    'S':  '\u03c3', # medial sigma (see special case in translator)
    'T':  '\u03c4', # tau
    'U':  '\u03c5', # upsilon
    'V':  '\u03dd', # digamma
    'W':  '\u03c9', # omega
    'X':  '\u03c7', # chi
    'Y':  '\u03c8', # psi
    'Z':  '\u03b6', # zeta
    ')':  '\u0313', # smooth breathing
    '(':  '\u0314', # rough breathing
    '/':  '\u0301', # acute
    '=':  '\u0342', # circumflex
    '\\': '\u0300', # grave
    '+':  '\u0308', # diaeresis
    '|':  '\u0345', # iota subscript
    '?':  '\u0323', # dot below
    ':':  '\u00b7', # middle dot
    '-':  '\u2010', # hyphen
    '_':  '\u2014', # em dash
}

map_b2u_sigma = {
    '1': '\u03c3', # medial sigma
    '2': '\u03c2', # final sigma
    '3': '\u03f2', # lunate sigma
}
