import os
import sys
import copy
from deprecation import deprecated
import networkx as nx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import Parser.yacc
from Parser.model import Fact, Predicate
def main(argv):
    facts = []
    rules = []
    query = []
    parser = Parser.yacc.parser
    file = open(argv[1], 'r')
    program = parser.parse(file.read())
    for p in program:
        if p.type == 'fact':
            print(p)
            facts.append(p)
        elif p.type == 'rule':
            rules.append(p)
        elif p.type == 'query':
            query.append(p)

    print(facts)
    print('\n', rules)
    print('\n', query)

    G = nx.DiGraph()

    # Parser.yacc.out.write("FACT:\n")
    # for f in fact:
    #     Parser.yacc.out.write(str(f) + "\n")
    #     G.add_node(f.fact)

    Parser.yacc.out.write("\nRULE:\n")
    for r in rules:
        Parser.yacc.out.write(str(r) + "\n")
        for body in r.body:
            if body.type == 'predicate' and not body.predicate == r.head.predicate:
                G.add_edge(body.predicate, r.head.predicate)

    Parser.yacc.out.write("\nQUERY:\n")
    for q in query:
        Parser.yacc.out.write(str(q) + "\n")

    # print('\n', G.nodes())
    # print('\n', G.edges())

    depends = nx.topological_sort(G)
    dependsList = list(depends)
    print('\nTopological sort:', dependsList)
    #Naive part
    #for each node in topological sort, implement of Extend dependency graph
    naiveEngine(dependsList, facts, rules)
    print("finally, get facts ", len(facts))
    for f in facts:
        print(f)

def naiveEngine(dependsList, facts, rules):
    for depend in dependsList:
        while True:
            newFacts = []
            for rule in rules:
                print("start find body in", rule.body)
                if depend in [x.predicate for x in rule.body if x.type == 'predicate']:
                    print("in body, depend is", depend)
                    newFacts = matchGoals(facts, rule)
                    print("new fact", newFacts)
                    if not len(newFacts) == 0:
                        break
            if len(newFacts) == 0:
                break
            facts.extend(newFacts)
            # print(facts)

            # match all the goals in the rule


def matchGoals(facts, rule):
    binding = {}
    #for each goal in body
    for body in rule.body:
        # print(body)
        # if body.buildin:
        #     do some thing
        # if body is negated:
        #     do some thing
        # else not negated
        if body.type == 'predicate':
            print("new facts length is", len(facts))
            b_facts = getFactsByPredicate(facts, body.predicate)
            # print(b_facts)
            for b_fact in b_facts:
                unifyBinding(b_fact.fact, body, binding)
    return matchHeader(rule.head, binding, facts)

# ('X', 'Y'): [['a', 'b'], ['a', 'c'], ['b', 'd'], ['c', 'd'], ['d', 'e']]
# above is value
# ('X', 'Y') is key
# list is the rest
# to {'X': {'c', 'a', 'd', 'b'}, 'Y': {'c', 'd', 'b', 'e'}}
# filter the variable value removed after doing intersection
# for example (X, Y) = (1,2), (2,3), (Y,Z) = (2,4).
# after intersection, Y = 2, 2 in X removed, then remove (2,3)
def filterBinding(binding, variable):
    for value in binding.values():
        for key in value.keys(): #('X', 'Y')
            for list in value[key].copy(): #['a', 'b']
                for i in range(0, len(list)):
                    print("check if value in new variable", list[i], variable[key[i]], list, value[key])
                    if not list[i] in variable[key[i]]:
                        if list in value[key]:
                            value[key].remove(list)
    print("new binding:", binding)

#make a tuple match to a new match, like
#('X', 'Y'): [['a', 'b'], ['a', 'c'], ['b', 'd'], ['c', 'd'], ['d', 'e']]
# to {'X': {'c', 'a', 'd', 'b'}, 'Y': {'c', 'd', 'b', 'e'}}
def globalIntersection(binding):
    variable = bindingToVariable(binding)
    filterBinding(binding, variable)
    print("new matching variable is:", variable)

def bindingToVariable(binding):
    variable = {}
    print(binding.values())
    for value in binding.values():
        for key in value.keys():
            for i in range(0, len(key)):
                listNew = []
                for v in value[key]:
                    listNew.append(v[i])
                    print(listNew)
                list = listNew
                if key[i] in variable.keys():
                    list = variable[key[i]]

                variable[key[i]] = set(listNew).intersection(list)
    return variable

@deprecated('duplicated implement')
def getVariablePossibleValue(variable, key):
    return variable[key]

