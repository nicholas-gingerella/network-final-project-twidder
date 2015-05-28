#enums
#example use:
#   Numbers = enum('STATE1','STATE2','STATE3')
#   Numbers.STATE1
#   0
#   Numbers.STATE2
#   1
#   ....
def enum(*sequential, **named):
  enums = dict(zip(sequential, range(len(sequential))), **named)
  return type('Enum', (), enums)

