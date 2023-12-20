# -*- coding: utf-8 -*-
# Implementation by Gilles Van Assche, hereby denoted as "the implementer".
#
# For more information, feedback or questions, please refer to our website:
# https://keccak.team/
#
# To the extent possible under law, the implementer has waived all copyright
# and related or neighboring rights to the source code in this file.
# http://creativecommons.org/publicdomain/zero/1.0/

def ROL64(a, n):
    return ((a >> (64-(n%64))) + (a << (n%64))) % (1 << 64)

def KeccakP1600onLanes(lanes, nrRounds):
    R = 1
    for round in range(24):
        if (round + nrRounds >= 24):
            # θ
            C = [lanes[x][0] ^ lanes[x][1] ^ lanes[x][2] ^ lanes[x][3] ^ lanes[x][4] for x in range(5)]
            D = [C[(x+4)%5] ^ ROL64(C[(x+1)%5], 1) for x in range(5)]
            lanes = [[lanes[x][y]^D[x] for y in range(5)] for x in range(5)]
            # ρ and π
            (x, y) = (1, 0)
            current = lanes[x][y]
            for t in range(24):
                (x, y) = (y, (2*x+3*y)%5)
                (current, lanes[x][y]) = (lanes[x][y], ROL64(current, (t+1)*(t+2)//2))
            # χ
            for y in range(5):
                T = [lanes[x][y] for x in range(5)]
                for x in range(5):
                    lanes[x][y] = T[x] ^((~T[(x+1)%5]) & T[(x+2)%5])
            # ι
            for j in range(7):
                R = ((R << 1) ^ ((R >> 7)*0x71)) % 256
                if (R & 2):
                    lanes[0][0] = lanes[0][0] ^ (1 << ((1<<j)-1))
        else:
            for j in range(7):
                R = ((R << 1) ^ ((R >> 7)*0x71)) % 256
    return lanes

def load64(b):
    return sum((b[i] << (8*i)) for i in range(8))

def store64(a):
    return bytearray((a >> (8*i)) % 256 for i in range(8))

def KeccakP1600(state, nrRounds):
    lanes = [[load64(state[8*(x+5*y):8*(x+5*y)+8]) for y in range(5)] for x in range(5)]
    lanes = KeccakP1600onLanes(lanes, nrRounds)
    state = bytearray().join([store64(lanes[x][y]) for y in range(5) for x in range(5)])
    return bytearray(state)

def TurboSHAKE(c, M, D, outputByteLen):
    outputBytes = bytearray()
    state = bytearray([0 for i in range(200)])
    rateInBytes = (1600-c)//8
    blockSize = 0
    inputOffset = 0
    # === Absorb all the input blocks ===
    while(inputOffset < len(M)):
        blockSize = min(len(M)-inputOffset, rateInBytes)
        for i in range(blockSize):
            state[i] = state[i] ^ M[i+inputOffset]
        inputOffset = inputOffset + blockSize
        if (blockSize == rateInBytes):
            state = KeccakP1600(state, 12)
            blockSize = 0
    # === Do the padding and switch to the squeezing phase ===
    state[blockSize] = state[blockSize] ^ D
    if (((D & 0x80) != 0) and (blockSize == (rateInBytes-1))):
        state = KeccakP1600(state, 12)
    state[rateInBytes-1] = state[rateInBytes-1] ^ 0x80
    state = KeccakP1600(state, 12)
    # === Squeeze out all the output blocks ===
    while(outputByteLen > 0):
        blockSize = min(outputByteLen, rateInBytes)
        outputBytes = outputBytes + state[0:blockSize]
        outputByteLen = outputByteLen - blockSize
        if (outputByteLen > 0):
            state = KeccakP1600(state, 12)
    return outputBytes

def TurboSHAKE128(M, D, outputByteLen):
    return TurboSHAKE(256, M, D, outputByteLen)

def TurboSHAKE256(M, D, outputByteLen):
    return TurboSHAKE(512, M, D, outputByteLen)

class TurboSHAKEAbosrb:
    '''TurboSHAKE in the absorb state.'''

    def __init__(self, c, D):
        '''
        Initialize the absorb state with capacity `c` (number of bits) and
        domain separation byte `D`.
        '''
        self.D = D
        self.rateInBytes = (1600-c)//8
        self.state = bytearray([0 for i in range(200)])
        self.stateOffset = 0

    def update(self, M):
        '''
        Update the absorb state with message fragment `M`.
        '''
        inputOffset = 0
        while inputOffset < len(M):
            length = len(M)-inputOffset
            blockSize = min(length, self.rateInBytes-self.stateOffset)
            for i in range(blockSize):
                self.state[i+self.stateOffset] ^= M[i+inputOffset]
            inputOffset += blockSize
            self.stateOffset += blockSize
            if self.stateOffset == self.rateInBytes:
                self.state = KeccakP1600(self.state, 12)
                self.stateOffset = 0

    def squeeze(self):
        '''
        Consume the absorb state and return the TurboSHAKE squeeze state.
        '''
        state = self.state[:]  # deep copy
        state[self.stateOffset] ^= self.D
        if (((self.D & 0x80) != 0) and \
            (self.stateOffset == (self.rateInBytes-1))):
            state = KeccakP1600(state, 12)
        state[self.rateInBytes-1] = state[self.rateInBytes-1] ^ 0x80
        state = KeccakP1600(state, 12)

        squeeze = TurboSHAKESqueeze()
        squeeze.rateInBytes = self.rateInBytes
        squeeze.state = state
        squeeze.stateOffset = 0
        return squeeze

class TurboSHAKESqueeze:
    '''TurboSHAKE in the squeeze state.'''

    def next(self, length):
        '''
        Return the next `length` bytes of output and update the squeeze state.
        '''
        outputBytes = bytearray()
        while length > 0:
             blockSize = min(length, self.rateInBytes-self.stateOffset)
             length -= blockSize
             outputBytes += \
                 self.state[self.stateOffset:self.stateOffset+blockSize]
             self.stateOffset += blockSize
             if self.stateOffset == self.rateInBytes:
                self.state = KeccakP1600(self.state, 12)
                self.stateOffset = 0
        return outputBytes

def NewTurboSHAKE128(D):
    '''
    Return the absorb state for TurboSHAKE128 with domain separation byte `D`.
    '''
    return TurboSHAKEAbosrb(256, D)

def NewTurboSHAKE256(D):
    '''
    Return the absorb state for TurboSHAKE256 with domain separation byte `D`.
    '''
    return TurboSHAKEAbosrb(512, D)

def testAPI(stateful, oneshot):
    '''Test that the outputs of the stateful and oneshot APIs match.'''

    testCases = [
        {
            'fragments': [],
            'lengths': [],
        },
        {
            'fragments': [],
            'lengths': [
                1000,
            ],
        },
        {
            'fragments': [
                b'\xff' * 500,
            ],
            'lengths': [
                12,
            ],
        },
        {
            'fragments': [
                b'hello',
                b', ',
                b'',
                b'world',
            ],
            'lengths': [
                1,
                17,
                256,
                128,
                0,
                7,
                14,
            ],
        },
        {
            'fragments': [
                b'\xff' * 1024,
                b'\x17' * 23,
                b'',
                b'\xf1' * 512,
            ],
            'lengths': [
                1000,
                0,
                0,
                14,
            ],

        }
    ]

    D = 99
    for (i, testCase) in enumerate(testCases):
        absorb = stateful(D)
        message = bytearray()
        for fragment in testCase['fragments']:
            absorb.update(fragment)
            message += fragment
        squeeze = absorb.squeeze()
        outputBytes = b''
        outputByteLen = 0
        for length in testCase['lengths']:
            outputBytes += squeeze.next(length)
            outputByteLen += length
        expectedOutputBytes = oneshot(message, D, outputByteLen)
        if outputBytes != expectedOutputBytes:
            raise Exception('test case {} failed: got {}; want {}'.format(
                i,
                outputBytes.hex(),
                expectedOutputBytes.hex(),
            ))

if __name__ == '__main__':
    testAPI(NewTurboSHAKE128, TurboSHAKE128)
    testAPI(NewTurboSHAKE256, TurboSHAKE256)