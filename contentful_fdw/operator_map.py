## Translates SQL operators into contentful operators

class unknownOperatorException(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)

def getOperatorFunction(opr):
  operatorFunctionMap = {
      '<':          '[lt]',
      '>':          '[gt]',
      '<=':         '[lte]',
      '>=':         '[gte]',
      '=':          '',
      '<>':         '[ne]',
      '!=':         '[ne]'
  }

  if opr not in operatorFunctionMap:
      raise unknownOperatorException("'%s' is not a supported operator." % opr)

  return operatorFunctionMap[opr]
