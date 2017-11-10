import os
import sys
import copy
from deprecation import deprecated
import networkx as nx
import logging
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import Parser.yacc
from Parser.model import Fact, Predicate

RELEASE = False
TRACE_LEVEL = 39
log = logging.getLogger('Datalog')

logging.addLevelName(TRACE_LEVEL, "TRACE")

def trace(self, message, *args, **kws):
    # Yes, logger takes its '*args' as 'args'.
    if RELEASE:
        return
    if self.isEnabledFor(TRACE_LEVEL):
        self._log(TRACE_LEVEL, message, args, **kws)

def debug(self, message, *args, **kws):
    # Yes, logger takes its '*args' as 'args'.
    if RELEASE:
        return
    if self.isEnabledFor(TRACE_LEVEL):
        self._log(logging.DEBUG, message, args, **kws)

logging.Logger.trace = trace
logging.Logger.debug = debug

fh = logging.FileHandler('trace.log')
fh.setLevel(TRACE_LEVEL)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(levelname)s] >> %(message)s << %(funcName)s() %(asctime)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
log.setLevel(logging.DEBUG)
log.addHandler(fh)
log.addHandler(ch)

def evaluationLog(l):
    if not RELEASE:
        Parser.yacc.out.write(l)

def main(argv):
    log.trace("Start Parser File")
    facts = []
    rules = []
    query = []
    parser = Parser.yacc.parser
    file = open(argv[1], 'r')
    program = parser.parse(file.read())
    for e in Parser.yacc.errorList:
        evaluationLog(e)
    if not program:
        return
    for p in program:
        if p.type == 'fact':
            facts.append(p)
        elif p.type == 'rule':
            rules.append(p)
        elif p.type == 'query':
            query.append(p)

    checkProgramValidity(facts, rules, query)

    G = nx.DiGraph() #used for evaluation
    G2 = nx.DiGraph() # for stratified check
    evaluationLog("\nFACT:\n")
    for f in facts:
        evaluationLog(str(f) + "\n")

    evaluationLog("\nRULE:\n")
    for r in rules:
        evaluationLog(str(r) + "\n")
        for body in r.body:
            if body.type == 'predicate':
                weight = 1
                if body.isNegated:
                    weight = 0
                edge = (body.predicate, r.head.predicate)
                data = G2.get_edge_data(*edge)
                if data:
                    data['weight'] = data['weight'] * weight
                else:
                    G2.add_edge(body.predicate, r.head.predicate, weight=weight)

                if body.predicate == r.head.predicate:
                    G.add_node(body.predicate)
                else:
                    if not G.has_edge(r.head.predicate, body.predicate):
                        G.add_edge(body.predicate, r.head.predicate)
    evaluationLog("\nQUERY:\n")
    for q in query:
        evaluationLog(str(q) + "\n")
    #check stratified
    cycle = list(nx.simple_cycles(G2))
    if not len(cycle) == 0:
        if not checkStratified(G2, cycle):
            log.error("Datalog program do not satisfy the stratified safety")
            return
    depends = nx.topological_sort(G)
    # depends2= nx.topological_sort(G2)
    dependsList = list(depends)
    # dependsList2 = list(depends2)
    log.trace('Topological sort: {}'.format(dependsList))
    if len(dependsList) == 0:
        log.trace("No valid rule to do the evaluation")
        return
    # if len(dependsList2) != 0:
    #     log.trace('cut the cycle graph, get topological sort: {}'.format(dependsList2))
    #Naive part
    #for each node in topological sort, implement of Extend dependency graph
    log.trace("Perform Naive evaluation method")
    engine(dependsList, facts, rules)
    # engine(dependsList2, facts, rules)
    log.debug("Finish Naive evaluation method")
    log.debug("Totally have {} facts.".format(len(facts)))
    for f in facts:
        log.trace(f)

    log.trace("Perform query by the facts")
    queryFromFacts(query, facts)

