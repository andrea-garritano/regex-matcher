# This is a very simple recursive descent parser that parses a simple
# regular expression dialect into an object hierarchy (the parse tree
# of the regular expression).
#
# This is the basic CFG that is parsed:
#
#  S -> A | C | K
#  K -> S*
#  A -> (S+S)
#  C -> (SS)
#  L -> a | b | c | d | ... | LL
#
# This grammar is *mostly* correct, but there are some shortcuts that
# are supported in how expressions are parsed. The biggest one is that
# the LAST character in a multi-character literal concatenation can be
# STARRED. This is just to support expressions like: ab*, ababc*, etc.
#
# Note also that the grammar is extremely picky about expressions
# being fully-parenthesized. Some examples:
#
# NOT VALID:
#  (a+b)*a*     (the concatenation is not parenthesized)
#  (a+b+c)      (one alternation is not parenthesized)
#  (a+b)+c      (one alternation still not parenthesized)
#
# VALID:
#  ((a+b)*a*)
#  ((a+b)+c)
#
# The main parsing function to use is parseRE(s), where 's' is the
# string containing the regular expression to be parsed. On success,
# it will return the parse tree of the regular expression.
#
# The parser implemented here is extremely hacky and hasn't been
# tested much. There is some minumal syntax checking and error
# catching, but don't rely on it. So have fun, but don't hurt
# yourself...
#
# Andrew D. Bagdanov
# 17 July 2016
#

# Import string module to test for literals.
import string

# Import sys module to grab the input from user
import sys

###
### Here are the classes used to build the parse tree representing a
### regular expression.
###

# Class to represent a single TERMINAL symbol: a, b, c, d, ...
class Literal:
    def __init__(self, c):
        self.char = c

# Class to represent an ALTERNATION: (a+b), ((abc)* + d), ...
class Alternation:
    def __init__(self, left, right):
        self.left = left
        self.right = right

# Class to represent a CONCATENATION: abc, ((ab)(a+b)), ...
class Concatenation:
    def __init__(self, left, right):
        self.left = left
        self.right = right

# Class to represent a KLEENE STAR: a*, (a+b)*, ...
class Star:
    def __init__(self, rexp):
        self.rexp = rexp

###
### The main parser function.
###

# This parses a LITERAL. For convenience in notation, a LITERAL can be
# one or more lowercase characters (note how string.ascii_lowercase is
# used to check validity. If there is more than one character in the
# literal, it is parsed as a CONCATENATION of multiple LITERALS.
def parseLiteral(s):
    if (len(s) > 1) and (s[0] in string.ascii_lowercase) and (s[1] in string.ascii_lowercase):
        (r, c) = parseLiteral(s[1:])
        return (r, Concatenation(Literal(s[0]), c))
    elif s[0] in string.ascii_lowercase:
        # This is a messy hack to handle the case of a '*' on the last
        # character of a literal.
        if len(s) > 1 and s[1] == '*':
            return (s[2:], Star(Literal(s[0])))
        else:
            return (s[1:], Literal(s[0]))
    else:
        raise ValueError('Parse error! Expected LITERAL, got: {}'.format(s))

# This is a simple function that checks if a parsed regular expression
# is followed by a '*' and then simply inserts the Star() object
# around the return value.
def parseStar(rest, ret):
    if (len(rest) > 0) and rest[0] == '*':
        return (rest[1:], Star(ret))
    else:
        return (rest, ret)

# The main parsing function. There are lots of messy special cases in
# here that are handled (like the closing parens, the STAR guard, and
# multiple-character literals. This code is probably hazzardous to
# your health.
def parseS(s):
    # First check if we're parsing a *compound* (Alt or Conc).
    if s[0] == '(':
        # Parse the first element of the compound.
        (rest, l) = parseS(s[1:])

        # Now test if we're an ALTERNATION.
        if rest[0] == '+':
            (rest, r) = parseS(rest[1:])
            if (len(rest) > 0) and rest[0] == ')':
                return parseStar(rest[1:], Alternation(l, r))
            else:
                raise ValueError('Parse error! Expected CLOSE PAREN, got: {}'.format(s))

        # Otherwise, assume we're in a CONCATENATION and hope for the best.
        else:
            (rest, l) = parseS(s[1:])
            if (len(rest) > 0) and rest[0] == ')':
                return parseStar(rest[1:], l)
            else:
                (rest, r) = parseS(rest)
            if (len(rest) > 0) and rest[0] == ')':
                return parseStar(rest[1:], Concatenation(l, r))
            else:
                raise ValueError('Parse error! Expected CLOSE PAREN, got: {}'.format(s))

    # Otherwise, we're in a LITERAL.
    elif s[0] in string.ascii_lowercase:
        return parseLiteral(s)

    else:
        raise ValueError('Parse error! Cant do anything with: {}'.format(s))

