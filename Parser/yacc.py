import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ply.yacc as yacc

from Parser.model import Fact, Rule, Query, Predicate, Constraint
from Parser.lex import tokens

### PARSER RULES ###
def p_program(p):
    '''program : facts rules queries
        | facts rules
        | facts queries
        | rules queries
        | facts
        | rules
        | queries'''
    # p[0] = p[1]
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = p[1] + p[2]
    elif len(p) == 4:
        p[0] = p[1] + p[2] + p[3]

def p_facts_list(p):
    '''facts : facts fact'''
    p[0] = p[1] + [p[2]]

def p_facts(p):
    '''facts :  fact'''
    p[0] = [p[1]]

def p_fact(p):
    '''fact : block DOT'''
    p[0] = Fact(p[1])
    # p[0] = p[1]

def p_rules_list(p):
    '''rules : rules rule'''
    p[0] = p[1] + [p[2]]

def p_rules(p):
    '''rules :  rule'''
    p[0] = [p[1]]

def p_rule(p):
    '''rule : head TURNSTILE body DOT'''
    p[0] = Rule(p[1], p[3], 'rule')

def p_queries_list(p):
    '''queries : queries query'''
    p[0] = p[1] + [p[2]]

def p_queries(p):
    '''queries :  query'''
    p[0] = [p[1]]

def p_query(p):
    '''query : blocklist QUERY'''
    p[0] = Query(p[1])  # Tree(p[1], {}, 'query')

def p_head(p):
    '''head : block'''
    p[0] = p[1]

def p_body(p):
    '''body : blocklist'''
    p[0] = p[1]

def p_blocklist1(p):
    '''blocklist : blocklist COMMA block'''
    p[0] = p[1] + [p[3]]

def p_blocklist2(p):
    '''blocklist : blocklist COMMA constraint'''
    p[0] = p[1] + [p[3]]

def p_blocklist3(p):
    '''blocklist : block'''
    p[0] = [p[1]]

def p_block(p):
    '''block : CONSTANT LEFT_PAR atomlist RIGHT_PAR'''
    p[0] = Predicate(p[1], p[3], False)

def p_negatedblock(p):
    '''block : NOT CONSTANT LEFT_PAR atomlist RIGHT_PAR'''
    p[0] = Predicate(p[2], p[4], True)

def p_atomlist1(p):
    '''atomlist : atomlist COMMA atom'''
    p[0] = p[1] + [p[3]]

def p_atomlist2(p):
    '''atomlist : atom'''
    p[0] = [p[1]]

def p_atomvariable(p):
    '''atom : VARIABLE
        | UNDERSCORE'''
    p[0] = p[1]

def p_atomconstant(p):
    '''atom : CONSTANT'''
    p[0] = "\'" + p[1] + "\'"

def p_constraintvariable(p):
    '''constraint : VARIABLE OPERATOR VARIABLE'''
    p[0] = Constraint(p[1], p[2], p[3])

def p_constraintconstant(p):
    '''constraint : VARIABLE OPERATOR CONSTANT'''
    p[0] = Constraint(p[1], p[2], "\'" + p[3] + "\'")

    # def p_recursion(p):
    #  '''query : block recursive_query DOT'''
    #  p[0] = Tree(p[1], p[-1], 'query')

def p_error(p):
    print("Syntax error in input! ", p)

parser = yacc.yacc(start='program', write_tables=False, debug=False)

if __name__ == '__main__':
    parser = yacc.yacc(start='program')
    
    while True:
        try:
            s = input('datalog > ')
        except EOFError:
            break
        if not s: continue
        prog = parser.parse(s)
        print(prog)
