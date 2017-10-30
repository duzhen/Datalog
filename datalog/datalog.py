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

    Parser.yacc.out.write("FACT:\n")
    for f in fact:
        Parser.yacc.out.write(str(f) + "\n")
        G.add_node(f.fact)

    Parser.yacc.out.write("\nRULE:\n")
    for r in rule:
        Parser.yacc.out.write(str(r) + "\n")
        for body_literal in r.body:
            G.add_edge(body_literal, r.head)

    Parser.yacc.out.write("\nQUERY:\n")
    for q in query:
        Parser.yacc.out.write(str(q) + "\n")

    print('\n', G.nodes())
    print('\n', G.edges())

    # depends = nx.topological_sort(G)
    # print('\n', list(depends))
    Parser.yacc.out.close()
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python datalog.py datalog.cdl')
        sys.exit(-1)
    main(sys.argv)