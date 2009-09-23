"""
no-vowel words: one beat

silent: -e -ed -es[er, usually]

one beat:
ae
ai
au
ea
ee
ei
ie
oa
oo
"""

def main(file):
    for line in file:
        word = line.split()[0]
        print '%s\t%s' % (''.join(str(b) for b in guess_beats(word)), word)

def load():
    r = {}
    for line in open('tolkien.unp3.easy'):
        word = line.split()[0]
        r[word] = guess_beats(word)
    return r

vowels = 'aeiou'

def guess_beats(word):
    return beatify(guessing(word))

def beatify(n):
    return (1,) + (0,) * max(0, n - 1)

## guessing('gabbled')
#. 1
## guessing('bled')
#. 0

def guessing(word):
    if not word:
        return 0
    if word in ('e', 'ed'):
        return 0
    if word[:2] == 'qu':
        return guessing(word[2:])
    if word in 'ales ides ires ites ives odes okes oles ones ores'.split():
        return 1
    if word[0] not in vowels:
        if 4 == len(word) and word[1] not in vowels and word[2:] == 'es':
            return 1
        return guessing(word[1:])
    if word[:2] in 'ae ai au ea ee ei ie oa oe oi oo ou'.split():
        return 1 + guessing(word[2:])
    return 1 + guessing(word[1:])

if __name__ == '__main__':
    import sys
    main(sys.stdin)
