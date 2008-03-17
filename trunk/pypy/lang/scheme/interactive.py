#!/usr/bin/env python
""" Interactive (untranslatable) version of the pypy
scheme interpreter
"""
import autopath
from pypy.lang.scheme.object import ExecutionContext, SchemeException, \
        SchemeQuit
from pypy.lang.scheme.ssparser import parse
from pypy.rlib.parsing.makepackrat import BacktrackException
import os, sys

def check_parens(s):
    return s.count("(") == s.count(")")

def interactive():
    print "PyPy Scheme interpreter"
    ctx = ExecutionContext()
    to_exec = ""
    cont = False
    while 1:
        if cont:
            ps = '.. '
        else:
            ps = '-> '
        sys.stdout.write(ps)
        to_exec += sys.stdin.readline()
        if to_exec == "\n":
            to_exec = ""
        elif check_parens(to_exec):
            try:
                if to_exec == "":
                    print
                    raise SchemeQuit
                print parse(to_exec)[0].eval(ctx).to_string()
            except SchemeQuit, e:
                break
            except BacktrackException, e:
                print "syntax error"
            except SchemeException, e:
                print "error: %s" % e

            to_exec = ""
            cont = False
        else:
            cont = True

if __name__ == '__main__':
    interactive()
