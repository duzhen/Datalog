import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ply.lex as lex

reserved = {'not' : 'NOT'}

tokens = [
    'TURNSTILE',    #:-
    'DOT',          #.
    'LEFT_PAR',     #(
    'RIGHT_PAR',    #)
    'COMMA',        #,
    #'NUMBER',       #0-9
    'CONSTANT',      #something
    'VARIABLE',     #X
    #'UNDERSCORE',   #_
    'OPERATOR',     #>
    'QUERY',        #?
] + list(reserved.values())

# Ignore spaces and tabs
t_ignore = ' \t'

# Tokens' regular expressions
t_TURNSTILE = r'\:\-'
t_DOT = r'\.'
t_LEFT_PAR = r'\('
t_RIGHT_PAR = r'\)'
t_COMMA = r'\,'
t_VARIABLE = r'[A-Z][A-Za-z0-9_]*'
# t_CONSTANT = r'[a-z0-9][a-zA-Z0-9_.]*'
# t_UNDERSCORE = r'_'
t_OPERATOR = r'[!<>=](=)?'
t_QUERY = r'\?'

def t_CONSTANT(t):
    r'[a-z0-9_][a-zA-Z_0-9]*'
    # Check for reserved words
    t.type = reserved.get(t.value, 'CONSTANT')
    return t

# t_NUMBER = r'\d+'
#
# def t_AND(t):
#     r'[a-z][a-z]*'
#     t.type = reserved.get(t.value, 'CONSTANT')  # Check for reserved words
#     return t
#
# def t_NOT(t):
#     r'not'
#     # r'[a-z][a-z]*'
#     t.type = reserved.get(t.value, 'CONSTANT')  # Check for reserved words
#     return t

def t_comment(t):
    r"[ ]*\%[^\n]*"  #
    pass

# Keep track of line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

lexer = lex.lex(debug=False)

if __name__ == '__main__':
    data = """e(a, b).
            e(b, c).
            path(X, Y) :- edge(X, Y).
            path(X, Y) :- path(X, Z), path(Z, Y).

            path(a, e)?
            """
    
    lexer = lex.lex()
    lexer.input(data)

    # Tokenize
    while True:
        tok = lexer.token()
        if not tok: break      # No more input
        print(tok)

