import py
from pypy.rlib.parsing.parsing import PackratParser, Rule
from pypy.rlib.parsing.tree import Nonterminal
from pypy.rlib.parsing.regex import StringExpression, RangeExpression
from pypy.rlib.parsing.lexer import Lexer, DummyLexer
from pypy.rlib.parsing.deterministic import compress_char_set, DFA
import string

set = py.builtin.set

ESCAPES = {
    "\\a": "\a",
    "\\b": "\b",
    "\\f": "\f",
    "\\n": "\n",
    "\\r": "\r",
    "\\t": "\t",
    "\\v": "\v",
    "\\":  "\\"
}

for i in range(256):
    # 'x' and numbers are reserved for hexadecimal/octal escapes
    if chr(i) in 'x01234567':
        continue
    escaped = "\\" + chr(i)
    if escaped not in ESCAPES:
        ESCAPES[escaped] = chr(i)
for a in "0123456789ABCDEFabcdef":
    for b in "0123456789ABCDEFabcdef":
        escaped = "\\x%s%s" % (a, b)
        if escaped not in ESCAPES:
            ESCAPES[escaped] = chr(int("%s%s" % (a, b), 16))
for a in "0123":
    for b in "01234567":
        for c in "01234567":
            escaped = "\\x%s%s%s" % (a, b, c)
            if escaped not in ESCAPES:
                ESCAPES[escaped] = chr(int("%s%s%s" % (a, b, c), 8))

def unescape(s):
    result = []
    i = 0
    while i < len(s):
        if s[i] != "\\":
            result.append(s[i])
            i += 1
            continue
        if s[i + 1] == "x":
            escaped = s[i: i + 4]
            i += 4
        elif s[i + 1] in "01234567":
            escaped = s[i: i + 4]
            i += 4
        else:
            escaped = s[i: i + 2]
            i += 2
        if escaped not in ESCAPES:
            raise ValueError("escape %r unknown" % (escaped, ))
        else:
            result.append(ESCAPES[escaped])
    return "".join(result)

syntax =  r"""
EOF:
    !__any__;

parse:
    regex
    [EOF];

regex:
    r1 = concatenation
    '|'
    r2 = regex
    return {r1 | r2}
  | concatenation;

concatenation:
    l = repetition+
    return {reduce(operator.add, l, regex.StringExpression(""))};

repetition:
    r1 = primary
    '*'
    return {r1.kleene()}
  | r1 = primary
    '+'
    return {r1 + r1.kleene()}
  | r1 = primary
    '?'
    return {regex.StringExpression("") | r1}
  | r = primary
    '{'
    n = numrange
    '}'
    return {r * n[0] + reduce(operator.or_, [r * i for i in range(n[1] - n[0] + 1)], regex.StringExpression(""))}
  | primary;

primary:
    ['('] regex [')']
  | range
  | c = char
    return {regex.StringExpression(c)}
  | '.'
    return {regex.RangeExpression(chr(0), chr(255))};

char:
    c = QUOTEDCHAR
    return {unescape(c)}
  | c = CHAR
    return {c};

QUOTEDCHAR:
    `(\\x[0-9a-fA-F]{2})|(\\.)`;

CHAR:
    `[^\*\+\(\)\[\]\{\}\|\.\-\?\,\^]`;

range:
    '['
    s = rangeinner
    ']'
    return {reduce(operator.or_, [regex.RangeExpression(a, chr(ord(a) + b - 1)) for a, b in compress_char_set(s)])};

rangeinner:
    '^'
    s = subrange
    return {set([chr(c) for c in range(256)]) - s}
  | subrange;

subrange:
    l = rangeelement+
    return {reduce(operator.or_, l)};

rangeelement:
    c1 = char
    '-'
    c2 = char
    return {set([chr(i) for i in range(ord(c1), ord(c2) + 1)])}
  | c = char
    return {set([c])};

numrange:
    n1 = NUM
    ','
    n2 = NUM
    return {n1, n2}
  | n1 = NUM
    return {n1, n1};

NUM:
    c = `0|([1-9][0-9]*)`
    return {int(c)};
"""


def parse_regex(s):
    p = RegexParser(s)
    r = p.parse()
    return r

def make_runner(regex, view=False):
    p = RegexParser(regex)
    r = p.parse()
    nfa = r.make_automaton()
    dfa = nfa.make_deterministic()
    if view:
        dfa.view()
    dfa.optimize()
    if view:
        dfa.view()
    r = dfa.get_runner()
    return r














# generated code between this line and its other occurence