def checkProgramValidity(facts, rules, query):
    warning = False
    for fact in facts.copy():
        if not isLowerCaseList(fact.fact.terms):
            facts.remove(fact)
            evaluationLog("Warning! Fact is not ground\n{}\n".format(str(fact)))
            log.warning("Warning! Fact is not ground")
            warning = True
    for q in query.copy():
        for p in q.query:
            if p.type == 'predicate':
                if p.isNegated and not isLowerCaseList(p.terms):
                    query.remove(q)
                    evaluationLog("\nWarning! Query value but with negation\n{}\n".format(str(q)))
                    log.warning("Warning! Query variable value but with negation")
                    warning = True
    for rule in rules.copy():
        if isLowerCaseList(rule.head.terms):
            break
        for t in rule.head.terms:
            vList = []
            for s in [x.terms for x in rule.body if x.type == 'predicate']:
                vList.extend(s)
            # log.debug("body variables {}".format(vList))
            if isLowerCase(t):
                rules.remove(rule)
                evaluationLog("\nWarning! Header has variable\n{}\n".format(str(rule)))
                log.warning("Warning! Header has variable")
                warning = True
                break
            elif not t in vList:
                rules.remove(rule)
                evaluationLog("\nWarning! Variable appears in Header but not in body\n{}\n".format(str(rule)))
                log.warning("Warning! Variable appears in Header but not in body")
                warning = True
                break

    if len(Parser.yacc.errorList) == 0:
        if warning:
            log.trace("Parser success, but warning in evaluation.log")
        else:
            log.trace("Parser success, no error found")
    else:
        log.trace("Parser failed, error save in evaluation.log")

    log.debug("Fact:{}".format(facts))
    log.debug("Rule:{}".format(rules))
    log.debug("Query:{}".format(query))

    return
def checkStratified(G, cycle):
    log.trace("Check if negation cycle in EDG, {}".format(cycle))
    edges = [zip(nodes, (nodes[1:] + nodes[:1])) for nodes in cycle]
    for c in edges:
        for e in c:
            data = G.get_edge_data(*e)
            if data['weight'] == 0:
                log.trace("There is negation cycle in EDG, {}".format(cycle))
                return False
    return True

def queryFromFacts(query, facts):
    log.trace("ANSWER:")
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
        # log.trace(answer)
        print(answer)

def builtRelativeRule(rules):
    return

def getRuleByNewFact(facts):
    return

def engine(dependsList, facts, rules):
    for i in range(0, len(dependsList)):
        depend = dependsList[i]
        # if not depend in [f.fact.predicate for f in facts]:
        #     if i < len(dependsList)-1:
        #         next = depend
        #         depend = dependsList[i+1]
        #         dependsList[i+1] = next
        #     else:
        #         continue
    # for depend in dependsList:
        semiRules = builtRelativeRule(rules)
        while True:
            log.trace("Evaluation predicate <{}> in EDB".format(depend))
            newFacts = []
            for rule in rules:
                log.trace("Start rule {}".format(rule))
                if depend in [x.predicate for x in rule.body if x.type == 'predicate']:
                    newFacts = matchGoals(facts, rule)
                    if not newFacts:
                        log.trace("Move forward to next rule")
                        continue
                    log.trace("Get {} new facts".format(len(newFacts)))
                    if not len(newFacts) == 0:
                        log.trace("Restart Evaluation from beginning")
                        break
                else:
                    log.trace("Skip this rule, no predicate in this rule")
            if not newFacts or len(newFacts) == 0:
                log.trace("Get 0 new facts, finish and move forward to next node")
                break
            log.debug("New facts:")
            for f in newFacts:
                evaluationLog("*{}\n".format(f))
                log.debug("******{}".format(f))
            facts.extend(newFacts)
            if False:#semi-naive
                # semi-naive part
                rules = getRuleByNewFact(facts)
    log.trace("Achieved least fix-point totally {} facts.".format(len(facts)))

