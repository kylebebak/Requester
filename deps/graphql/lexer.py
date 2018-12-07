from __future__ import unicode_literals
from decimal import Decimal

import ply.lex as lex
from ply.lex import TOKEN

from .exceptions import LexerError


class GraphQLLexer(object):
    """
    GraphQL lexer with PLY-compatible interface for usage with PLY-yacc.

    Usage example:

        lexer = GraphQLLexer()
        lexer.input(some_text)
        for token in lexer:
            print token.type, token.value

    To use it with yacc, pass instance of GraphQLLexer to yacc.parse() method:

        lexer = GraphQLLexer()
        yacc.parse(input=some_text, lexer=lexer)

    """
    def __init__(self, **kwargs):
        self._lexer = lex.lex(module=self, **kwargs)
        self.reset()

    def reset(self):
        self.text = ''
        self._lexer.lineno = 1
        return self

    def input(self, s):
        self.reset()
        self.text = s
        self._lexer.input(s)
        return self

    def token(self):
        return self._lexer.token()

    # Iterator interface
    def __iter__(self):
        return self

    def next(self):
        t = self.token()
        if t is None:
            raise StopIteration
        return t

    __next__ = next

    def find_column(self, t):
        """
        Returns token position in current text, starting from 1
        """
        cr = max(self.text.rfind(l, 0, t.lexpos) for l in self.line_terminators)
        if cr == -1:
            return t.lexpos + 1
        return t.lexpos - cr

    whitespace = ' \t\v\f\u00A0'
    line_terminators = '\n\r\u2028\u2029'
    comma = ','

    re_line_terminators = r'\n\r\u2028\u2029'

    re_escaped_char = r'\\[\"\\/bfnrt]'
    re_escaped_unicode = r'\\u[0-9A-Fa-f]{4}'
    re_string_char = r'[^\"\\' + re_line_terminators + u']'

    re_int_value = r'(-?0|-?[1-9][0-9]*)'
    re_fraction_part = r'\.[0-9]+'
    re_exponent_part = r'[eE][\+-]?[0-9]+'

    tokens = [
        'NAME',
        'FRAGMENT',
        'QUERY',
        'MUTATION',
        'ON',
        'TRUE',
        'FALSE',
        'NULL',
        'STRING_VALUE',
        'FLOAT_VALUE',
        'INT_VALUE',
        'BANG',
        'DOLLAR',
        'PAREN_L',
        'PAREN_R',
        'COLON',
        'EQUALS',
        'AT',
        'BRACKET_L',
        'BRACKET_R',
        'BRACE_L',
        'BRACE_R',
        'SPREAD',
    ]

    t_BANG = '!'
    t_DOLLAR = r'\$'
    t_PAREN_L = r'\('
    t_PAREN_R = r'\)'
    t_COLON = ':'
    t_EQUALS = '='
    t_AT = '@'
    t_BRACKET_L = r'\['
    t_BRACKET_R = r'\]'
    t_BRACE_L = r'\{'
    t_BRACE_R = r'\}'
    t_SPREAD = r'\.\.\.'

    t_NAME = r'[_A-Za-z][_0-9A-Za-z]*'

    t_ignore = whitespace + comma

    @TOKEN(r'\#[^' + re_line_terminators + ']*')
    def t_COMMENT(self, t):
        return  # return nothing, ignore comments

    @TOKEN(r'\"(' + re_escaped_char +
           '|' + re_escaped_unicode +
           '|' + re_string_char + r')*\"')
    def t_STRING_VALUE(self, t):
        t.value = t.value[1:-1]  # cut leading and trailing quotes ""
        return t

    @TOKEN(re_int_value + re_fraction_part + re_exponent_part + '|' +
           re_int_value + re_fraction_part + '|' +
           re_int_value + re_exponent_part)
    def t_FLOAT_VALUE(self, t):
        t.value = Decimal(t.value)
        return t

    @TOKEN(re_int_value)
    def t_INT_VALUE(self, t):
        t.value = int(t.value)
        return t

    not_followed_by_name = '(?![_0-9A-Za-z])'

    @TOKEN('fragment' + not_followed_by_name)
    def t_FRAGMENT(self, t):
        return t

    @TOKEN('query' + not_followed_by_name)
    def t_QUERY(self, t):
        return t

    @TOKEN('mutation' + not_followed_by_name)
    def t_MUTATION(self, t):
        return t

    @TOKEN('on' + not_followed_by_name)
    def t_ON(self, t):
        return t

    @TOKEN('true' + not_followed_by_name)
    def t_TRUE(self, t):
        t.value = True
        return t

    @TOKEN('false' + not_followed_by_name)
    def t_FALSE(self, t):
        t.value = False
        return t

    @TOKEN('null' + not_followed_by_name)
    def t_NULL(self, t):
        t.value = None
        return t

    def t_error(self, t):
        raise LexerError(
            message='Illegal character %s' % repr(t.value[0]),
            value=t.value,
            line=t.lineno,
            column=self.find_column(t),
        )

    @TOKEN('[' + re_line_terminators + ']+')
    def t_newline(self, t):
        t.lexer.lineno += len(t.value)
        return
