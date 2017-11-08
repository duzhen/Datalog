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
    if not program:
        return
    for p in program:
        if p.type == 'fact':
            print(p)
            facts.append(p)
        elif p.type == 'rule':
            rules.append(p)
        elif p.type == 'query':
            query.append(p)
    for fact in facts.copy():
        if not isLowerCaseList(fact.fact.terms):
            facts.remove(fact)
            Parser.yacc.out.write("\nBad value in Fact\n" + str(fact))
    for q in query.copy():
        for p in q.query:
            if p.type == 'predicate':
                if p.isNegated and not isLowerCaseList(p.terms):
                    query.remove(q)
                    Parser.yacc.out.write("\nBad negation query\n" + str(q))
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
    engine(dependsList, facts, rules)
    print("finally, get facts ", len(facts))
    for f in facts:
        print(f)

    print('\n', query)
    queryFromFacts(query, facts)

def queryFromFacts(query, facts):
    print("ANSWER:")
    for q in query:
        answer = []
        for p in q.query:
            if p.type == 'predicate':
                newFacts = getFactsByPredicate(facts, p.predicate, len(p.terms))
                if isLowerCaseList(p.terms):
                    r = False
                    for f in newFacts:
                        if f.fact.terms == p.terms:
                            r = p.isNegated == f.fact.isNegated
                    answer.append(r)
                else:
                    for f in newFacts.copy():
                        for i in range(0, len(p.terms)):
                            if isLowerCase(p.terms[i]):
                                if not f.fact.terms[i] == p.terms[i]:
                                    newFacts.remove(f)
                    answer.append([tuple(x.fact.terms) for x in newFacts])
        print(answer)

def buildRelativeRule(rules):
    return

def getRuleByNewFact():
    return

def engine(dependsList, facts, rules):
    for depend in dependsList:
        semiRules = buildRelativeRule(rules)
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
                    else:
                        #semi-naive part
                        rules = rules#getRuleByNewFact(newFacts, semiRules)
            if len(newFacts) == 0:
                break
            for f in newFacts:
                Parser.yacc.out.write("\n*{}\n".format(f))
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
                if not unifyBinding(b_fact.fact, body, binding, facts):
                    return
    globalIntersection(binding, rule.body)
    return matchHeader(rule, binding, facts)

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
def globalIntersection(binding, body):
    variable = bindingToVariable(binding, body)
    filterBinding(binding, variable)
    print("new matching variable is:", variable)

def checkBodyNegative(predicate, key, body):
    print("check negative", predicate, key)
    for b in body:
        if b.type == 'predicate' and b.predicate == predicate and b.terms == list(key):
            return b.isNegated
    return False

def bindingToVariable(binding, body):
    variable = {}
    print(binding.values())
    negativeValue = []
    # for bindingKey, value in binding.items():
    #     for key, keyValue in value.items():
    #         # check if edge(X, Y) in body is negative, we cannot have edge(X, Y), not edge(X, Y)
    #         if checkBodyNegative(bindingKey, key, body):
    #             # negativeValue.extend(keyValue)
    #             print(keyValue, value)
    #             if keyValue in value:
    #                 value = value - keyValue

    # for bindingKey, value in binding.items():
    #     for key, keyValue in value.items():
    print("after process negative", binding)
    for bindingKey, value in binding.items():
        for key, keyValue in value.items():
            localVariable = {}
            for i in range(0, len(key)): #(X, X)
                listNew = []
                for v in value[key]:
                    listNew.append(v[i])
                    print(listNew)
                list = listNew
                if key[i] in variable.keys():
                    list = variable[key[i]]
                # if not key[i] in localVariable.keys():
                #     localVariable[key[i]] = []
                # localVariable[key[i]].append(listNew)
                # if i == len(key) - 1:
                #     for localV in localVariable.values():
                #         localVCopy = localV.copy()
                #         if len(localV) > 1:
                #             firstV = localV[0].copy()
                #             for index in range(0, len(firstV)):
                #                 for k in range(0, len(localV)):
                #                     if not localVCopy[k][index] == firstV[index]:
                #                         for l in range(0, len(localV)):
                #                             if localVCopy[l][index] in localV[l]:
                #                                 localV[l].remove(localVCopy[l][index])
                #
                # print(localVariable)


                # if key[i] in variable.keys(): # value already exist
                #     if key[i] in localVariable.keys():
                #         copyListNew = listNew.copy()
                #         for j in range(0, len(copyListNew)): # local intersection
                #             print(listNew, localVariable[key[i]])
                #             if not copyListNew[j] == localVariable[key[i]][j]:
                #                 listNew.remove(copyListNew[j])
                # if not key[i] in localVariable.keys():
                #     localVariable[key[i]] = listNew
                # check if edge(X, Y) in body is negative, we cannot have edge(X, Y), not edge(X, Y)
                variable[key[i]] = set(listNew).intersection(list)
            # if checkBodyNegative(bindingKey, key, body):
            #     localBinding = {bindingKey: value}
            #     filterBinding(localBinding, localVariable)

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
        # print("check valid value", value)
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
            # print("remove dit", f)
            filterList.remove(f)
    dict.clear()
    dict.extend(filterList)

#generate new facts from header
def matchHeader(rule, binding, facts):
    # variable = bindingToVariable(binding)
    # print("new variable", variable)
    header = rule.head
    first = True
    dict = []
    for term in header.terms:
        # if first:
        #     first = False
        #     dict = getDicFromTuplesByTerm(binding, term)
        # else:
        dictNew = getDicFromTuplesByTerm(binding, term)
        filterDicByNewTermDic(dict, dictNew)
        #[{'X': {'a'}, 'Z': {'b'}, 'Y': {'d'}}, {'X': {'a'}, 'Z': {'b'}, 'Y': {'a'}}]

    print("after filter dict", dict)

    #now we get all the accept value for header
    newFacts = []
    for d in dict:
        for t in header.terms:
            if not t in d: # free variable in header
                return newFacts
        if satisfyBuildInPredicate(d, rule.body):
            term = [list(d[x])[0] for x in header.terms]
            # print("get terms", term)
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

def satisfyBuildInPredicate(dict, body):
    return True

def checkFactExist(facts, fact):
    return fact in facts

#get variable tuple for each goal
def unifyBinding(p1, p2, binding, facts):
    if len(p1.terms) == len(p2.terms):
        # keys = (x for x in p1.terms)
        # print(keys)
        # for i in range(0, len(p1.terms)-1):
        #     print(p1.terms[i])
        #     print(p2.terms[i])
        if isUpperCaseList(p2.terms):
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
        elif isLowerCaseList(p2.terms):
            return p2.terms in [x.terms for x in facts]

    return True
def isUpperCaseList(list):
    for i in list:
        if not i.istitle():
            return False
    return True

def isLowerCaseList(list):
    for i in list:
        if i.istitle():
            return False
    return True

def isUpperCase(c):
    return c.istitle()

def isLowerCase(c):
    return not c.istitle()

#get the relative facts
def getFactsByPredicate(facts, name, termLength=None):
    if termLength:
        return [x for x in facts if x is not None and x.fact.predicate == name and len(x.fact.terms) == termLength]
    else:
        return [x for x in facts if x is not None and x.fact.predicate == name]

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python datalog.py datalog.cdl')
        sys.exit(-1)
    main(sys.argv)
    Parser.yacc.out.close()