# match all the goals in the rule
def matchGoals(facts, rule):
    binding = {}
    bindingFact = [] # for fact in body
    builtInBody = []
    #for each goal in body
    for body in rule.body:
        # print(body)
        # if body.builtin:
        #     do some thing
        # if body is negated:
        #     do some thing
        # else not negated
        if body.type == 'predicate':
            log.trace("Start match predicate {}".format(body))
            if isLowerCaseList(body.terms):
                exist = body.terms in [x.fact.terms for x in facts]
                log.debug("Body is a ground clause, value is {}".format(exist))
                if not exist:
                    return

            b_facts = getFactsByPredicate(facts, body.predicate)
            log.debug("in body {} get fact {}".format(body.predicate, b_facts))
            log.trace("Find {} facts with this predicate".format(len(b_facts)))
            if len(b_facts) == 0:
                log.trace("Leave current rule")
                return
            else:
                for b_fact in b_facts:
                    if not unifyBinding(b_fact.fact, body, binding, bindingFact, facts):
                        continue
        else:
            builtInBody.append(body)
            log.trace("Temp save one built-in predicate {}".format(body))
    if not len(bindingFact) == 0 and len(binding) == 0 and isLowerCaseList(rule.head.terms):
        fact = Fact(rule.head)
        if not (checkFactExist(facts, fact)):
            log.trace("******Get new fact {}".format(fact))
            return [fact]
        else:
            return []
    log.trace("Start match built-in predicate {}".format(builtInBody))
    # do some thing for builtIn predicate
    dict = globalIntersection(binding, rule.body)
    return matchHeader(rule, binding, facts, dict)

# ('X', 'Y'): [['a', 'b'], ['a', 'c'], ['b', 'd'], ['c', 'd'], ['d', 'e']]
# above is value
# ('X', 'Y') is key
# list is the rest
# to {'X': {'c', 'a', 'd', 'b'}, 'Y': {'c', 'd', 'b', 'e'}}
# filter the variable value removed after doing intersection
# for example (X, Y) = (1,2), (2,3), (Y,Z) = (2,4).
# after intersection, Y = 2, 2 in X removed, then remove (2,3)
def filterBinding(binding, variable):
    log.trace("Perform a bit optimization, remove unsatisfied tuple value")
    for value in binding.values(): # each predicate as key
        for key in value.keys(): #('X', 'Y')
            for l in value[key].copy(): #['a', 'b']
                for i in range(0, len(l)):
                    # print("check if value in new variable", list[i], variable[key[i]], list, value[key])
                    if not l[i] in variable[key[i]]:
                        if l in value[key]:
                            value[key].remove(l)

#make a tuple match to a new match, like
#('X', 'Y'): [['a', 'b'], ['a', 'c'], ['b', 'd'], ['c', 'd'], ['d', 'e']]
# to {'X': {'c', 'a', 'd', 'b'}, 'Y': {'c', 'd', 'b', 'e'}}
def globalIntersection(binding, body):
    variable = bindingToVariable(binding, body)
    filterBinding(binding, variable)

    dict = []
    # for term in ['X', 'Y']:
    log.trace("Perform global intersection")
    for value in binding.values():
        for key, v in value.items():
            # if first:
            #     first = False
            #     dict = getDicFromTuplesByTerm(binding, term)
            # else:
            dictNew = getDicFromTuplesByTerm(key, v)
            filterDicByNewTermDic(dict, dictNew)
            # [{'X': {'a'}, 'Z': {'b'}, 'Y': {'d'}}, {'X': {'a'}, 'Z': {'b'}, 'Y': {'a'}}]

    log.debug("After do intersection, dictionary is {}".format(dict))
    return dict

def checkBodyNegative(predicate, key, body):
    log.trace("check negative {}, key is {}".format(predicate, key))
    for b in body:
        if b.type == 'predicate' and b.predicate == predicate and b.terms == list(key):
            return b.isNegated
    return False

def bindingToVariable(binding, body):
    variable = {}
    # print(binding.values())
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
    log.debug("after process negative, {}".format(binding))
    for bindingKey, value in binding.items():
        for key, keyValue in value.items():
            localVariable = {}
            for i in range(0, len(key)): #(X, X)
                listNew = []
                for v in value[key]:
                    listNew.append(v[i])
                    # print(listNew)
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
    log.debug("variable is {}".format(variable))
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
    # print("before update", dict1, dict2)
    for key, value in dict1.items():
        if key in dict2.keys() and not value == dict2[key]:
            return
    dict = dict1.copy()
    dict1.update(dict2)
    # print("previous dict and new dict1", dict, dict1)
    for key, value in dict1.items():
        if key in dict.keys():
            dict1[key] = value.union(dict[key])
    if not checkIfDicSetValid(dict1):
        log.trace("I should check first, not check after.")
        return
    return dict1
    log.debug("Get new dictionary {}", dict)
    # print("new dict", dict1)

