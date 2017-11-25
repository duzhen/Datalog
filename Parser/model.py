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
        self.fact.type = type
        self.type = type
        self.record = set()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "%r" % (self.__dict__)

class Predicate(object):
    def __init__(self, name="", terms=[], isNegated=False, type = "predicate"):
        self.predicate = name
        self.terms = terms
        self.isNegated = isNegated
        self.type = type

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "%r" % (self.__dict__)
   
   
class Constraint(object):
    def __init__(self, termX="", operator="", termY="", type = "constraint"):
        self.termX = termX
        self.operator = operator
        self.termY = termY
        self.type = type
    def __repr__(self):
        return "%r" % (self.__dict__)