#!/bin/python
# -*- coding: utf-8 -*

import argparse
from os import walk
from os.path import isdir, isfile
import subprocess

class color:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    GREY = '\033[38;5;244m'
    RED = '\033[91m'
    VIOLET = '\033[95m'
    YELLOW = '\033[93m'
    END = '\033[0m'
    BOLD = '\033[1m'


class Setting:
    def __init__(self, keyword, symbol, color):
        self.color = color
        self.keyword = keyword
        self.symbol = symbol

MARKS = [
    Setting('BUG', '☢', color.RED),
    Setting('FIXME', '☠', color.RED),
    Setting('HACK', '✄', color.YELLOW),
    Setting('NOTE', '✐', color.YELLOW),
    Setting('OPTIMIZE', '↻', color.YELLOW),
    Setting('TODO', '✓', color.BLUE),
    Setting('XXX', '✗', color.VIOLET),
]


COMMENTS = ['/**', '/*', '//', '#', '\'\'', '""', ';', '%', '--']
COMMENTS_MID = ['*']
COMMENTS_END = {
    '/**':  ['**/', '*/'],
    '/*':   ['*/']
}


class FileDir(argparse.Action):
    def __call__(self, parser, args, dest, option_string=None):
        files = []
        for entry in dest:
            if isfile(entry):
                files.append(entry)
            elif isdir(entry):
                for (dirpath, dirnames, filenames) in walk(entry):
                    for filename in filenames:
                        path = "{}/{}".format(dirpath, filename)
                        files.append(path)
        files.sort()
        setattr(args, self.dest, files)

    def type(dest):
        if not isdir(dest) and not isfile(dest):
            msg = "{} is neither file nor directory".format(dest)
            raise argparse.ArgumentTypeError(msg)
        return dest


class Tofi():
    _filenames = True
    _keywords = True
    _numbers = True
    _symbols = True

    def __init__(self,
                 numbers=True,
                 symbols=True,
                 keywords=True,
                 filenames=True):
        self._filenames = filenames
        self._keywords = keywords
        self._numbers = numbers
        self._symbols = symbols

    def _build(self, mark, line, num, indent):
        prefix = ''

        if self._numbers:
            prefix = '{}{:>{}} '.format(color.GREY, num, indent)

        if self._symbols:
            prefix = prefix + color.BOLD + mark.color + mark.symbol + ' ' + color.END

        if self._keywords:
            prefix = prefix + color.BOLD + mark.color + mark.keyword + color.END

        line = line.split('\n')[0]
        text = line.split(mark.keyword)
        output = prefix + mark.keyword.join(text[1:])

        # Get comment symbols
        text = text[0].split()

        if text:
            text = text[-1][-3:]
            for comment in COMMENTS:
                if comment in text:
                    return (output, comment)

        return (None, None)


    def _build_follower(self, line, prefix):
        found = True
        line = line.split('\n')[0]
        text = line.split(prefix)

        if len(text) < 2:
            found = False
            tmp = line.split()
            if len(tmp) > 0 and tmp[0] in COMMENTS_MID:
                text = tmp[1:]
                found = True

        if prefix in COMMENTS_END:
            found = True
      
        if not found:
            return None

        line = ' '.join(text)
        line = ' ' +  ' '.join(line.split())

        return line


    def _print(self, output, prefix):
        if output:
            if prefix in COMMENTS_END:
                for symbol in COMMENTS_END[prefix]:
                    output = output.split(symbol)[0]
            print(output)


    def parse(self, path, print_filename):
        num = 0
        output = None
        symbol = None
        prefix = None
        found = False

        f = open(path, 'r')
        try:
            text = f.readlines()
        except UnicodeDecodeError:
            return False

        indent = sum(1 for line in text)
        indent = len(str(indent))

        for line in text:
            num += 1

            prefix = None
            for mark in MARKS:
                if mark.keyword in line:
                    (suffix, prefix) = self._build(mark, line, num, indent)
                    if suffix:
                        if not found and print_filename:
                            found = True
                            print('{}:'.format(path))
                        self._print(output, symbol)
                        output = suffix
                        symbol = prefix

            if not prefix and symbol:
                append = self._build_follower(line, symbol)
                if append:
                    output += append
                else:
                    symbol = None

        self._print(output, symbol)
        f.close()

        return found


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Print TODOs, FIXMEs & Co.')

    parser.add_argument('-f', '--hide-filenames', action='store_true',
                        help='hide filenames')
    parser.add_argument('-k', '--hide-keywords', action='store_true',
                        help='hide keywords')
    parser.add_argument('-n', '--hide-numbers', action='store_true',
                        help='hide number of line')
    parser.add_argument('-s', '--hide-symbols', action='store_true',
                        help='hide symbols')
    parser.add_argument('file', nargs='*', type=FileDir.type, action=FileDir,
                        help='source files', default='.')

    args = parser.parse_args()

    if args.file == []:
        parser.print_usage()
        print('tofi.py: error: the following arguments are required: file')
        exit(2)

    try:
        tofi = Tofi(not args.hide_numbers,
                    not args.hide_symbols,
                    not args.hide_keywords,
                    not args.hide_filenames)
    except ValueError:
        exit(1)

    num = len(args.file)
    if num == 1 or not tofi._filenames:
        num = 0

    for file in args.file:
        found = tofi.parse(file, num > 0)
        num -= 1
        if found and num > 0:
            print('')

    exit(0)