def getDicFromTuplesByTerm(key, value):
    log.trace("Get dictionary value from facts{}".format(key))
    dictList = []
    for v in value:
        dic = {}
        for i in range(0, len(key)):
            dic[key[i]] = set([v[i]])
        dictList.append(dic)
    log.debug("generate new dictList {}".format(dictList))
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
    # print("original dict and new dict", dict, dictNew)
    log.trace("Merge two dictionary and do filter")
    if len(dict) == 0:
        dict.extend(dictNew)
        return
    filterList = []
    for dic in dict:
        for d in dictNew:
            dicFilter = dic.copy()
            newDic = mergeTwoDict(dicFilter, d)
            if newDic:
                filterList.append(dicFilter)
    log.trace("Check satisfy for each dictionary, if len(value) > 1, then remove it")
    list = filterList.copy()
    for f in list:
        if not checkIfDicSetValid(f):
            log.trace("I don't want to see some dict is out of the filter")
            filterList.remove(f)
    dict.clear()
    dict.extend(filterList)

#generate new facts from header
def matchHeader(rule, binding, facts, dict):
    # variable = bindingToVariable(binding)
    # print("new variable", variable)
    log.trace("start to match header {}".format(rule.head.predicate))
    header = rule.head
    #now we get all the accept value for header
    newFacts = []
    for d in dict:
        for t in header.terms:
            if not t in d: # free variable in header
                assert()
                return newFacts
        if satisfybuiltInPredicate(d, rule.body):
            term = [list(d[x])[0] for x in header.terms]
            # print("get terms", term)
            fact = Fact(Predicate(header.predicate, term, header.isNegated))
            if not (checkFactExist(facts, fact) or checkFactExist(newFacts, fact)):
                log.trace("******Get new fact {}".format(fact))
                newFacts.append(fact)
        # possible = getVariablePossibleValue(variable, term)
        # print("possible value for", term, possible)
        # for performance in possible:
        #     tuple = getVariableTuple(binding, term, performance)
        #     print("variable tuple is", tuple)

    return newFacts

def satisfybuiltInPredicate(dict, body):
    #X==Y, can precess directly, <=, >= >, < need the variable ground
    log.trace("Perform builtIn predicate check {}".format(body))
    return True

def checkFactExist(facts, fact):
    return fact in facts

# get variable tuple for each goal
# p1: fact, p2:body
def unifyBinding(p1, p2, binding, bindingFact, facts):
    if len(p1.terms) == len(p2.terms):
        # keys = (x for x in p1.terms)
        # print(keys)
        # for i in range(0, len(p1.terms)-1):
        #     print(p1.terms[i])
        #     print(p2.terms[i])
        log.debug("fact is {}, body is {}".format(p1, p2))
        if True:#isUpperCaseList(p2.terms):
            variable = {}
            if p2.predicate in binding.keys():
                variable = binding[p2.predicate]

            termsKey = p2.terms.copy()
            termsValue = p1.terms.copy()
            for i in range(0, len(p2.terms)):
               if isLowerCase(p2.terms[i]):
                   if p1.terms[i] != p2.terms[i]:
                        log.warning("Body terms contains constant not equal with current facts, skip")
                        return False
                   else:
                       termsKey.remove(p2.terms[i])
                       termsValue.remove(p1.terms[i])
            value = []
            if tuple(termsKey) in variable.keys():
                value = variable[tuple(termsKey)]
            value.append(termsValue)

            variable[tuple(termsKey)] = value
            binding[p2.predicate] = variable
            log.trace("Collect potential tuple values for {}".format(p2))
            log.debug("potential value is {}".format(binding))
        # elif isLowerCaseList(p2.terms):
        #     exist = p2.terms in [x.fact.terms for x in facts]
        #     bindingFact.append(exist)
        #     log.debug("Body is a ground clause, value is {}".format(exist))
        #     return exist
        else:
            log.warning("Terms contains constant, terms is {}".format(p2.terms))
        return True
    return False
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
    start = time.time()
    main(sys.argv)
    Parser.yacc.out.close()
    log.info("Total time: {} seconds".format(time.time()-start))