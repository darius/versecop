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
        words = get_words(line)
        if (meter_matches(meter, words)
            or (options.slacker and meter_matches(meter2, words))):
            yield input
            seen.add(input)

def meter_matches(meter, words):
    return () == match_words(words, meter)

def match_words(words, line_meter):
    meter = line_meter
    for word in words:
        if meter is None: break
        if False:
            # This lets us treat tweets as multiple lines in the given meter.
            # Disabled for now.
            if meter == (): meter = line_meter
        meter, rhyme = metercop.match_word(word, meter)
    return meter

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
               # TODO: o.o T.T
               ]
smiley_pat = '|'.join(smiley_pats)


if __name__ == '__main__':
    main()
