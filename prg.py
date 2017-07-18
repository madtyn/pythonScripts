#!/usr/bin/python3

from random import randint
from numpy import arange, array

P = array([295075153])  # about 2^28

seeds = array([210205973, 22795300, 58776750, 121262470, 264731963,
               140842553, 242590528, 195244728, 86752752])

# findNext(0) = ( 178119821 , 197537961 )


def findNext(i):
    for x in arange(0, P[0]):
        a = (2 * x + 5) % P[0]
        b = (3 * (seeds[i] ^ x) + 7) % P[0]
        if (a ^ b) == seeds[i + 1]:
            print("(", a, ",", b, ")")
            return


class WeakPrng(object):
    def __init__(self, p):  # generate seed with 56 bits of entropy
        self.p = p
        self.x = randint(0, p)
        self.y = randint(0, p)

    def __next__(self):
        # x_{i+1} = 2*x_{i}+5  (mod p)
        self.x = (2 * self.x + 5) % self.p

        # y_{i+1} = 3*y_{i}+7 (mod p)
        self.y = (3 * self.y + 7) % self.p

        # z_{i+1} = x_{i+1} xor y_{i+1}
        return self.x ^ self.y


prng = WeakPrng(P)
for i in range(1, 10):
    print("output #%d: %d" % (i, next(prng)))
