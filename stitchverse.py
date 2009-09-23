import optparse
import random
import socket
import string
import sys

import pronounce

parser = optparse.OptionParser()
parser.add_option("-p", "--port", dest="port",
                  help="listen on PORT")

def main():
    options, args = parser.parse_args()
    if args:
        parser.print_help()
        sys.exit(1)
    if options.port is not None:
        host, port = '', int(options.port)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        while True:
            s.listen(1)
            conn, addr = s.accept()
            print >>sys.stderr, 'accepted from', addr
            filtering(*files_from_socket(conn))
    else:
        filtering(sys.stdin, sys.stdout)

def filtering(infile, outfile):
    for line in filter_for_verse(infile):
        outfile.write(line)

def files_from_socket(conn):
    # Geez. Return a pair of things acting enough like files for our use.
    def infile():
        buffer = ''  # The last partial line read so far.
        while True:
            data = conn.recv(4096)
            if not data: break
            lines = (buffer + data).split('\n')
            for line in lines[:-1]:
                yield line + '\n'
            buffer = lines[-1]
        if buffer:
            yield buffer
    class Outfile:
        def write(self, line):
            conn.send(line)
    return infile(), Outfile()

def filter_for_verse(lines):
    meter = iambic_pentameter
    seen = set()
    for line in lines:
        #print >>sys.stderr, 'LINE:', line,
        if line in seen: continue
        if meter_matches(meter, get_words(line)):
            yield line
            seen.add(line)

def get_words(line):
    import re
    line = re.sub(r"&#8217;", "'", line)
    line = re.sub(r"&amp;", "&", line)
    # Strip smileys:
    line = re.sub(r":D(\W|$)", r"\1", line)
    line = re.sub(r"(^|\W)D:", r"\1", line)
    line = re.sub(r"[^A-Za-z0-9']", ' ', line)
    return [word.strip("'") for word in line.split()]

slack, stressed, rhymed = range(3)
iamb = (slack, stressed)
iambic_pentameter = iamb * 5

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
        meter, rhyme = match_word(word, meter)
    return meter

def match_phones(phones, meter):
    beats = segment_beats(phones)
    if not beats: return None, None
    lobeat, hibeat = argh(beats)
    v, nvowels = 0, len(beats)
    p, nphones = 0, len(phones)
    for j, m in enumerate(meter):
        if nphones <= p:
            return meter[j+1:], None
        if m == rhymed:
            # NB we assume a rhymed may only appear once, at the end of meter
            # XXX I think this is not quite right: e.g. 'intelligible'
            #  against meter (0,1,0,rhymed) produces rhyme 'gible' here,
            #  but it should fail:
            return match_as_rhyme(phones[p:], lobeat, hibeat)
        while not pronounce.is_vowel(phones[p]):
            p += 1
            if nphones <= p:
                return None, None
        if not match_beat(int(phones[p][-1]), m, lobeat, hibeat):
            # XXX let's try a special case improvement until we can
            #   better it:
            if beats == [1, 0, 0] and meter[:3] == (1, 0, 1):
                return meter[3:], None
            return None, None
        p += 1
        v += 1
        if v == nvowels:
            return meter[j+1:], None
    return None, None             # XXX was (), None


# Unchanged from verse.py from here down

# TODO: Can we just penalize unstressables (to varying degrees)
#  instead of banning them, and then include more words in this set?
unstressables = 'a an of the'.split()
if True:
    unstressables += 'am and for in is on or that to with'.split()
    unstressables += 'are as be by he him his her my she them us we'.split()
    unstressables += 'its they their were you your'.split()
    unstressables += 'at do did from i it me'.split()
    unstressables += 'but had has have our shall was will'.split()
    unstressables += 'dost hast hath shalt thee thou thy wilt ye'.split()
    unstressables += 'if how what when where who why'.split()
    unstressables += 'can so this though which'.split()
    unstressables += 'could should would'.split()
    unstressables += 'all like nor out too yet'.split()
    unstressables += 'near through while whose'.split()
    unstressables += 'these those'.split()
    unstressables += 'came come'.split()
    unstressables += 'none one two three four five six eight nine ten'.split()
    unstressables += 'ah en et la may non off per re than un'.split()
unstressables = frozenset(unstressables)

bad_words = frozenset(string.ascii_lowercase) - frozenset('aio')
bad_words |= frozenset('co il th'.split())

def match_word(word, meter):
    if meter and meter[0] and word in unstressables:
        return None, None
    if True:
        if word == '<S>':
            return meter, None
    try:
        phones = pronounce.pronounce(word)
    except KeyError:
        return try_guess(word, meter)
    else:
        return match_phones(phones, meter)

import guessbeats
guesses = guessbeats.load()

def try_guess(word, meter):
#    print 'YO! TRYING', word
    try:
        beats = guesses[word]
    except KeyError:
        return None, None
    if not beats: return None, None
    lobeat, hibeat = argh(beats)
    nvowels = len(beats)
    for j, m in enumerate(meter):
        if nvowels <= j:
            return meter[j:], None
        if m == rhymed:
            return None, None
        if not match_beat(beats[j], m, lobeat, hibeat):
            # XXX let's try a special case improvement until we can
            #   better it:
            if beats == (1, 0, 0,) and meter[:3] == (1, 0, 1):
                return meter[3:], None
            return None, None
    return None, None

sheeshtable = [0, 2, 1]
def argh(beats):
    sheesh = [sheeshtable[b] for b in beats]
    return min(sheesh), max(sheesh)

def match_as_rhyme(phones, lobeat, hibeat):
    beats = segment_beats(phones)
    assert beats
    if beats[0] == 1 or lobeat == hibeat:
        return (), phones
    return None, None

def match_beat(beat, meter_beat, lobeat, hibeat):
    # TODO: use 1/2 distinction in meter
    if meter_beat == 0:
        rv = (sheeshtable[beat] == lobeat)
    else:
        rv = (lobeat < sheeshtable[beat] or lobeat == hibeat)
    return rv

def memo(f):
    "Memoize function f."
    table = {}
    def fm(*x):
        if x not in table:
            table[x] = f(*x)
        return table[x]
    fm.memo = table
    return fm

@memo
def segment_beats(phones):
    return [int(phone[-1]) for phone in phones if pronounce.is_vowel(phone)]


def rhyme_matches(phones1, phones2):
    return onset(phones1) != onset(phones2) and rime(phones1) == rime(phones2)

def onset(phones): return phones[:find_rime(phones)]
def rime(phones):  return phones[find_rime(phones):]

def find_rime(phones):
    assert isinstance(phones, tuple), "phones: %r" % phones
    for i, ph in enumerate(phones):
        if pronounce.is_vowel(ph):
            return i
    assert False



if __name__ == '__main__':
    main()
