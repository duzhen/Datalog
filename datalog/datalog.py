import os
import sys
import networkx as nx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import Parser.yacc

def main(argv):
    fact = []
    rule = []
    query = []
    parser = Parser.yacc.parser
    file = open(argv[1], 'r')
    program = parser.parse(file.read())
    for p in program:
        if p.type == 'fact':
            fact.append(p)
        elif p.type == 'rule':
            rule.append(p)
        elif p.type == 'query':
            query.append(p)
    print(fact)
    print('\n', rule)
    print('\n', query)

    G = nx.DiGraph()

    for f in fact:
        G.add_node(f.fact)

    for r in rule:
        for body_literal in r.body:
            G.add_edge(body_literal, r.head)

    print('\n', G.nodes())
    print('\n', G.edges())

    # depends = nx.topological_sort(G)
    # print('\n', list(depends))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python datalog.py datalog.cdl')
        sys.exit(-1)
    main(sys.argv)