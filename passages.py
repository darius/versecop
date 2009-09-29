import re
import sys

import metercop

def main():
    """Print iambic-pentameter passages collected from stdin without
    regard to line-breaks; longer ones first."""
    passages = text_passages(sys.stdin.read())
    for nlines in sorted(passages.keys(), reverse=True):
        for passage in passages[nlines]:
            print passage
            print

def text_passages(text, min_length=None):
    return collect_passages(get_words(text), min_length)

def collect_passages(words, min_length=None):
    """Return a dict mapping #lines (>=min_length) to a list of
    passages of that many iambic-pentameter lines (perhaps with a
    partial line after)."""
    if min_length is None: min_length = 2
    results = {}
    dupes = set()
    # dupes filters out all subsequences of the passages we pick. (We
    # still look for more passages starting right within each passage
    # picked, because we don't know a priori where the iambic-
    # pentameter lines start -- we don't know that the first "reading
    # frame" we find is the best one. Thus we suspend judgement and
    # drop the duplicates after.)
    for i in loud_range(len(words)):
        passage = read_passage(tail(words, i))
        nlines = passage.count('\n')
        if min_length <= nlines:
            dupe_key = tuple(passage.split())
            if dupe_key not in dupes:
                results.setdefault(nlines, []).append(passage)
                add_subseqs(dupes, dupe_key[1:])
    return results

def read_passage(words):
    """Return, as a string, any iambic-pentameter lines that start the
    given word-sequence."""
    meter = metercop.iamb * 5
    passage = ''
    for word in words:
        meter, rhyme = metercop.match_word(word, meter)
        if meter is None:
            break
        passage += ' ' + word
        if meter == ():
            passage += '\n'
            meter = metercop.iamb * 5
    return passage

def get_words(text):
    "Return text's words in order."
    return [word.strip("'") for word in re.findall(r"['\w]+", text)]

def loud_range(n):
    "Like xrange(n), but reporting progress to stderr."
    print >>sys.stderr, n
    for i in xrange(n):
        if i % 1000 == 0:
            sys.stderr.write('.')
            sys.stderr.flush()
        yield i
    print >>sys.stderr

def add_subseqs(xs_set, xs):
    "Add all nonempty subsequences of xs to xs_set."
    for i in xrange(len(xs)):
        for j in xrange(i + 1, len(xs) + 1):
            xs_set.add(xs[i:j])

def tail(xs, i):
    "Generate xs[i:] without materializing it."
    return (xs[j] for j in xrange(i, len(xs)))


test_input = """
A brief vision he had of swirling cloud, and in the midst of it towers
and battlements, tall as hills, founded upon a mighty mountain-throne
above immeasurable pits; great courts and dungeons, eyeless prisons
sheer as cliffs, and gaping gates of steel and adamant: and then all
passed. Towers fell and mountains slid; walls crumbled and melted,
crashing down; vast spires of smoke and spouting steams went billowing
up, up, until they toppled like an overwhelming wave, and its wild
crest curled and came foaming down upon the land. And then at last
over the miles between there came a rumble, rising to a deafening
crash and roar; the earth shook, the plain heaved and cracked, and
Orodruin reeled. Fire belched from its riven summit. The skies burst
into thunder seared with lightning. Down like lashing whips fell a
torrent of black rain. And into the heart of the storm, with a cry
that pierced all other sounds, tearing the clouds asunder, the Nazgul
came, shooting like flaming bolts, as caught in the fiery ruin of hill
and sky they crackled, withered, and went out.
"""

def testme():
    result = text_passages(test_input, min_length=1)
    def view(passages):
        return [passage.splitlines() for passage in passages]
    assert sorted(result.keys()) == [1, 2, 3]
    assert view(result[3]) == \
        [[' above immeasurable pits great courts',
          ' and dungeons eyeless prisons sheer as cliffs',
          ' and gaping gates of steel and adamant',
          ' and then all passed']]
    assert view(result[2]) == \
        [[' and melted crashing down vast spires of smoke',
          ' and spouting steams went billowing up up',
          ' until they toppled']]
    assert view(result[1]) == \
        [[' upon a mighty mountain throne above',
          ' immeasurable pits great courts and'],
         [' came foaming down upon the land And then',
          ' at last'],
         [' its riven summit The skies burst into']]


if __name__ == '__main__':
    main()
