#!/bin/python
#
# sahysmodIO.py
#
# Usage:
#
# CSV to INP:
# python sahysmodIO.py exampleIn.csv exampleOut.inp 
#
# INP to CSV:
# python sahysmodIO.py exampleIn.inp exampleOut.csv
#
# jerome.boisvert-chouinard@mail.mcgill.ca
#
##########
import mioparser
import sys
from pprint import pprint

CSVTEMPLATE = 'sahysmod.csv.tmpl'
INPTEMPLATE = 'sahysmod.inp.tmpl'
CSVCOMMENTS = 'sahysmod.csv.comments.txt'

paramsToTranspose = [
    'A',
    'B',
    'KCA',
    'KCB',
    'PP',
    'EPA',
    'EPB',
    'EPU',
    'SIU',
    'SOU',
    'SOA',
    'SOB',
    'GW',
    'FCD',
    'LC',
    'CIC',
    'IAA',
    'IAB',
    'GU',
    'FW',
    'FSA',
    'FSB',
    'FSU',
    'HS'
]


def transposeParams(parameterDictionary):
    for param in paramsToTranspose:
        arrayA = parameterDictionary[param]
        arrayB = []
        for i in range(len(arrayA[0])):
            arrayB.append([])
        for vector in arrayA:
            i=0
            for element in vector:
                arrayB[i].append(element)
                i+=1
        parameterDictionary[param] = arrayB


def main(*args):
    fromFn = args[1]
    toFn = args[2]

    fromTemplate = CSVTEMPLATE if fromFn[-3:] == 'csv' else INPTEMPLATE
    toTemplate = INPTEMPLATE if fromFn[-3:] == 'csv' else CSVTEMPLATE

    paramDictionary = mioparser.readFile(fromFn, fromTemplate)
    transposeParams(paramDictionary)

    N_IN_S = []
    SEASON = []
    NN_IN = int(paramDictionary['NN_IN'])
    for i in range(NN_IN):
        N_IN_S.append(('{}'.format(i),'',''))
        SEASON.append(('1', '2', '3'))

    paramDictionary['NINETYNINE'] = '99'
    paramDictionary['ONE'] = '1'
    paramDictionary['FOURS'] = ['4'] * NN_IN
    paramDictionary['N_IN_S'] =  N_IN_S
    paramDictionary['SEASON'] = SEASON
    paramDictionary['NNS'] = ['{}'.format(i) for i in range(1, int(paramDictionary['NS'])+1)]

    with open(CSVCOMMENTS, 'r') as commentsF:
        paramDictionary['#'] = [line.strip() for line in commentsF.read().split('\n')]

    mioparser.writeFile(paramDictionary, toFn, toTemplate)
    return 0


if __name__ == '__main__':
    main(*sys.argv)