from pypy.rlib.parsing.pypackrat import PackratParser, Status
from pypy.rlib.parsing.pypackrat import BacktrackException
from pypy.rlib.parsing import regex
import operator
class Parser(object):
    def EOF(self):
        return self._EOF().result
    def _EOF(self):
        _key = self._pos
        _status = self._dict_EOF.get(_key, None)
        if _status is None:
            _status = self._dict_EOF[_key] = Status()
        else:
            _statusstatus = _status.status
            if _statusstatus == _status.NORMAL:
                self._pos = _status.pos
                return _status
            elif _statusstatus == _status.ERROR:
                raise BacktrackException(_status.error)
            elif (_statusstatus == _status.INPROGRESS or
                  _statusstatus == _status.LEFTRECURSION):
                _status.status = _status.LEFTRECURSION
                if _status.result is not None:
                    self._pos = _status.pos
                    return _status
                else:
                    raise BacktrackException(None)
            elif _statusstatus == _status.SOMESOLUTIONS:
                _status.status = _status.INPROGRESS
        _startingpos = self._pos
        try:
            _result = None
            _error = None
            _choice0 = self._pos
            _stored_result1 = _result
            try:
                _result = self.__any__()
            except BacktrackException:
                self._pos = _choice0
                _result = _stored_result1
            else:
                raise BacktrackException(None)
            if _status.status == _status.LEFTRECURSION:
                if _status.result is not None:
                    if _status.pos >= self._pos:
                        _status.status = _status.NORMAL
                        self._pos = _status.pos
                        return _status
                _status.pos = self._pos
                _status.status = _status.SOMESOLUTIONS
                _status.result = _result
                _status.error = _error
                self._pos = _startingpos
                return self._EOF()
            _status.status = _status.NORMAL
            _status.pos = self._pos
            _status.result = _result
            _status.error = _error
            return _status
        except BacktrackException, _exc:
            _status.pos = -1
            _status.result = None
            _error = _exc.error
            _status.error = _error
            _status.status = _status.ERROR
            raise BacktrackException(_error)
    def parse(self):
        return self._parse().result
    def _parse(self):
        _key = self._pos
        _status = self._dict_parse.get(_key, None)
        if _status is None:
            _status = self._dict_parse[_key] = Status()
        else:
            _statusstatus = _status.status
            if _statusstatus == _status.NORMAL:
                self._pos = _status.pos
                return _status
            elif _statusstatus == _status.ERROR:
                raise BacktrackException(_status.error)
            elif (_statusstatus == _status.INPROGRESS or
                  _statusstatus == _status.LEFTRECURSION):
                _status.status = _status.LEFTRECURSION
                if _status.result is not None:
                    self._pos = _status.pos
                    return _status
                else:
                    raise BacktrackException(None)
            elif _statusstatus == _status.SOMESOLUTIONS:
                _status.status = _status.INPROGRESS
        _startingpos = self._pos
        try:
            _result = None
            _error = None
            _call_status = self._regex()
            _result = _call_status.result
            _error = _call_status.error
            _before_discard0 = _result
            _call_status = self._EOF()
            _result = _call_status.result
            _error = self._combine_errors(_error, _call_status.error)
            _result = _before_discard0
            if _status.status == _status.LEFTRECURSION:
                if _status.result is not None:
                    if _status.pos >= self._pos:
                        _status.status = _status.NORMAL
                        self._pos = _status.pos
                        return _status
                _status.pos = self._pos
                _status.status = _status.SOMESOLUTIONS
                _status.result = _result
                _status.error = _error
                self._pos = _startingpos
                return self._parse()
            _status.status = _status.NORMAL
            _status.pos = self._pos
            _status.result = _result
            _status.error = _error
            return _status
        except BacktrackException, _exc:
            _status.pos = -1
            _status.result = None
            _error = self._combine_errors(_error, _exc.error)
            _status.error = _error
            _status.status = _status.ERROR
            raise BacktrackException(_error)
    def regex(self):
        return self._regex().result
    def _regex(self):
        _key = self._pos
        _status = self._dict_regex.get(_key, None)
        if _status is None:
            _status = self._dict_regex[_key] = Status()
        else:
            _statusstatus = _status.status
            if _statusstatus == _status.NORMAL:
                self._pos = _status.pos
                return _status
            elif _statusstatus == _status.ERROR:
                raise BacktrackException(_status.error)
            elif (_statusstatus == _status.INPROGRESS or
                  _statusstatus == _status.LEFTRECURSION):
                _status.status = _status.LEFTRECURSION
                if _status.result is not None:
                    self._pos = _status.pos
                    return _status
                else:
                    raise BacktrackException(None)
            elif _statusstatus == _status.SOMESOLUTIONS:
                _status.status = _status.INPROGRESS
        _startingpos = self._pos
        try:
            _result = None
            _error = None
            while 1:
                _choice0 = self._pos
                try:
                    _call_status = self._concatenation()
                    _result = _call_status.result
                    _error = _call_status.error
                    r1 = _result
                    _result = self.__chars__('|')
                    _call_status = self._regex()
                    _result = _call_status.result
                    _error = self._combine_errors(_error, _call_status.error)
                    r2 = _result
                    _result = (r1 | r2)
                    break
                except BacktrackException, _exc:
                    _error = self._combine_errors(_error, _exc.error)
                    self._pos = _choice0
                _choice1 = self._pos
                try:
                    _call_status = self._concatenation()
                    _result = _call_status.result
                    _error = self._combine_errors(_error, _call_status.error)
                    break
                except BacktrackException, _exc:
                    _error = self._combine_errors(_error, _exc.error)
                    self._pos = _choice1
                    raise BacktrackException(_error)
                _call_status = self._concatenation()
                _result = _call_status.result
                _error = self._combine_errors(_error, _call_status.error)
                break
            if _status.status == _status.LEFTRECURSION:
                if _status.result is not None:
                    if _status.pos >= self._pos:
                        _status.status = _status.NORMAL
                        self._pos = _status.pos
                        return _status
                _status.pos = self._pos
                _status.status = _status.SOMESOLUTIONS
                _status.result = _result
                _status.error = _error
                self._pos = _startingpos
                return self._regex()
            _status.status = _status.NORMAL
            _status.pos = self._pos
            _status.result = _result
            _status.error = _error
            return _status
        except BacktrackException, _exc:
            _status.pos = -1
            _status.result = None
            _error = self._combine_errors(_error, _exc.error)
            _status.error = _error
            _status.status = _status.ERROR
            raise BacktrackException(_error)
    def concatenation(self):
        return self._concatenation().result
    def _concatenation(self):
        _key = self._pos
        _status = self._dict_concatenation.get(_key, None)
        if _status is None:
            _status = self._dict_concatenation[_key] = Status()
        else:
            _statusstatus = _status.status
            if _statusstatus == _status.NORMAL:
                self._pos = _status.pos
                return _status
            elif _statusstatus == _status.ERROR:
                raise BacktrackException(_status.error)
            elif (_statusstatus == _status.INPROGRESS or
                  _statusstatus == _status.LEFTRECURSION):
                _status.status = _status.LEFTRECURSION
                if _status.result is not None:
                    self._pos = _status.pos
                    return _status
                else:
                    raise BacktrackException(None)
            elif _statusstatus == _status.SOMESOLUTIONS:
                _status.status = _status.INPROGRESS
        _startingpos = self._pos
        try:
            _result = None
            _error = None
            _all0 = []
            _call_status = self._repetition()
            _result = _call_status.result
            _error = _call_status.error
            _all0.append(_result)
            while 1:
                _choice1 = self._pos
                try:
                    _call_status = self._repetition()
                    _result = _call_status.result
                    _error = self._combine_errors(_error, _call_status.error)
                    _all0.append(_result)
                except BacktrackException, _exc:
                    _error = self._combine_errors(_error, _exc.error)
                    self._pos = _choice1
                    break
            _result = _all0
            l = _result
            _result = (reduce(operator.add, l, regex.StringExpression("")))
            if _status.status == _status.LEFTRECURSION:
                if _status.result is not None:
                    if _status.pos >= self._pos:
                        _status.status = _status.NORMAL
                        self._pos = _status.pos
                        return _status
                _status.pos = self._pos
                _status.status = _status.SOMESOLUTIONS
                _status.result = _result
                _status.error = _error
                self._pos = _startingpos
                return self._concatenation()
            _status.status = _status.NORMAL
            _status.pos = self._pos
            _status.result = _result
            _status.error = _error
            return _status
        except BacktrackException, _exc:
            _status.pos = -1
            _status.result = None
            _error = self._combine_errors(_error, _exc.error)
            _status.error = _error
            _status.status = _status.ERROR
            raise BacktrackException(_error)
    def repetition(self):
        return self._repetition().result
    def _repetition(self):
        _key = self._pos
        _status = self._dict_repetition.get(_key, None)
        if _status is None:
            _status = self._dict_repetition[_key] = Status()
        else:
            _statusstatus = _status.status
            if _statusstatus == _status.NORMAL:
                self._pos = _status.pos
                return _status
            elif _statusstatus == _status.ERROR:
                raise BacktrackException(_status.error)
            elif (_statusstatus == _status.INPROGRESS or
                  _statusstatus == _status.LEFTRECURSION):
                _status.status = _status.LEFTRECURSION
                if _status.result is not None:
                    self._pos = _status.pos
                    return _status
                else:
                    raise BacktrackException(None)
            elif _statusstatus == _status.SOMESOLUTIONS:
                _status.status = _status.INPROGRESS
        _startingpos = self._pos
        try:
            _result = None
            _error = None
            while 1:
                _choice0 = self._pos
                try:
                    _call_status = self._primary()
                    _result = _call_status.result
                    _error = _call_status.error
                    r1 = _result
                    _result = self.__chars__('*')
                    _result = (r1.kleene())
                    break
                except BacktrackException, _exc:
                    _error = self._combine_errors(_error, _exc.error)
                    self._pos = _choice0
                _choice1 = self._pos
                try:
                    _call_status = self._primary()
                    _result = _call_status.result
                    _error = self._combine_errors(_error, _call_status.error)
                    r1 = _result
                    _result = self.__chars__('+')
                    _result = (r1 + r1.kleene())
                    break
                except BacktrackException, _exc:
                    _error = self._combine_errors(_error, _exc.error)
                    self._pos = _choice1
                _choice2 = self._pos
                try:
                    _call_status = self._primary()
                    _result = _call_status.result
                    _error = self._combine_errors(_error, _call_status.error)
                    r1 = _result
                    _result = self.__chars__('?')
                    _result = (regex.StringExpression("") | r1)
                    break
                except BacktrackException, _exc:
                    _error = self._combine_errors(_error, _exc.error)
                    self._pos = _choice2
                _choice3 = self._pos
                try:
                    _call_status = self._primary()
                    _result = _call_status.result
                    _error = self._combine_errors(_error, _call_status.error)
                    r = _result
                    _result = self.__chars__('{')
                    _call_status = self._numrange()
                    _result = _call_status.result
                    _error = self._combine_errors(_error, _call_status.error)
                    n = _result
                    _result = self.__chars__('}')
                    _result = (r * n[0] + reduce(operator.or_, [r * i for i in range(n[1] - n[0] + 1)], regex.StringExpression("")))
                    break
                except BacktrackException, _exc:
                    _error = self._combine_errors(_error, _exc.error)
                    self._pos = _choice3
                _choice4 = self._pos
                try:
                    _call_status = self._primary()
                    _result = _call_status.result
                    _error = self._combine_errors(_error, _call_status.error)
                    break
                except BacktrackException, _exc:
                    _error = self._combine_errors(_error, _exc.error)
                    self._pos = _choice4
                    raise BacktrackException(_error)
                _call_status = self._primary()
                _result = _call_status.result
                _error = self._combine_errors(_error, _call_status.error)
                break
            if _status.status == _status.LEFTRECURSION:
                if _status.result is not None:
                    if _status.pos >= self._pos:
                        _status.status = _status.NORMAL
                        self._pos = _status.pos
                        return _status
                _status.pos = self._pos
                _status.status = _status.SOMESOLUTIONS
                _status.result = _result
                _status.error = _error
                self._pos = _startingpos
                return self._repetition()
            _status.status = _status.NORMAL
            _status.pos = self._pos
            _status.result = _result
            _status.error = _error
            return _status
        except BacktrackException, _exc:
            _status.pos = -1
            _status.result = None
            _error = self._combine_errors(_error, _exc.error)
            _status.error = _error
            _status.status = _status.ERROR
            raise BacktrackException(_error)
    def primary(self):
        return self._primary().result
    def _primary(self):
        _key = self._pos
        _status = self._dict_primary.get(_key, None)
        if _status is None:
            _status = self._dict_primary[_key] = Status()
        else:
            _statusstatus = _status.status
            if _statusstatus == _status.NORMAL:
                self._pos = _status.pos
                return _status
            elif _statusstatus == _status.ERROR:
                raise BacktrackException(_status.error)
            elif (_statusstatus == _status.INPROGRESS or
                  _statusstatus == _status.LEFTRECURSION):
                _status.status = _status.LEFTRECURSION
                if _status.result is not None:
                    self._pos = _status.pos
                    return _status
                else:
                    raise BacktrackException(None)
            elif _statusstatus == _status.SOMESOLUTIONS:
                _status.status = _status.INPROGRESS
        _startingpos = self._pos
        try:
            _result = None
            _error = None
            while 1:
                _choice0 = self._pos
                try:
                    _before_discard1 = _result
                    _result = self.__chars__('(')
                    _result = _before_discard1
                    _call_status = self._regex()
                    _result = _call_status.result
                    _error = _call_status.error
                    _before_discard2 = _result
                    _result = self.__chars__(')')
                    _result = _before_discard2
                    break
                except BacktrackException, _exc:
                    _error = self._combine_errors(_error, _exc.error)
                    self._pos = _choice0
                _choice3 = self._pos
                try:
                    _call_status = self._range()
                    _result = _call_status.result
                    _error = self._combine_errors(_error, _call_status.error)
                    break
                except BacktrackException, _exc:
                    _error = self._combine_errors(_error, _exc.error)
                    self._pos = _choice3
                _choice4 = self._pos
                try:
                    _call_status = self._char()
                    _result = _call_status.result
                    _error = self._combine_errors(_error, _call_status.error)
                    c = _result
                    _result = (regex.StringExpression(c))
                    break
                except BacktrackException, _exc:
                    _error = self._combine_errors(_error, _exc.error)
                    self._pos = _choice4
                _choice5 = self._pos
                try:
                    _result = self.__chars__('.')
                    _result = (regex.RangeExpression(chr(0), chr(255)))
                    break
                except BacktrackException, _exc:
                    _error = self._combine_errors(_error, _exc.error)
                    self._pos = _choice5
                    raise BacktrackException(_error)
                _result = self.__chars__('.')
                _result = (regex.RangeExpression(chr(0), chr(255)))
                break
            if _status.status == _status.LEFTRECURSION:
                if _status.result is not None:
                    if _status.pos >= self._pos:
                        _status.status = _status.NORMAL
                        self._pos = _status.pos
                        return _status
                _status.pos = self._pos
                _status.status = _status.SOMESOLUTIONS
                _status.result = _result
                _status.error = _error
                self._pos = _startingpos
                return self._primary()
            _status.status = _status.NORMAL
            _status.pos = self._pos
            _status.result = _result
            _status.error = _error
            return _status
        except BacktrackException, _exc:
            _status.pos = -1
            _status.result = None
            _error = self._combine_errors(_error, _exc.error)
            _status.error = _error
            _status.status = _status.ERROR
            raise BacktrackException(_error)
    def char(self):
        return self._char().result
    def _char(self):
        _key = self._pos
        _status = self._dict_char.get(_key, None)
        if _status is None:
            _status = self._dict_char[_key] = Status()
        else:
            _statusstatus = _status.status
            if _statusstatus == _status.NORMAL:
                self._pos = _status.pos
                return _status
            elif _statusstatus == _status.ERROR:
                raise BacktrackException(_status.error)
            elif (_statusstatus == _status.INPROGRESS or
                  _statusstatus == _status.LEFTRECURSION):
                _status.status = _status.LEFTRECURSION
                if _status.result is not None:
                    self._pos = _status.pos
                    return _status
                else:
                    raise BacktrackException(None)
            elif _statusstatus == _status.SOMESOLUTIONS:
                _status.status = _status.INPROGRESS
        _startingpos = self._pos
        try:
            _result = None
            _error = None
            while 1:
                _choice0 = self._pos
                try:
                    _call_status = self._QUOTEDCHAR()
                    _result = _call_status.result
                    _error = _call_status.error
                    c = _result
                    _result = (unescape(c))
                    break
                except BacktrackException, _exc:
                    _error = self._combine_errors(_error, _exc.error)
                    self._pos = _choice0
                _choice1 = self._pos
                try:
                    _call_status = self._CHAR()
                    _result = _call_status.result
                    _error = self._combine_errors(_error, _call_status.error)
                    c = _result
                    _result = (c)
                    break
                except BacktrackException, _exc:
                    _error = self._combine_errors(_error, _exc.error)
                    self._pos = _choice1
                    raise BacktrackException(_error)
                _call_status = self._CHAR()
                _result = _call_status.result
                _error = self._combine_errors(_error, _call_status.error)
                c = _result
                _result = (c)
                break
            if _status.status == _status.LEFTRECURSION:
                if _status.result is not None:
                    if _status.pos >= self._pos:
                        _status.status = _status.NORMAL
                        self._pos = _status.pos
                        return _status
                _status.pos = self._pos
                _status.status = _status.SOMESOLUTIONS
                _status.result = _result
                _status.error = _error
                self._pos = _startingpos
                return self._char()
            _status.status = _status.NORMAL
            _status.pos = self._pos
            _status.result = _result
            _status.error = _error
            return _status
        except BacktrackException, _exc:
            _status.pos = -1
            _status.result = None
            _error = self._combine_errors(_error, _exc.error)
            _status.error = _error
            _status.status = _status.ERROR
            raise BacktrackException(_error)
    def QUOTEDCHAR(self):
        return self._QUOTEDCHAR().result
    def _QUOTEDCHAR(self):
        _key = self._pos
        _status = self._dict_QUOTEDCHAR.get(_key, None)
        if _status is None:
            _status = self._dict_QUOTEDCHAR[_key] = Status()
        else:
            _statusstatus = _status.status
            if _statusstatus == _status.NORMAL:
                self._pos = _status.pos
                return _status
            elif _statusstatus == _status.ERROR:
                raise BacktrackException(_status.error)
        _startingpos = self._pos
        try:
            _result = None
            _error = None
            _result = self._regex1380912319()
            assert _status.status != _status.LEFTRECURSION
            _status.status = _status.NORMAL
            _status.pos = self._pos
            _status.result = _result
            _status.error = _error
            return _status
        except BacktrackException, _exc:
            _status.pos = -1
            _status.result = None
            _error = _exc.error
            _status.error = _error
            _status.status = _status.ERROR
            raise BacktrackException(_error)
    def CHAR(self):
        return self._CHAR().result
    def _CHAR(self):
        _key = self._pos
        _status = self._dict_CHAR.get(_key, None)
        if _status is None:
            _status = self._dict_CHAR[_key] = Status()
        else:
            _statusstatus = _status.status
            if _statusstatus == _status.NORMAL:
                self._pos = _status.pos
                return _status
            elif _statusstatus == _status.ERROR:
                raise BacktrackException(_status.error)
        _startingpos = self._pos
        try:
            _result = None
            _error = None
            _result = self._regex1323868075()
            assert _status.status != _status.LEFTRECURSION
            _status.status = _status.NORMAL
            _status.pos = self._pos
            _status.result = _result
            _status.error = _error
            return _status
        except BacktrackException, _exc:
            _status.pos = -1
            _status.result = None
            _error = _exc.error
            _status.error = _error
            _status.status = _status.ERROR
            raise BacktrackException(_error)
    def range(self):
        return self._range().result
    def _range(self):
        _key = self._pos
        _status = self._dict_range.get(_key, None)
        if _status is None:
            _status = self._dict_range[_key] = Status()
        else:
            _statusstatus = _status.status
            if _statusstatus == _status.NORMAL:
                self._pos = _status.pos
                return _status
            elif _statusstatus == _status.ERROR:
                raise BacktrackException(_status.error)
            elif (_statusstatus == _status.INPROGRESS or
                  _statusstatus == _status.LEFTRECURSION):
                _status.status = _status.LEFTRECURSION
                if _status.result is not None:
                    self._pos = _status.pos
                    return _status
                else:
                    raise BacktrackException(None)
            elif _statusstatus == _status.SOMESOLUTIONS:
                _status.status = _status.INPROGRESS
        _startingpos = self._pos
        try:
            _result = None
            _error = None
            _result = self.__chars__('[')
            _call_status = self._rangeinner()
            _result = _call_status.result
            _error = _call_status.error
            s = _result
            _result = self.__chars__(']')
            _result = (reduce(operator.or_, [regex.RangeExpression(a, chr(ord(a) + b - 1)) for a, b in compress_char_set(s)]))
            if _status.status == _status.LEFTRECURSION:
                if _status.result is not None:
                    if _status.pos >= self._pos:
                        _status.status = _status.NORMAL
                        self._pos = _status.pos
                        return _status
                _status.pos = self._pos
                _status.status = _status.SOMESOLUTIONS
                _status.result = _result
                _status.error = _error
                self._pos = _startingpos
                return self._range()
            _status.status = _status.NORMAL
            _status.pos = self._pos
            _status.result = _result
            _status.error = _error
            return _status
        except BacktrackException, _exc:
            _status.pos = -1
            _status.result = None
            _error = self._combine_errors(_error, _exc.error)
            _status.error = _error
            _status.status = _status.ERROR
            raise BacktrackException(_error)
    def rangeinner(self):
        return self._rangeinner().result
    def _rangeinner(self):
        _key = self._pos
        _status = self._dict_rangeinner.get(_key, None)
        if _status is None:
            _status = self._dict_rangeinner[_key] = Status()
        else:
            _statusstatus = _status.status
            if _statusstatus == _status.NORMAL:
                self._pos = _status.pos
                return _status
            elif _statusstatus == _status.ERROR:
                raise BacktrackException(_status.error)
            elif (_statusstatus == _status.INPROGRESS or
                  _statusstatus == _status.LEFTRECURSION):
                _status.status = _status.LEFTRECURSION
                if _status.result is not None:
                    self._pos = _status.pos
                    return _status
                else:
                    raise BacktrackException(None)
            elif _statusstatus == _status.SOMESOLUTIONS:
                _status.status = _status.INPROGRESS
        _startingpos = self._pos
        try:
            _result = None
            _error = None
            while 1:
                _choice0 = self._pos
                try:
                    _result = self.__chars__('^')
                    _call_status = self._subrange()
                    _result = _call_status.result
                    _error = _call_status.error
                    s = _result
                    _result = (set([chr(c) for c in range(256)]) - s)
                    break
                except BacktrackException, _exc:
                    _error = self._combine_errors(_error, _exc.error)
                    self._pos = _choice0
                _choice1 = self._pos
                try:
                    _call_status = self._subrange()
                    _result = _call_status.result
                    _error = self._combine_errors(_error, _call_status.error)
                    break
                except BacktrackException, _exc:
                    _error = self._combine_errors(_error, _exc.error)
                    self._pos = _choice1
                    raise BacktrackException(_error)
                _call_status = self._subrange()
                _result = _call_status.result
                _error = self._combine_errors(_error, _call_status.error)
                break
            if _status.status == _status.LEFTRECURSION:
                if _status.result is not None:
                    if _status.pos >= self._pos:
                        _status.status = _status.NORMAL
                        self._pos = _status.pos
                        return _status
                _status.pos = self._pos
                _status.status = _status.SOMESOLUTIONS
                _status.result = _result
                _status.error = _error
                self._pos = _startingpos
                return self._rangeinner()
            _status.status = _status.NORMAL
            _status.pos = self._pos
            _status.result = _result
            _status.error = _error
            return _status
        except BacktrackException, _exc:
            _status.pos = -1
            _status.result = None
            _error = self._combine_errors(_error, _exc.error)
            _status.error = _error
            _status.status = _status.ERROR
            raise BacktrackException(_error)
    def subrange(self):
        return self._subrange().result
    def _subrange(self):
        _key = self._pos
        _status = self._dict_subrange.get(_key, None)
        if _status is None:
            _status = self._dict_subrange[_key] = Status()
        else:
            _statusstatus = _status.status
            if _statusstatus == _status.NORMAL:
                self._pos = _status.pos
                return _status
            elif _statusstatus == _status.ERROR:
                raise BacktrackException(_status.error)
            elif (_statusstatus == _status.INPROGRESS or
                  _statusstatus == _status.LEFTRECURSION):
                _status.status = _status.LEFTRECURSION
                if _status.result is not None:
                    self._pos = _status.pos
                    return _status
                else:
                    raise BacktrackException(None)
            elif _statusstatus == _status.SOMESOLUTIONS:
                _status.status = _status.INPROGRESS
        _startingpos = self._pos
        try:
            _result = None
            _error = None
            _all0 = []
            _call_status = self._rangeelement()
            _result = _call_status.result
            _error = _call_status.error
            _all0.append(_result)
            while 1:
                _choice1 = self._pos
                try:
                    _call_status = self._rangeelement()
                    _result = _call_status.result
                    _error = self._combine_errors(_error, _call_status.error)
                    _all0.append(_result)
                except BacktrackException, _exc:
                    _error = self._combine_errors(_error, _exc.error)
                    self._pos = _choice1
                    break
            _result = _all0
            l = _result
            _result = (reduce(operator.or_, l))
            if _status.status == _status.LEFTRECURSION:
                if _status.result is not None:
                    if _status.pos >= self._pos:
                        _status.status = _status.NORMAL
                        self._pos = _status.pos
                        return _status
                _status.pos = self._pos
                _status.status = _status.SOMESOLUTIONS
                _status.result = _result
                _status.error = _error
                self._pos = _startingpos
                return self._subrange()
            _status.status = _status.NORMAL
            _status.pos = self._pos
            _status.result = _result
            _status.error = _error
            return _status
        except BacktrackException, _exc:
            _status.pos = -1
            _status.result = None
            _error = self._combine_errors(_error, _exc.error)
            _status.error = _error
            _status.status = _status.ERROR
            raise BacktrackException(_error)
    def rangeelement(self):
        return self._rangeelement().result
    def _rangeelement(self):
        _key = self._pos
        _status = self._dict_rangeelement.get(_key, None)
        if _status is None:
            _status = self._dict_rangeelement[_key] = Status()
        else:
            _statusstatus = _status.status
            if _statusstatus == _status.NORMAL:
                self._pos = _status.pos
                return _status
            elif _statusstatus == _status.ERROR:
                raise BacktrackException(_status.error)
            elif (_statusstatus == _status.INPROGRESS or
                  _statusstatus == _status.LEFTRECURSION):
                _status.status = _status.LEFTRECURSION
                if _status.result is not None:
                    self._pos = _status.pos
                    return _status
                else:
                    raise BacktrackException(None)
            elif _statusstatus == _status.SOMESOLUTIONS:
                _status.status = _status.INPROGRESS
        _startingpos = self._pos
        try:
            _result = None
            _error = None
            while 1:
                _choice0 = self._pos
                try:
                    _call_status = self._char()
                    _result = _call_status.result
                    _error = _call_status.error
                    c1 = _result
                    _result = self.__chars__('-')
                    _call_status = self._char()
                    _result = _call_status.result
                    _error = self._combine_errors(_error, _call_status.error)
                    c2 = _result
                    _result = (set([chr(i) for i in range(ord(c1), ord(c2) + 1)]))
                    break
                except BacktrackException, _exc:
                    _error = self._combine_errors(_error, _exc.error)
                    self._pos = _choice0
                _choice1 = self._pos
                try:
                    _call_status = self._char()
                    _result = _call_status.result
                    _error = self._combine_errors(_error, _call_status.error)
                    c = _result
                    _result = (set([c]))
                    break
                except BacktrackException, _exc:
                    _error = self._combine_errors(_error, _exc.error)
                    self._pos = _choice1
                    raise BacktrackException(_error)
                _call_status = self._char()
                _result = _call_status.result
                _error = self._combine_errors(_error, _call_status.error)
                c = _result
                _result = (set([c]))
                break
            if _status.status == _status.LEFTRECURSION:
                if _status.result is not None:
                    if _status.pos >= self._pos:
                        _status.status = _status.NORMAL
                        self._pos = _status.pos
                        return _status
                _status.pos = self._pos
                _status.status = _status.SOMESOLUTIONS
                _status.result = _result
                _status.error = _error
                self._pos = _startingpos
                return self._rangeelement()
            _status.status = _status.NORMAL
            _status.pos = self._pos
            _status.result = _result
            _status.error = _error
            return _status
        except BacktrackException, _exc:
            _status.pos = -1
            _status.result = None
            _error = self._combine_errors(_error, _exc.error)
            _status.error = _error
            _status.status = _status.ERROR
            raise BacktrackException(_error)
    def numrange(self):
        return self._numrange().result
    def _numrange(self):
        _key = self._pos
        _status = self._dict_numrange.get(_key, None)
        if _status is None:
            _status = self._dict_numrange[_key] = Status()
        else:
            _statusstatus = _status.status
            if _statusstatus == _status.NORMAL:
                self._pos = _status.pos
                return _status
            elif _statusstatus == _status.ERROR:
                raise BacktrackException(_status.error)
            elif (_statusstatus == _status.INPROGRESS or
                  _statusstatus == _status.LEFTRECURSION):
                _status.status = _status.LEFTRECURSION
                if _status.result is not None:
                    self._pos = _status.pos
                    return _status
                else:
                    raise BacktrackException(None)
            elif _statusstatus == _status.SOMESOLUTIONS:
                _status.status = _status.INPROGRESS
        _startingpos = self._pos
        try:
            _result = None
            _error = None
            while 1:
                _choice0 = self._pos
                try:
                    _call_status = self._NUM()
                    _result = _call_status.result
                    _error = _call_status.error
                    n1 = _result
                    _result = self.__chars__(',')
                    _call_status = self._NUM()
                    _result = _call_status.result
                    _error = self._combine_errors(_error, _call_status.error)
                    n2 = _result
                    _result = (n1, n2)
                    break
                except BacktrackException, _exc:
                    _error = self._combine_errors(_error, _exc.error)
                    self._pos = _choice0
                _choice1 = self._pos
                try:
                    _call_status = self._NUM()
                    _result = _call_status.result
                    _error = self._combine_errors(_error, _call_status.error)
                    n1 = _result
                    _result = (n1, n1)
                    break
                except BacktrackException, _exc:
                    _error = self._combine_errors(_error, _exc.error)
                    self._pos = _choice1
                    raise BacktrackException(_error)
                _call_status = self._NUM()
                _result = _call_status.result
                _error = self._combine_errors(_error, _call_status.error)
                n1 = _result
                _result = (n1, n1)
                break
            if _status.status == _status.LEFTRECURSION:
                if _status.result is not None:
                    if _status.pos >= self._pos:
                        _status.status = _status.NORMAL
                        self._pos = _status.pos
                        return _status
                _status.pos = self._pos
                _status.status = _status.SOMESOLUTIONS
                _status.result = _result
                _status.error = _error
                self._pos = _startingpos
                return self._numrange()
            _status.status = _status.NORMAL
            _status.pos = self._pos
            _status.result = _result
            _status.error = _error
            return _status
        except BacktrackException, _exc:
            _status.pos = -1
            _status.result = None
            _error = self._combine_errors(_error, _exc.error)
            _status.error = _error
            _status.status = _status.ERROR
            raise BacktrackException(_error)
    def NUM(self):
        return self._NUM().result
    def _NUM(self):
        _key = self._pos
        _status = self._dict_NUM.get(_key, None)
        if _status is None:
            _status = self._dict_NUM[_key] = Status()
        else:
            _statusstatus = _status.status
            if _statusstatus == _status.NORMAL:
                self._pos = _status.pos
                return _status
            elif _statusstatus == _status.ERROR:
                raise BacktrackException(_status.error)
        _startingpos = self._pos
        try:
            _result = None
            _error = None
            _result = self._regex1166214427()
            c = _result
            _result = (int(c))
            assert _status.status != _status.LEFTRECURSION
            _status.status = _status.NORMAL
            _status.pos = self._pos
            _status.result = _result
            _status.error = _error
            return _status
        except BacktrackException, _exc:
            _status.pos = -1
            _status.result = None
            _error = _exc.error
            _status.error = _error
            _status.status = _status.ERROR
            raise BacktrackException(_error)
    def __init__(self, inputstream):
        self._dict_EOF = {}
        self._dict_parse = {}
        self._dict_regex = {}
        self._dict_concatenation = {}
        self._dict_repetition = {}
        self._dict_primary = {}
        self._dict_char = {}
        self._dict_QUOTEDCHAR = {}
        self._dict_CHAR = {}
        self._dict_range = {}
        self._dict_rangeinner = {}
        self._dict_subrange = {}
        self._dict_rangeelement = {}
        self._dict_numrange = {}
        self._dict_NUM = {}
        self._pos = 0
        self._inputstream = inputstream
    def _regex1166214427(self):
        _choice0 = self._pos
        _runner = self._Runner(self._inputstream, self._pos)
        _i = _runner.recognize_1166214427(self._pos)
        if _runner.last_matched_state == -1:
            self._pos = _choice0
            raise BacktrackException
        _upto = _runner.last_matched_index + 1
        _result = self._inputstream[self._pos: _upto]
        self._pos = _upto
        return _result
    def _regex1323868075(self):
        _choice1 = self._pos
        _runner = self._Runner(self._inputstream, self._pos)
        _i = _runner.recognize_1323868075(self._pos)
        if _runner.last_matched_state == -1:
            self._pos = _choice1
            raise BacktrackException
        _upto = _runner.last_matched_index + 1
        _result = self._inputstream[self._pos: _upto]
        self._pos = _upto
        return _result
    def _regex1380912319(self):
        _choice2 = self._pos
        _runner = self._Runner(self._inputstream, self._pos)
        _i = _runner.recognize_1380912319(self._pos)
        if _runner.last_matched_state == -1:
            self._pos = _choice2
            raise BacktrackException
        _upto = _runner.last_matched_index + 1
        _result = self._inputstream[self._pos: _upto]
        self._pos = _upto
        return _result
    class _Runner(object):
        def __init__(self, text, pos):
            self.text = text
            self.pos = pos
            self.last_matched_state = -1
            self.last_matched_index = -1
            self.state = -1
        def recognize_1166214427(runner, i):
            assert i >= 0
            input = runner.text
            state = 0
            while 1:
                if state == 0:
                    if i < len(input):
                        char = input[i]
                        i += 1
                    else:
                        runner.state = 0
                        return ~i
                    if '1' <= char <= '9':
                        state = 1
                    elif char == '0':
                        state = 2
                    else:
                        break
                if state == 1:
                    runner.last_matched_index = i - 1
                    runner.last_matched_state = state
                    if i < len(input):
                        char = input[i]
                        i += 1
                    else:
                        runner.state = 1
                        return i
                    if '0' <= char <= '9':
                        state = 1
                        continue
                    else:
                        break
                runner.last_matched_state = state
                runner.last_matched_index = i - 1
                runner.state = state
                if i == len(input):
                    return i
                else:
                    return ~i
                break
            runner.state = state
            return ~i
        def recognize_1323868075(runner, i):
            assert i >= 0
            input = runner.text
            state = 0
            while 1:
                if state == 0:
                    if i < len(input):
                        char = input[i]
                        i += 1
                    else:
                        runner.state = 0
                        return ~i
                    if '\x00' <= char <= "'":
                        state = 1
                    elif '/' <= char <= '>':
                        state = 1
                    elif '@' <= char <= 'Z':
                        state = 1
                    elif char == '\\':
                        state = 1
                    elif '_' <= char <= 'z':
                        state = 1
                    elif '~' <= char <= '\xff':
                        state = 1
                    else:
                        break
                runner.last_matched_state = state
                runner.last_matched_index = i - 1
                runner.state = state
                if i == len(input):
                    return i
                else:
                    return ~i
                break
            runner.state = state
            return ~i
        def recognize_1380912319(runner, i):
            assert i >= 0
            input = runner.text
            state = 0
            while 1:
                if state == 0:
                    if i < len(input):
                        char = input[i]
                        i += 1
                    else:
                        runner.state = 0
                        return ~i
                    if char == '\\':
                        state = 1
                    else:
                        break
                if state == 1:
                    if i < len(input):
                        char = input[i]
                        i += 1
                    else:
                        runner.state = 1
                        return ~i
                    if char == 'x':
                        state = 2
                    elif '\x00' <= char <= 'w':
                        state = 3
                    elif 'y' <= char <= '\xff':
                        state = 3
                    else:
                        break
                if state == 2:
                    runner.last_matched_index = i - 1
                    runner.last_matched_state = state
                    if i < len(input):
                        char = input[i]
                        i += 1
                    else:
                        runner.state = 2
                        return i
                    if '0' <= char <= '9':
                        state = 4
                    elif 'A' <= char <= 'F':
                        state = 4
                    elif 'a' <= char <= 'f':
                        state = 4
                    else:
                        break
                if state == 4:
                    if i < len(input):
                        char = input[i]
                        i += 1
                    else:
                        runner.state = 4
                        return ~i
                    if '0' <= char <= '9':
                        state = 3
                    elif 'A' <= char <= 'F':
                        state = 3
                    elif 'a' <= char <= 'f':
                        state = 3
                    else:
                        break
                runner.last_matched_state = state
                runner.last_matched_index = i - 1
                runner.state = state
                if i == len(input):
                    return i
                else:
                    return ~i
                break
            runner.state = state
            return ~i
