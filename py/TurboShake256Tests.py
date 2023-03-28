# -*- coding: utf-8 -*-
# Implementation by Gilles Van Assche and Benoit Viguier, hereby denoted as "the implementers".
#
# For more information, feedback or questions, please refer to our website:
# https://keccak.team/
#
# To the extent possible under law, the implementers has waived all copyright
# and related or neighboring rights to the source code in this file.
# http://creativecommons.org/publicdomain/zero/1.0/

from __future__ import print_function
import TurboShake256

def generateSimpleRawMaterial(length, seed1, seed2):
    seed2 = seed2 % 8
    return bytes([(seed1 + 161*length - ((i%256) << seed2) - ((i%256) >> (8-seed2)) + i)%256 for i in range(length)])

customizationByteSize = 32

def performTestTurboSHAKE256OneInput(inputLen, outputLen, customLen):
    customizationString = generateSimpleRawMaterial(customizationByteSize, customLen, 97)[0:customLen]
    inputMessage = generateSimpleRawMaterial(inputLen, outputLen, inputLen + customLen)
    print("outputLen {0:5d}, inputLen {1:5d}, customLen {2:3d}".format(outputLen, inputLen, customLen))
    output = TurboShake256.TurboSHAKE256(inputMessage, customizationString, outputLen)
    print("Kangaroo-Twelve")
    print("Input of {0:d} bytes:".format(inputLen), end='')
    for i in range(min(inputLen, 16)):
        print(" {0:02x}".format(inputMessage[i]), end='')
    if (inputLen > 16):
        print(" ...", end='')
    print("")
    print("Output of {0:d} bytes:".format(outputLen), end='')
    for i in range(outputLen):
        print(" {0:02x}".format(output[i]), end='')
    print("")
    print("")

def performTestTurboSHAKE256():
    cBlockSize = 8192
    outputLen = 256//8
    customLen = 0
    for inputLen in range(cBlockSize*9+124):
        performTestTurboSHAKE256OneInput(inputLen, outputLen, customLen)

    outputLen = 128//8
    while(outputLen <= 512//8):
        inputLen = 0
        while(inputLen <= (3*cBlockSize)):
            customLen = 0
            while(customLen <= customizationByteSize):
                performTestTurboSHAKE256OneInput(inputLen, outputLen, customLen)
                customLen += 7
            inputLen = (inputLen + 167) if (inputLen > 0) else 1
        outputLen = outputLen*2

def performShortTestTurboSHAKE256():
    cBlockSize = 8192
    outputLen = 256//8
    customLen = 0
    for inputLen in range(4):
        performTestTurboSHAKE256OneInput(inputLen, outputLen, customLen)
    performTestTurboSHAKE256OneInput(27121, outputLen, customLen)

#performTestTurboSHAKE256()
#performShortTestTurboSHAKE256()

def outputHex(s):
    for i in range(len(s)):
        print("{0:02x}".format(s[i]), end=' ')
    print()
    print()

def printTestVectors():
    print("TurboSHAKE256(M=empty, D=0x07, 64 output bytes):")
    outputHex(TurboShake256.TurboSHAKE256(b'', 0x7, 64))
    print("TurboSHAKE256(M=empty, D=0x07, 10032 output bytes), last 32 bytes:")
    outputHex(TurboShake256.TurboSHAKE256(b'', 0x7, 10032)[10000:])
    for i in range(7):
        M = bytearray([(j % 251) for j in range(17**i)])
        print("TurboSHAKE256(M=pattern 0x00 to 0xFA for 17^{0:d} bytes, D=0x07, 64 output bytes):".format(i))
        outputHex(TurboShake256.TurboSHAKE256(M, 0x7, 64))
    print("TurboSHAKE256(M=empty, D=0x0B, 64 output bytes):")
    outputHex(TurboShake256.TurboSHAKE256(b'', 0xB, 64))
    for i in range(4):
        M = bytearray([0xFF for j in range(2**i-1)])
        print("TurboSHAKE256(M={0:d} times byte 0xFF, D=0x06, 64 output bytes):".format(2**i-1))
        outputHex(TurboShake256.TurboSHAKE256(M, 0x6, 64))

printTestVectors()