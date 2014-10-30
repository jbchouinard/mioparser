#!/bin/python

# mioparser.py
#
# This module can parse fixed format text files based on template files
# and convert between different formats.
# 
# Originally written to exchange data between legacy FORTRAN and Pascal 
# scientific models that use weirdly formatted text files with a varying
# number of fixed column width and withespace separated lines.
# 
# Example commmand line usage:
#
# python mioparser.py -r example_in.txt example1.tmpl
#
# Parses example_in.txt and print parsed parameters as a dictionary
# This is only really useful for debugging.
#
# python mioparser.py -c example_in.txt example1.tmpl example_out.txt example2.tmpl
#
# Converts example_in.txt (in example1 format) to example2 format, and writes output to example_out.txt
#
# See documentation for details on how to write template files.
#
# jerome.boisvert-chouinard@mail.mcgill.ca
#
##########
import sys
import itertools
from pprint import pprint


#Read plain text line
def parseLLine(line, parameterNames, parameterDictionary):
    if parameterNames[0] == '#':
        parameterDictionary['#'].append(line.strip())
    else:
        parameterDictionary[parameterNames[0]] = line.strip()
    return parameterDictionary


#Construct plain text line
def buildLLine(parameterNames, parameterDictionary):
    if parameterNames[0] == '#':
        try:
            line = parameterDictionary['#'].pop(0)
        except KeyError:
            line = ''
        except IndexError:
            line = ''
    else:
        line = parameterDictionary[parameterNames[0]]
    return line + '\n'


#Read fixed column width line
def parseFLine(line, parameterNames, columnWidths, parameterDictionary):
    cursor = 0
    arrayParam = 0

    for i in range(len(columnWidths)):
        if not arrayParam:
            if parameterNames[i][0] != '*':
                parameterDictionary[parameterNames[i]] = line[cursor:cursor+columnWidths[i]].strip('\n')
                cursor += columnWidths[i]
            else:
                arrayParam = parameterNames[i][1:]
                parameterDictionary[arrayParam] = []
        if arrayParam:
            parameterDictionary[arrayParam].append(line[cursor:cursor+columnWidths[i]].strip())
            cursor += columnWidths[i]
    return parameterDictionary


# Construct fixed column width line
def buildFLine(parameterNames, columnWidths, parameterDictionary):
    lineOut = ''
    arrayParam = 0
    for i in range(len(columnWidths)):
        if not arrayParam:
            paramName = parameterNames[i]
            if paramName[0] != '*':
                param = parameterDictionary[paramName]
                param = (columnWidths[i] - len(param)) * ' ' + param
                lineOut += param
            else:
                arrayParam = paramName.strip('*')
                paramList = [parameter for parameter in parameterDictionary[arrayParam]]
        if arrayParam:
            param = paramList.pop(0)
            param = (columnWidths[i] - len(param)) * ' ' + param
            lineOut += param
    return lineOut + '  \n'


def parseDLine(line, parameterNames, delim, parameterDictionary):
    line = line.strip()
    if delim == 'W':
        values = line.split()
    else:
        values = [value.strip() for value in line.split(delim)]
    arrayParam = 0
    for i in range(len(values)):
        if not arrayParam:
            try:
                if parameterNames[i][0] != '*':
                    parameterDictionary[parameterNames[i]] = values[i]
                else:
                    arrayParam = parameterNames[i][1:]
                    parameterDictionary[arrayParam] = []
            except IndexError:
                return parameterDictionary
        if arrayParam:
            parameterDictionary[arrayParam].append(values[i])
    return parameterDictionary


def buildDLine(parameterNames, delim, parameterDictionary):
    values = []
    #If the separator is whitespace (denotes by 'W'), use a space as separator
    delim = '  ' if delim == 'W' else delim
    for paramName in parameterNames:
        if paramName[0] != '*':
            values.append(parameterDictionary[paramName])
        else:
            values += parameterDictionary[paramName.strip('*')]
        #print(values)
    return delim.join(values) + '  \n'


def parseLine(line, parameterNames, lineSpec, parameterDictionary):
    if lineSpec[0] == 'L':
        parseLLine(line, parameterNames, parameterDictionary)
    elif lineSpec[0] == 'F':
        parseFLine(line, parameterNames, lineSpec[1], parameterDictionary)
    elif lineSpec[0] == 'D':
        parseDLine(line, parameterNames, lineSpec[1], parameterDictionary)
    return parameterDictionary