# This is the function you should call to parse the regular expression.
def parseRE(s):
    (rest, p) = parseS(s)
    if len(rest) > 0:
        raise ValueError('Parse error! Unparsed input: {}'.format(rest))
    else:
        return p

def matcher(cur_node, stringList):
    if isinstance(cur_node, Literal):
        i = 0
        copyStringList = stringList[:]
        control = False
        newCopyStringList = []
        while i < len(copyStringList):
            myString = copyStringList[i]
            if (len(myString) > 0) and (cur_node.char == myString[0]):
                control = True
                newCopyStringList.append(myString[1:])
            i += 1
        return newCopyStringList, control


    if isinstance(cur_node, Alternation):
        copyStringList = stringList[:]
        testedLeft, checkLeft = matcher(cur_node.left, copyStringList)
        copyTestedLeft = testedLeft[:]
        testedRight, checkRight = matcher(cur_node.right, copyStringList)
        copyTestedRight = testedRight[:]

        # Unisce le due liste e le ordina in base ala lunghezza
        copyStringList = copyTestedLeft + copyTestedRight
        copyStringList = list(set(copyStringList))
        copyStringList.sort(key=len)
        copyStringList = list(reversed(copyStringList))
        return copyStringList, checkLeft or checkRight

    if isinstance(cur_node, Concatenation):
        copyStringList = stringList[:]
        testedLeft, checkLeft = matcher(cur_node.left, copyStringList)
        copyTestedLeft = testedLeft[:]
        testedRight, checkRight = matcher(cur_node.right, copyTestedLeft)
        copyTestedRight = testedRight[:]

        copyTestedRight = list(set(copyTestedRight))
        copyTestedRight.sort(key=len)
        copyTestedRight = list(reversed(copyTestedRight))
        return copyTestedRight, checkLeft and checkRight

    if isinstance(cur_node, Star):
        copyStringList = stringList[:]
        check=True;
        if len(copyStringList)>0:
            i = len(copyStringList[0])
        else:
            i=0
        while check and i>0:
            newCopyStringList, check = matcher(cur_node.rexp, copyStringList)
            if check == True:
                copyStringList.append(newCopyStringList[-1])
                if newCopyStringList[-1] == "":
                    check = False
            i +=-1
        return copyStringList, True



def matchString(root, myString):
    stringList = [myString]
    (rest, check) = matcher(root, stringList)
    #print len(rest)
    i = 0
    matched = False
    while i < len(rest):
        if rest[i]=="":
            matched = True
        i += 1
    if (matched == False):
        return False
        #raise ValueError('Matcher error! Unmatched input: {}'.format(rest))
    else:
        return True

if __name__ == '__main__':
    while (True):
        regex = raw_input("Regex: ")
        root = parseRE(regex)
        if len(sys.argv) > 1:
            with open(sys.argv[1], 'r') as file:
                for line in file:
                    line = line.strip('\n')
                    print line, "- Matched:", matchString(root, line)
        else:
            print "No input file"
            #print root, "Matched:", matchString(root, toTest)
        print "\n"

    #root = parseRE('(b(((aa+b)(a+b))b))')
    #root = parseRE('(((a+b)*)b)')
    #root = parseRE('(a+((b+c)*))')
    #root = parseRE('(((aa)*)(bb)*)');
    #root = parseRE('((((((((((((((((((((((((((q+w)+e)+r)+t)+y)+u)+i)+o)+p)+a)+s)+d)+f)+g)+h)+j)+k)+l)+z)+x)+c)+v)+b)+n)+m)*)')

    '''
    #Print the tree
    stack = [root]
    while stack:
        cur_node = stack[0]
        stack = stack[1:]
        if isinstance(cur_node, Literal):
            print "Literal:", cur_node.char
            stack.insert(0, cur_node.char)
        if isinstance(cur_node, Alternation):
            print "Alternation"
            stack.insert(0, cur_node.left)
            stack.insert(1, cur_node.right)
        if isinstance(cur_node, Concatenation):
            print "Concatenation"
            stack.insert(0, cur_node.left)
            stack.insert(1, cur_node.right)
        if isinstance(cur_node, Star):
            print "Star"
            stack.insert(0, cur_node.rexp)
    '''

    #print parseRE('(aa+b)*')
    #print parseRE('((a+b)+c)')
    #print parseRE('(a+(b+c))')
    #print parseRE('((a+b)*(c+d)*)')
    #print parseRE('(((aa+ab)+ba)+bb)*')
    #print parseRE('(((a+b)*ccc)(a+b)*)')





