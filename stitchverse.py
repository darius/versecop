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
options = None

def main():
    global options
    options, args = parser.parse_args()
    if args:
        parser.print_help()
        sys.exit(1)
    filtering()

def filtering():
    write_lines(sys.stdout, 
                filter_for_verse(read_lines(sys.stdin)))

def write_lines(outfile, lines):
    for line in lines:
        outfile.write(line)
        outfile.flush()

def read_lines(infile):
    while True:
        input = infile.readline()
        if not input: break
        yield input

def filter_for_verse(inputs):
    meter = metercop.iamb * int(options.beats)
    meter2 = meter + (metercop.slack,)
    seen = set()
    for input in inputs:
        if input in seen: continue
        try:
            meta, line = input.split(' ', 1)
        except ValueError:
            # A too-short line -- skip it.
            continue
        tokens = get_tokens(line)
        output = (versify(meter, tokens)
                  or (options.slacker and versify(meter2, tokens)))
        if output:
            yield meta + ' ' + output
            seen.add(input)

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

def get_words(line):
    line = re.sub(r'^<text>|</text>$', '', line)
    line = re.sub(r"&#8217;", "'", line)
    line = re.sub(r"&amp;", "&", line)
    line = re.sub(smiley_pat, ' ', line)
    # Remove non-words:
    line = re.sub(r"[^A-Za-z0-9']", ' ', line)
    return [word.strip("'") for word in line.split()]

smiley_pats = [r'[:;=][DExLPp](?!\w)',
               r"(?<!\w)[Dx][:;=]",
               r"[:;]o\)",
               r"(?<!\w)8\)|\(8(?!\w)",
               # TODO: o.o T.T X_X
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
