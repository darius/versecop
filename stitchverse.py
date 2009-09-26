import optparse
import re
import sys

import metercop

parser = optparse.OptionParser()
parser.add_option('-b', '--beats', dest='beats', default='5',
                  help="Number of beats/line (default 5)")
parser.add_option('-s', '--slacker', dest='slacker',
                  action='store_true',
                  help="Allow a slack syllable to end lines")
parser.add_option('-v', '--verse', dest='verse', default='blankverse',
                  help="Verse form: haiku or (default) blankverse")
options = None
meter1, meter2 = None, None

def main():
    global options, meter1, meter2
    options, args = parser.parse_args()
    if args:
        parser.print_help()
        sys.exit(1)
    if options.verse == 'blankverse':
        meter1 = metercop.iamb * int(options.beats)
        meter2 = meter1 + (metercop.slack,)
        filtering(filter_blank_verse)
    elif options.verse == 'haiku':
        filtering(filter_haiku)
    else:
        parser.print_help()
        sys.exit(1)

def filtering(verse_form):
    write_lines(sys.stdout, filter_for(verse_form,
                                       read_lines(sys.stdin)))

def write_lines(outfile, lines):
    for line in lines:
        outfile.write(line)
        outfile.flush()

def read_lines(infile):
    while True:
        input = infile.readline()
        if not input: break
        yield input

def filter_for(verse_form, inputs):
    seen = set()
    for input in inputs:
        if input in seen: continue
        try:
            meta, line = input.split(' ', 1)
        except ValueError:
            # A too-short line -- skip it.
            continue
        output = verse_form(get_tokens(line))
        if output:
            yield meta + ' ' + output
            seen.add(input)

def filter_haiku(tokens):
    counts = [5, 7, 5]
    acc = ''
    nsyllables = 0
    for token in tokens:
        if not is_word(token):
            acc += token
        else:
            word = clean_word(token)
            n = metercop.count_syllables(word)
            if n is None or not counts:
                return None
            if n and counts[0] == nsyllables:
                acc += '<br/>'
                nsyllables -= counts.pop(0)
                if not counts:
                    return None
            nsyllables += n
            if counts[0] < nsyllables:
                return None
            acc += token
    return acc if counts == [nsyllables] else None

def filter_blank_verse(tokens):
    return (versify(meter1, tokens)
            or (options.slacker and versify(meter2, tokens)))

def versify(line_meter, tokens):
    acc = ''
    meter = line_meter
    for token in tokens:
        if not is_word(token):
            acc += token
        else:
            if meter == ():
                meter = line_meter
                acc += '<br/>'
            word = clean_word(token)
            meter, rhyme = metercop.match_word(word, meter)
            if meter is None:
                break
            acc += token
    return acc if meter == () else None

def get_tokens(text):
    text = re.sub(r'^<text>|</text>$', '', text)
    return re.split(token_pat, text)

smiley_pats = [r'[:;=][DExLOPp](?!\w)',
               r"(?<!\w)[Dx][:;=]",
               r"[:;]o\)",
               r"(?<!\w)8\)|\(8(?!\w)",
               # TODO: o.o o.O T.T X_X
               #r"(?<!\w)[oOTX][_.][oOTX](?!\w)",
               ]
smiley_pat = '|'.join(smiley_pats)

rquote_pat = r"&#8217;"
#word_pat = r"(?:[\w']|%s)+" % (rquote_pat,)
word_pat = r"(?:[A-Za-z0-9']|%s)+" % (rquote_pat,)

token_pat = '(%s|%s|&amp;)' % (word_pat, smiley_pat)

def is_word(token):
    return re.match(word_pat, token)

def clean_word(token):
    token = re.sub(r"&#8217;", "'", token)
    return token.strip("'")


if __name__ == '__main__':
    main()
