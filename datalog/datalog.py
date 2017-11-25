import os
import sys
import copy
from deprecation import deprecated
import networkx as nx
import logging
import time
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import Parser.yacc
from Parser.model import Fact, Predicate

parser = argparse.ArgumentParser(description="Datalog bottom-up evaluation implement by Python, support Naive, Semi-Naive, Built-Ins and Negation")
parser.add_argument("-p", action='store_true', dest="verbose", default=False, help="Prints parser result to file.")
parser.add_argument("-c", action='store_true', dest="command", default=False, help="Command to query.")
parser.add_argument("-t", action='store_true', dest="trace", default=False, help="Trace evaluation progress.")
parser.add_argument("-x", action='store_true', dest="optimize", default=False, help="Turn on optimization mode.")

subparsers = parser.add_subparsers(help='commands')

naive_parser = subparsers.add_parser('naive', help='Bottom up evaluation with naive method search.')
naive_parser.set_defaults(which='naive')
semi_parser = subparsers.add_parser('semi-naive', help='Bottom up evaluation with semi-naive method search')
semi_parser.set_defaults(which='semi-naive')
parser.add_argument("file", help="Datalog program file")

args = parser.parse_args()
TRACE = args.trace

start = time.time()
lastTime = 0

RELEASE = True
TRACE_LEVEL = 38
T_LEVEL = 39

log = logging.getLogger('Datalog')

logging.addLevelName(TRACE_LEVEL, "TRACE")
logging.addLevelName(T_LEVEL, "TRACE")

def t(self, message, *args, **kws):
    # Yes, logger takes its '*args' as 'args'.
    if not TRACE:
        return
    if self.isEnabledFor(T_LEVEL):
        self._log(T_LEVEL, message, args, **kws)

def trace(self, message, release=RELEASE, *args, **kws):
    # Yes, logger takes its '*args' as 'args'.
    if release:
        return
    if self.isEnabledFor(TRACE_LEVEL):
        self._log(TRACE_LEVEL, message, args, **kws)

def debug(self, message, release=RELEASE, *args, **kws):
    # Yes, logger takes its '*args' as 'args'.
    if release:
        return
    if self.isEnabledFor(TRACE_LEVEL):
        self._log(logging.DEBUG, message, args, **kws)

logging.Logger.trace = trace
logging.Logger.debug = debug
logging.Logger.t = t

fh = logging.FileHandler('trace.log')
fh.setLevel(TRACE_LEVEL)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
if RELEASE:
    formatter = logging.Formatter('[%(levelname)s] >> %(message)s <<')