#get variable tuple, which has key and value equals keyvalue
#('X', 'Y'): [['a', 'b'], ['a', 'c'], ['b', 'd'], ['c', 'd'], ['d', 'e']]
#return X == a
#('X', 'Y'): [['a', 'b'], ['a', 'c']]
@deprecated('duplicated implement')
def getVariableTuple(binding, key, keyValue):
    tuple = []
    for value in binding.values():
        for k in value.keys():
            print("search {} value {} in {}".format(key, keyValue, k))
            if key in k:
                #parser X in k (X, Y)
                for i in range(0, len(k)):
                    if key == k[i]:
                        #parser current tuple value [['a', 'b'], ['a', 'c'], ['b', 'd']]
                        #copy a new one, then do filter
                        tupleValue = copy.deepcopy(value)
                        print(" before filter tuple value is", tupleValue)
                        for v in value[k]:
                            print("     for each value list", v, v[i])
                            if not v[i] == keyValue:
                                print("         remove value", v)
                                tupleValue[k].remove(v)
                        print(" after filter tuple value is", tupleValue)
                        tuple.append(tupleValue)
    return tuple

# value of dict express by set
def mergeTwoDict(dict1, dict2):
    print("before update", dict1, dict2)
    dict = dict1.copy()
    dict1.update(dict2)
    print("previous dict and new dict1", dict, dict1)
    for key, value in dict1.items():
        if key in dict.keys():
            dict1[key] = value.union(dict[key])

    print("new dict", dict1)

def getDicFromTuplesByTerm(binding, term):
    dictList = []
    for value in binding.values():
        for key in value.keys():
            if term in key:
                for v in value[key]:
                    dic = {}
                    #dict(zip(key, v))
                    for i in range(0, len(key)):
                        dic[key[i]] = set(v[i])
                    dictList.append(dic)
    print("get {} in {} results {}".format(term, binding, dictList))
    return dictList

def checkIfDicSetValid(dict):
    for key, value in dict.items():
        print("check valid value", value)
        if not len(value) == 1:
            return False
    return True

# matching all possible variable, only the variable has one value is valid
# for example, (X, Y) = (1, 2) (Y, Z) = (2, 3) ==> (X, Y, Z) = (1, 2, 3)
# but, (X, Y) = (1, 4) (Y, Z) = (2, 3) ==> (X, Y, Z) = (1, {2,4}, 3), invalid
def filterDicByNewTermDic(dict, dictNew):
    print("original dict and new dict", dict, dictNew)
    if len(dict) == 0:
        dict.extend(dictNew)
        return
    filterList = []
    for dic in dict:
        for d in dictNew:
            dicFilter = dic.copy()
            mergeTwoDict(dicFilter, d)
            print("after intersection", dicFilter)
            filterList.append(dicFilter)

    list = filterList.copy()
    for f in list:
        if not checkIfDicSetValid(f):
            print("remove dit", f)
            filterList.remove(f)
    dict.clear()
    dict.extend(filterList)

#generate new facts from header
def matchHeader(header, binding, facts):
    globalIntersection(binding)
    variable = bindingToVariable(binding)
    print("new variable", variable)
    first = True
    dict = []
    for term in header.terms:
        # if first:
        #     first = False
        #     dict = getDicFromTuplesByTerm(binding, term)
        # else:
        dictNew = getDicFromTuplesByTerm(binding, term)
        filterDicByNewTermDic(dict, dictNew)

    print("after filter dict", dict)

    #now we get all the accept value for header
    newFacts = []
    for d in dict:
        term = [list(d[x])[0] for x in header.terms]
        print("get terms", term)
        fact = Fact(Predicate(header.predicate, term, header.isNegated))
        if not (checkFactExist(facts, fact) or checkFactExist(newFacts, fact)):
            print("get new fact", fact)
            newFacts.append(fact)
        # possible = getVariablePossibleValue(variable, term)
        # print("possible value for", term, possible)
        # for p in possible:
        #     tuple = getVariableTuple(binding, term, p)
        #     print("variable tuple is", tuple)

    return newFacts

def checkFactExist(facts, fact):
    return fact in facts

#get variable tuple for each goal
def unifyBinding(p1, p2, binding):
    if len(p1.terms) == len(p2.terms):
        # keys = (x for x in p1.terms)
        # print(keys)
        for i in range(0, len(p1.terms)-1):
            print(p1.terms[i])
            print(p2.terms[i])
        if isUpperCase(p2.terms):
            variable = {}
            if p2.predicate in binding.keys():
                variable = binding[p2.predicate]

            value = []
            if tuple(p2.terms) in variable.keys():
                value = variable[tuple(p2.terms)]
            value.append(p1.terms)

            variable[tuple(p2.terms)] = value
            binding[p2.predicate] = variable
            print("binding is:", binding)

def isUpperCase(list):
    for i in list:
        if not i.istitle():
            return False
    return True

#get the relative facts
def getFactsByPredicate(facts, name):
    return [x for x in facts if x is not None and x.fact.predicate == name]

    Parser.yacc.out.close()
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python datalog.py datalog.cdl')
        sys.exit(-1)
    main(sys.argv)