def buildLine(parameterNames, lineSpec, parameterDictionary, configDictionary):
    if lineSpec[0] == 'L':
        line = buildLLine(parameterNames, parameterDictionary)
    elif lineSpec[0] == 'F':
        line = buildFLine(parameterNames, lineSpec[1], parameterDictionary)
    elif lineSpec[0] == 'D':
        line = buildDLine(parameterNames, lineSpec[1], parameterDictionary)
    if 'CSVPAD' in configDictionary.keys():
        diff = configDictionary['CSVPAD'] - 1 - line.count(',')
        if diff > 0:
            line = line.strip() + ',' * diff + '\n'
    return line


# Easy optimization option: rewrite to use numpy.zeros instead...
def createArrayOfZeros(*dims):
    if len(dims) == 1:
        return [0]*dims[0]
    else:
        arr = []
        for i in range(dims[0]):
            arr.append(createArrayOfZeros(*dims[1:]))
        return arr


def readFile(contentFn, templateFn):
    #k=1
    parameterDictionary = {'#':[]}
    configDictionary = {}
    with open(contentFn, 'r') as contentF, open(templateFn, 'r') as templateF:
        for templateLine in templateF:
            #print('parsing line {} of file {}'.format(k, templateFn))
            #k+=1
            if templateLine[0] == '!':
                exec('configTuple = ' + templateLine[1:].strip())
                configDictionary[configTuple[0]] = configTuple[1]
            elif templateLine[0] != '#':
                exec('templateTuple = ' + templateLine.strip())
                if templateTuple[0][0:4] != 'FOR[':
                    contentLine = contentF.readline().strip('\n')
                    #print(contentLine)
                    parseLine(contentLine, templateTuple[1], templateTuple[0], parameterDictionary)
                else:
                    dims = [i.strip(']') for i in templateTuple[0].split('[')][1:]
                    for i in range(len(dims)):
                        try:
                            dims[i] = int(dims[i])
                        except ValueError:
                            dims[i] = int(parameterDictionary[dims[i]])
                    lineSpecTuple = templateTuple[1]
                    for lineSpec in lineSpecTuple:

                        for paramName in lineSpec[1]:
                            paramName = paramName.strip('*')
                            parameterDictionary[paramName] = createArrayOfZeros(*dims)
                    iterdims = [range(dim) for dim in dims]
                    for indices in itertools.product(*iterdims):
                        tempDict = {}
                        indicesString = ''.join(['[{}]'.format(i) for i in indices])
                        for lineSpec in lineSpecTuple:
                            contentLine = contentF.readline().strip('\n')
                            #pprint(contentLine)
                            parseLine(contentLine, lineSpec[1], lineSpec[0], tempDict)
                            #pprint(tempDict)
                            for paramName in lineSpec[1]:
                                paramName = paramName.strip("*")
                                exec('parameterDictionary[paramName]' + indicesString + '= tempDict[paramName]')
    return parameterDictionary


def writeFile(parameterDictionary, contentFn, templateFn):
    #k=1
    configDictionary = {}
    with open(contentFn, 'w') as contentF, open(templateFn, 'r') as templateF:
        for templateLine in templateF:
            #print('building line {} of file {}'.format(k, templateFn))
            #k+=1
            if templateLine[0] == '!':
                exec('configTuple = ' + templateLine[1:].strip())
                configDictionary[configTuple[0]] = configTuple[1]
            elif templateLine[0] != '#':
                exec('templateTuple = ' + templateLine.strip())
                if templateTuple[0][0:4] != 'FOR[':
                    contentF.write(buildLine(templateTuple[1], templateTuple[0], parameterDictionary, configDictionary))
                else:
                    dims = [i.strip(']') for i in templateTuple[0].split('[')][1:]
                    for i in range(len(dims)):
                        try:
                            dims[i] = int(dims[i])
                        except ValueError:
                            dims[i] = int(parameterDictionary[dims[i]])
                    lineSpecTuple = templateTuple[1]
                    iterdims = [range(dim) for dim in dims]
                    for indices in itertools.product(*iterdims):
                        tempDict = {}
                        indicesString = ''.join(['[{}]'.format(i) for i in indices])
                        for lineSpec in lineSpecTuple:
                            for paramName in lineSpec[1]:
                                paramName = paramName.strip('*')
                                exec('tempDict[paramName] = parameterDictionary[paramName]' + indicesString)
                            contentF.write(buildLine(lineSpec[1], lineSpec[0], tempDict, configDictionary))
    return contentFn


def main(*args):
    if args[1] == '-r':
        parameterDictionary = readFile(args[2], args[3])
        pprint(parameterDictionary[args[4]])
        #pprint(parameterDictionary)
    elif args[1] == '-c':
        parameterDictionary = readFile(args[2], args[3])
        writeFile(parameterDictionary, args[4], args[5])
    return 0


if __name__ == '__main__':
    main(*sys.argv)