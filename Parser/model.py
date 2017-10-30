class Rule(object):
    def __init__(self, head={}, body={}, type="rule"):
        self.head = head 
        self.body = body
        self.type = type
    def __repr__(self):
        return "%r" % (self.__dict__)
     
class Query(object):
    def __init__(self, query, type = "query"):
        self.query = query
        self.type = type
    def __repr__(self):
        return "%r" % (self.__dict__)

class Fact(object):
    def __init__(self, fact, type = "fact"):
        self.fact = fact
        self.type = type

    def __repr__(self):
        return "%r" % (self.__dict__)

class Predicate(object):
    def __init__(self, name="", terms=[], isNegated=""):
        self.predicate = name
        self.terms = terms
        self.isNegated = isNegated
    def __repr__(self):
        return "%r" % (self.__dict__)
   
   
class Constraint(object):
    def __init__(self, termX="", operator="", termY=""):
        self.termX = termX
        self.operator = operator
        self.termY = termY 
    def __repr__(self):
        return "%r" % (self.__dict__)