class RegexParser(PackratParser):
    def __init__(self, stream):
        self.init_parser(stream)
forbidden = dict.fromkeys(("__weakref__ __doc__ "
                           "__dict__ __module__").split())
initthere = "__init__" in RegexParser.__dict__
for key, value in Parser.__dict__.iteritems():
    if key not in RegexParser.__dict__ and key not in forbidden:
        setattr(RegexParser, key, value)
RegexParser.init_parser = Parser.__init__.im_func
# generated code between this line and its other occurence



















def test_generate():
    f = py.magic.autopath()
    oldcontent = f.read()
    s = "# GENERATED CODE BETWEEN THIS LINE AND ITS OTHER OCCURENCE\n".lower()
    pre, gen, after = oldcontent.split(s)

    from pypackrat import PyPackratSyntaxParser
    from makepackrat import TreeOptimizer, ParserBuilder
    p = PyPackratSyntaxParser(syntax)
    t = p.file()
    t = t.visit(TreeOptimizer())
    visitor = ParserBuilder()
    t.visit(visitor)
    code = visitor.get_code()
    content = """\
%s\
%s
from pypy.rlib.parsing.pypackrat import PackratParser, Status
from pypy.rlib.parsing.pypackrat import BacktrackException
from pypy.rlib.parsing import regex
import operator
%s
class RegexParser(PackratParser):
    def __init__(self, stream):
        self.init_parser(stream)
forbidden = dict.fromkeys(("__weakref__ __doc__ "
                           "__dict__ __module__").split())
initthere = "__init__" in RegexParser.__dict__
for key, value in Parser.__dict__.iteritems():
    if key not in RegexParser.__dict__ and key not in forbidden:
        setattr(RegexParser, key, value)
RegexParser.init_parser = Parser.__init__.im_func
%s
%s\
""" % (pre, s, code, s, after)
    print content
    f.write(content)