else:
    formatter = logging.Formatter('[%(levelname)s] >> %(message)s << %(funcName)s() %(asctime)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
log.setLevel(logging.DEBUG)
log.addHandler(fh)
log.addHandler(ch)

facts = []
rules = []
query = []

def evaluationLog(l):
    if args.verbose:
        Parser.yacc.out.write(l)

def logTime(step):
    if RELEASE:
        return
    global lastTime
    current = time.time()
    spend = current - start
    log.trace("{} spend time:{} s, total time:{} s, total facts:{}".format(step, current-lastTime, spend, len(facts)), release=False)
    lastTime = current

def main(argv):
    log.trace("Start Parser File")

    parser = Parser.yacc.parser
    file = open(args.file, 'r')
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
    evaluationLog("FACT:\n")
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

    evaluationLog("\n{}\n".format("\nNEW FACTS:\n"))
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
    if not args.which == 'semi-naive':
        log.t("Perform naive evaluation method")

    logTime("Parser and safety check")
    engine(dependsList, facts, rules)
    logTime("Perform program evaluation")
    if not args.which == 'semi-naive':
        log.debug("Finish Naive evaluation method")
    log.debug("Totally have {} facts.".format(len(facts)))
    for f in facts:
        log.trace(f)

    log.trace("Perform query by the facts")
    queryFromFacts(query, facts)
    logTime("Perform query from fact")

def checkProgramValidity(facts, rules, query):
    warning = False
    for fact in facts.copy():
        if not isLowerCaseList(fact.fact.terms):
            facts.remove(fact)
            evaluationLog("Warning! Fact is not ground\n{}\n".format(str(fact)))
            log.warning("Warning! Fact is not ground")
            warning = True

    for rule in rules.copy():
        bList = []
        pList = []
        for s in [x.terms for x in rule.body if x.type == 'predicate']:
            bList.extend(s)
        for s in [x.termX for x in rule.body if x.type == 'constraint']:
            if isUpperCase(s):
                pList.extend(s)
        for s in [x.termY for x in rule.body if x.type == 'constraint']:
            if isUpperCase(s):
                pList.extend(s)
        remove = False
        for p in pList:
            if not p in bList:
                rules.remove(rule)
                evaluationLog("\nWarning! Built-ins is not safety\n{}\n".format(str(rule)))
                log.warning("Warning! Built-ins is not safety")
                warning = True
                remove = True
                break
        if remove:
            continue
        if isLowerCaseList(rule.head.terms):
            break
        for t in rule.head.terms:
            vList = []
            for s in [x.terms for x in rule.body if x.type == 'predicate']:
                vList.extend(s)
            # log.debug("body variables {}".format(vList))
            if False:#isLowerCase(t):
                rules.remove(rule)
                evaluationLog("\nWarning! Header has variable\n{}\n".format(str(rule)))
                log.warning("Warning! Header has variable")
                warning = True
                break
            elif not t in vList:
                rules.remove(rule)
                evaluationLog("\nWarning! Variable appears in header but not in body\n{}\n".format(str(rule)))
                log.warning("Warning! Variable appears in header but not in body")
                warning = True
                break
    for q in query.copy():
        for p in q.query:
            if p.type == 'predicate':
                if p.isNegated and not isLowerCaseList(p.terms):
                    query.remove(q)
                    evaluationLog("\nWarning! Query value but with negation\n{}\n".format(str(q)))
                    log.warning("Warning! Query variable value but with negation")
                    warning = True

    if len(Parser.yacc.errorList) == 0:
        if warning:
            log.trace("Parser success, see warning in p.res")
        else:
            log.trace("Parser success, no error found")
    else:
        log.trace("Parser failed, see error in p.res")

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
    evaluationLog("\n{}\n".format("ANSWER:"))
    print("ANSWER:")
    for q in query:
        answer = []
        builtInVariable, builtInBody = getBuiltInTerm(q.query)
        for p in q.query:
            if p.type == 'predicate':
                newFacts = getFactsByPredicate(facts, p.predicate, termLength = len(p.terms))
                if isLowerCaseList(p.terms):
                    r = False
                    for f in newFacts:
                        if f.fact.terms == p.terms:
                            r = p.isNegated == f.fact.isNegated
                    answer.append(r)
                else:
                    for f in newFacts.copy():
                        remove = False
                        dict = {}
                        for i in range(0, len(p.terms)):
                            if isLowerCase(p.terms[i]):
                                if not f.fact.terms[i] == p.terms[i]:
                                    newFacts.remove(f)
                                    remove = True
                                    break
                            elif p.terms[i] in dict.keys():
                                preValue = dict[p.terms[i]]
                                if preValue != f.fact.terms[i]:
                                    newFacts.remove(f)
                                    remove = True
                                    break
                            else:
                                dict[p.terms[i]] = f.fact.terms[i]
                        # built-in predicate
                        if not remove:

                            # for i in range(0, len(p.terms)):
                            #     if p.terms[i] in dict.keys():
                            #         preValue = dict[p.terms[i]]
                            #         if preValue != f.fact.terms[i]:
                            #             newFacts.remove(f)
                            #             break
                            #     else:
                            #         dict[p.terms[i]] = f.fact.terms[i]
                            if not evaluateBuiltInPredicate(dict, builtInBody, False):
                                newFacts.remove(f)
                    answer.append([tuple(x.fact.terms) for x in newFacts])
        # log.trace(answer)
        evaluationLog("{}\n".format(answer))
        print(answer)

def builtRelativeRule(rules):
    semiRules = {}
    for rule in rules:
        if not rule.head.predicate in semiRules.keys():
            semiRules[rule.head.predicate] = []
        rs = semiRules[rule.head.predicate]
        rs.append(rule)
        for body in rule.body:
            if body.type == 'predicate':
                if not body.predicate in semiRules.keys():
                    semiRules[body.predicate] = []
                rs = semiRules[body.predicate]
                rs.append(rule)
    log.debug("Built semi rules {}".format(semiRules))
    return semiRules

def getRuleByNewFact(facts, semiRules):
    rules = set()
    for f in facts:
        if f.fact.predicate in semiRules:
            for r in semiRules[f.fact.predicate]:
                rules.add(r)
    return list(rules)

#record fact has processed by specific rule
def resetFacts():
    for fact in facts:
        fact.record.clear()

evaluateTimes = 1
def engine(dependsList, facts, rules):
    global evaluateTimes
    if args.which == 'semi-naive':
        log.t("Perform semi-naive evaluation method")
        semiRules = builtRelativeRule(rules)
        rules = getRuleByNewFact(facts, semiRules)
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
        while True:
            log.t("Evaluation predicate <{}> in EDB".format(depend))
            newFacts = []
            resetFacts()
            for i in range(0, len(rules)):
            # for rule in rules:
                rule = rules[i]
                log.trace("Inference rule {}".format(rule.head))
                if depend in [x.predicate for x in rule.body if x.type == 'predicate']:
                    log.t("Inference rule {}".format(rule.head))
                    newFacts = matchGoals(facts, rule, i)
                    logTime("\tTotal {} time perform evaluation".format(evaluateTimes))
                    evaluateTimes += 1
                    if not newFacts:
                        log.trace("Nothing get, return")
                        continue
                    log.t("Get {} new facts".format(len(newFacts)))
                    if not len(newFacts) == 0:
                        if args.which == 'semi-naive':
                            log.t("semi-Naive restart evaluation")
                            if TRACE:
                                print("\t----------------------------------------------------------------")
                        else:
                            log.t("Naive restart evaluation")
                            if TRACE:
                                print("\t----------------------------------------------------------------")
                        break
                else:
                    log.trace("Skip this rule, no predicate in this rule")
            if not newFacts or len(newFacts) == 0:
                log.t("No more new facts, return")
                break
            log.debug("New facts:")
            for f in newFacts:
                evaluationLog("*{}\n".format(f))
                log.debug("******{}".format(f))
            facts.extend(newFacts)
            if args.which == 'semi-naive':
                # semi-naive part
                rules = getRuleByNewFact(facts, semiRules)
                log.trace("Semi-Naive derive this rules {}".format(rules))
    log.t("Achieved least fix-point, total {} facts.".format(len(facts)))

# match all the goals in the rule
def matchGoals(facts, rule, ruleIndex):
    # perform negation check first
    n_facts = facts.copy()
    for nb in rule.body:
        if nb.type == 'predicate' and nb.isNegated:
            log.t("process negation predicate {}".format(nb))
            b_facts = getFactsByPredicate(n_facts, nb.predicate)
            if isLowerCaseList(nb.terms):
                if nb.terms in [x.fact.terms for x in b_facts]:
                    return
            else:
                for b_fact in b_facts:
                    if len(b_fact.fact.terms) == len(nb.terms):
                        termsKey = nb.terms.copy()
                        termsValue = b_fact.fact.terms.copy()
                        for i in range(0, len(nb.terms)):
                            if isLowerCase(nb.terms[i]):
                                if b_fact.fact.terms[i] != nb.terms[i]:
                                    break
                                else:
                                    termsKey.remove(nb.terms[i])
                                    termsValue.remove(b_fact.fact.terms[i])
                            if i == len(nb.terms)-1:
                                if checkUnifiable(tuple(termsKey), termsValue):
                                    log.t("  drop fact {}".format(b_fact))
                                    n_facts.remove(b_fact)

    binding = {}
    #for each goal in body
    for b in range(0, len(rule.body)):
        body = rule.body[b]
    # for body in rule.body:
        # print(body)
        # if body.builtin:
        #     do some thing
        # if body is negated:
        #     do some thing
        # else not negated
        if body.type == 'predicate' and not body.isNegated:
            log.trace("Start match predicate {}".format(body))

            b_facts = getFactsByPredicate(n_facts, body.predicate, ruleIndex, b)
            if isLowerCaseList(body.terms):
                exist = body.terms in [x.fact.terms for x in b_facts]
                log.debug("Body is a ground clause, value is {}".format(exist))
                if body.isNegated:
                    log.t("process negation predicate {}".format(body))
                if exist == body.isNegated:
                    return
                else:
                    continue

            log.debug("in body {} get fact {}".format(body.predicate, b_facts))
            log.trace("Find {} facts with this predicate".format(len(b_facts)))
            if len(b_facts) == 0:
                log.trace("Leave current rule")
                return
            else:
                for b_fact in b_facts:
                    if args.optimize:
                        b_fact.record.add("{}.{}".format(ruleIndex, b))
                    if not unifyBinding(b_fact.fact, body, binding, facts):
                        continue
        if len(binding) == 0:
            log.debug("At least one body cannot unify from all the facts")
            break
        # else:
        #     builtInBody.append(body)
        #     log.trace("Temp save one built-in predicate {}".format(body))
    if len(binding) == 0 and isLowerCaseList(rule.head.terms):
        fact = Fact(rule.head)
        if not (checkFactExist(facts, fact)):
            log.t("******Get new fact {}".format(fact))
            return [fact]
        else:
            return []
    logTime("\t\tThe {} time perform local unify binding".format(evaluateTimes))
    dict = globalUnify(binding, rule.body)
    logTime("\t\tThe {} time perform global unify binding".format(evaluateTimes))
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
    log.t("perform optimization, filter substitution not in ground intersection set")
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
def globalUnify(binding, body):
    variable = bindingToVariable(binding, body)
    if args.optimize:
        filterBinding(binding, variable)

    log.trace("evaluate built-in predicate before do global intersection")
    builtInVariable, builtInBody = getBuiltInTerm(body)
    dict = []
    # for term in ['X', 'Y']:
    log.t("global unification")
    for value in binding.values():
        for key, v in value.items():
            dictNew = getDicFromTuplesByTerm(key, v, builtInVariable, builtInBody)
            filterDicByNewTermDic(dict, dictNew)
            # [{'X': {'a'}, 'Z': {'b'}, 'Y': {'d'}}, {'X': {'a'}, 'Z': {'b'}, 'Y': {'a'}}]

    log.debug("After do intersection, dictionary is {}".format(dict))
    return dict


def getBuiltInTerm(body):
    builtInBody = []
    builtInVariable = set()
    for b in body:
        if b.type == 'constraint':
            builtInBody.append(b)
            if not isLowerCase(b.termX):
                builtInVariable.add(b.termX)
            if not isLowerCase(b.termY):
                builtInVariable.add(b.termY)
    return builtInVariable, builtInBody

def checkBodyNegative(predicate, key, body):
    log.trace("check negative {}, key is {}".format(predicate, key))
    for b in body:
        if b.type == 'predicate' and b.predicate == predicate and b.terms == list(key):
            return b.isNegated
    return False

def checkUnifiable(key, value):
    dict = {}
    for i in range(0, len(key)):
        if not key[i] in dict:
            dict[key[i]] = set()
        dict[key[i]].add(value[i])
    for v in dict.values():
        if not len(v) == 1:
            log.t("  unify local substitution {},{} -> nonunifiable".format(key, value))
            return False
    log.t("  unify local substitution {},{} -> unifiable".format(key, value))
    return True


def bindingToVariable(binding, body):
    log.t("get possible fact set {}".format(binding))
    log.t("local unification")
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
            for v in value[key].copy():
                if not checkUnifiable(key, v):
                    value[key].remove(v)
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
    if not checkIfDicSetUnifiable(dict1):
        log.trace("I should check first, not check after.")
        return
    return dict1
    log.debug("Get new dictionary {}", dict)
    # print("new dict", dict1)

def getDicFromTuplesByTerm(key, value, builtInVariable, builtInBody):
    log.trace("Get dictionary value from facts{}".format(key))
    dictList = []
    for v in value:
        dic = {}
        for i in range(0, len(key)):
            dic[key[i]] = set([v[i]])
        if set(key) >= builtInVariable and len(builtInVariable) > 0:
            if not evaluateBuiltInPredicate(dic, builtInBody):
                continue
        dictList.append(dic)
    log.debug("generate new dictList {}".format(dictList))
    return dictList

def checkIfDicSetUnifiable(dict):
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
    log.trace("unify two substitution {},{}".format(dict, dictNew))
    if len(dict) == 0:
        dict.extend(dictNew)
        return
    filterList = []
    for dic in dict:
        for d in dictNew:
            dicFilter = dic.copy()
            logdic = dicFilter.copy()
            newDic = mergeTwoDict(dicFilter, d)
            if newDic:
                log.t("  most general unifier {},{} -> unifiable".format(logdic, d))
                filterList.append(dicFilter)
            else:
                log.t("  most general unifier {},{} -> nonunifiable".format(logdic, d))
    log.trace("Check satisfy for each dictionary, if len(value) > 1, then remove it")
    list = filterList.copy()
    for f in list:
        if not checkIfDicSetUnifiable(f):
            log.trace("I don't want to see some dict is out of the filter in mergeTwoDict process")
            filterList.remove(f)
    dict.clear()
    dict.extend(filterList)

#generate new facts from header
def matchHeader(rule, binding, facts, dict):
    # variable = bindingToVariable(binding)
    # print("new variable", variable)
    log.trace("use GMP to generate new facts {}".format(rule.head.predicate))
    header = rule.head
    builtInVariable, builtInBody = getBuiltInTerm(rule.body)
    #now we get all the accept value for header
    newFacts = []
    for d in dict:
        for t in header.terms:
            if not t in d: # free variable in header
                if not RELEASE:
                    assert()
                return newFacts
        if evaluateBuiltInPredicate(d, builtInBody):
            term = [list(d[x])[0] for x in header.terms]
            # print("get terms", term)
            fact = Fact(Predicate(header.predicate, term, header.isNegated))
            if not (checkFactExist(facts, fact) or checkFactExist(newFacts, fact)):
                log.t("******Get new fact {}".format(fact))
                newFacts.append(fact)
        # possible = getVariablePossibleValue(variable, term)
        # print("possible value for", term, possible)
        # for performance in possible:
        #     tuple = getVariableTuple(binding, term, performance)
        #     print("variable tuple is", tuple)
    logTime("\t\tThe {} time perform GMP".format(evaluateTimes))
    return newFacts

def checkConstraint(dict, cons, verbose=True):
    if verbose:
        log.trace("operator is {}".format(cons))
    if isLowerCase(cons.termX):
        x = cons.termX
    else:
        if isinstance(dict[cons.termX], set):
            x = list(dict[cons.termX])[0]
        else:
            x = dict[cons.termX]
    if isLowerCase(cons.termY):
        y = cons.termY
    else:
        if isinstance(dict[cons.termY], set):
            y = list(dict[cons.termY])[0]
        else:
            y = dict[cons.termY]
    if verbose:
        log.debug("x:{}, y:{}".format(x, y))
    if x and y:
        operator = cons.operator
        if operator == ">=":
            return x >= y
        elif operator == "<=":
            return x <= y
        elif operator == ">":
            return x > y
        elif operator == "<":
            return x < y
        elif "!" in operator:
            return x != y
        elif operator == "==" or operator == "=":
            return x == y
        else:
            return False

def evaluateBuiltInPredicate(dict, builtin, verbose=True):
    # X==Y, can precess directly, <=, >= >, < need the variable ground
    # builtInBody = []
    if verbose:
        if len(builtin) > 0:
            log.t("derive built-ins, value {}, builtin {}".format(dict, builtin))
    for body in builtin:
        if body.type == 'constraint':
            # builtInBody.append(body)
            if not checkConstraint(dict, body, verbose):
                if verbose:
                    log.t("{} does not satisfy built-ins".format(dict))
                return False
    return True

def checkFactExist(facts, fact):
    for fs in facts:
        if fs.fact == fact.fact:
            return True
    return False
    # return fact in facts

# get variable tuple for each goal
# p1: fact, p2:body
def unifyBinding(p1, p2, binding, facts):
    global evaluateTimes
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
        if not i[0].isupper():
            return False
    return True

def isLowerCaseList(list):
    for i in list:
        if i[0].isupper():
            return False
    return True

def isUpperCase(c):
    return c[0].isupper()

def isLowerCase(c):
    return not c[0].isupper()

#get the relative facts
def getFactsByPredicate(facts, name, ruleIndex=None, bodyIndex=None, termLength=None):
    if ruleIndex and bodyIndex:
        if termLength:
            return [x for x in facts if not ("{}.{}".format(ruleIndex, bodyIndex)) in x.record and x is not None and x.fact.predicate == name and len(x.fact.terms) == termLength]
        else:
            return [x for x in facts if not ("{}.{}".format(ruleIndex, bodyIndex)) in x.record and x is not None and x.fact.predicate == name]
    else:
        if termLength:
            return [x for x in facts if x is not None and x.fact.predicate == name and len(x.fact.terms) == termLength]
        else:
            return [x for x in facts if x is not None and x.fact.predicate == name]

if __name__ == '__main__':
    # if len(sys.argv) != 2:
    #     print('Usage: python datalog.py datalog.cdl')
    #     sys.exit(-1)
    start = time.time()
    main(sys.argv)
    Parser.yacc.out.close()
    log.info("Total time: {} seconds".format(time.time()-start))
    if args.command:
        while True:
            args.verbose = False
            try:
                s = input('query > ')
                if s == 'q':
                    break
            except EOFError:
                break
            if not s: continue
            query = []
            Parser.yacc.errorList.clear()
            parser = Parser.yacc.parser
            program = parser.parse(s)
            if not len(Parser.yacc.errorList) == 0:
                continue
            for p in program:
                if p.type == 'query':
                    query.append(p)
            queryFromFacts(query, facts)