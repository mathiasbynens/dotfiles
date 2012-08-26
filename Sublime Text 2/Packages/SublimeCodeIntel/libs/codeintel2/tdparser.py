"""
A simple Top-Down Python expression parser.

This parser is based on the "Simple Top-Down Parsing in Python" article by
Fredrik Lundh (http://effbot.org/zone/simple-top-down-parsing.htm)

These materials could be useful for understanding ideas behind
the Top-Down approach:

 * Top Down Operator Precedence -- Douglas Crockford
   http://javascript.crockford.com/tdop/tdop.html

 * Top-Down operator precedence parsing -- Eli Benderski
   http://eli.thegreenplace.net/2010/01/02/top-down-operator-precedence-parsing/

 * Top down operator precedence -- Vaughan R. Pratt
   http://portal.acm.org/citation.cfm?doid=512927.512931

This implementation is a subject to change as it is very premature.
"""

import re
import cStringIO as sio
import tokenize

class ParseError(Exception): pass

type_map = {tokenize.NUMBER: "(literal)",
            tokenize.STRING: "(literal)",
            tokenize.OP: "(operator)",
            tokenize.NAME: "(name)"}

def gen_python_tokens(source):
    stream = tokenize.generate_tokens(sio.StringIO(source).readline)
    for token, value, begin, end in (t[:4] for t in stream):
        if token in type_map:
            yield type_map[token], value, begin, end
        elif token == tokenize.NL:
            continue
        elif token == tokenize.ENDMARKER:
            break
        else:
            raise ParseError("Syntax error at (%r) in text (%r) -- "
                             "unexpected token (%r)" % (value, source,
                                                        tokenize.tok_name[token]))
    yield "(end)", "(end)", None, None


class Symbol(object):
    id = None
    value = None
    first = second = third = None
    
    def __init__(self, parser, begin, end):
        self.parser = parser
        self.begin = begin
        self.end = end
    
    def nud(self):
        raise ParseError("Syntax error (%r)" % self)
        
    def led(self, left):
        raise ParseError("Unknown operator (%r)" % self)
        
    def py(self):
        if self.id[0] != "(":
            return self.id
        else:
            return self.value
        
    def __repr__(self):
        if self.id in ("(name)", "(literal)"):
            return "(%s %s)" % (self.id[1:-1], self.value)
        children = (str(item) for item in (self.first, self.second, self.third)
                              if item is not None)
        out = " ".join((self.id,) + tuple(children))
        return "(" + out + ")"
    
    @property
    def token(self):
        return self.parser.token
    
    @token.setter
    def token(self, token):
        self.parser.token = token
        
    @property
    def next(self):
        return self.parser.next
    
    @property
    def expression(self):
        return self.parser.expression

    @property
    def advance(self):
        return self.parser.advance
    
    
class Parser(object):
    token = None
    next = None
    
    def __init__(self, grammar=None):
        self.grammar = grammar or self.grammar
    
    def symbol(self, id, bp=0):
        return self.grammar.symbol(d, bp)

    def expression(self, rbp=0):
        t = self.token
        self.token = self.next()
        left = t.nud()
        while rbp < self.token.lbp:
            t = self.token
            self.token = self.next()
            left = t.led(left)
        return left

    def advance(self, id=None):
        if id and self.token.id != id:
            raise ParseError("Expected '%r', got '%r'" % (id, self.token))
        self.token = self.next()

    def gen_python_symbols(self, source):
        for id, value, begin, end in gen_python_tokens(source):
            if id == "(literal)":
                symbol = self.grammar.get_symbol(id)
                inst = symbol(self, begin, end)
                inst.value = value
            else:
                symbol = self.grammar.get_symbol(value)
                if symbol:
                    inst = symbol(self, begin, end)
                elif id == "(name)":
                    symbol = self.grammar.get_symbol(id)
                    inst = symbol(self, begin, end)
                    inst.value = value
                else:
                    raise ParseError("Unknown operator (%r)" % id)
            yield inst

    def parse(self, source):
        self.next = self.gen_python_symbols(source).next
        self.token = self.next()
        result = self.expression()
        if self.token.id != "(end)":
            raise ParseError("Expected end, got '%r'" % self.token)
        return result


class Grammar(object):
    symbol_table = {}
    
    def __init__(self):
        class proto(Symbol): pass
        self.proto = proto
    
    def common(self, fn):
        setattr(self.proto, fn.__name__, fn)
        return fn

    def method(self, id, bp=0):
        sym = self.symbol(id, bp)
        assert issubclass(sym, Symbol)
        def bind(fn):
            setattr(sym, fn.__name__, fn)
        return bind

    def symbol(self, id, bp=0):
        if id in self.symbol_table:
            sym = self.symbol_table[id]
        else:
            # can this be done with partials?
            class sym(self.proto): pass
            sym.__name__ = "symbol-" + id
            sym.id = id
            sym.lbp = bp
            self.symbol_table[id] = sym
        sym.lbp = max(bp, sym.lbp)
        return sym
    
    def get_symbol(self, id):
        return self.symbol_table.get(id)

    def infix(self, id, bp):
        @self.method(id, bp)
        def led(self, left):
            self.first = left
            self.second = self.expression(bp)
            return self
        
        @self.method(id, bp)
        def py(self):
            return "%s %s %s" % (self.first.py(), self.id, self.second.py())
    
    def prefix(self, id, bp):
        @self.method(id, bp)
        def nud(self):
            self.first = self.expression(bp)
            self.second = None
            return self
        
        @self.method(id, bp)
        def py(self):
            return "%s%s" % (self.id, self.first.py())
    
    
    def infix_r(self, id, bp):
        @self.method(id, bp)
        def led(self, left):
            self.first = left
            self.second = self.expression(bp-1)
            return self
        
        @self.method(id, bp)
        def py(self):
            return "%s %s %s" % (self.first.py(), self.value, self.second.py())
    
    def constant(self, id):
        @self.method(id)
        def nud(self):
            self.id = "(literal)"
            self.value = id
            return self


def arg_list_py(args):
    buf = []
    for name, value, type in args:
        if value:
            buf.append("%s=%s" % (name.py(), value.py()))
        else:
            buf.append(name.py())
    return ", ".join(buf)


def call_list_py(args):
    buf = []
    for name, value in args:
        value_py = value and value.py() or ''
        if name:
            if name.id in ("*", "**"):
                arg = name.id + value.py()
            else:
                arg = "%s=%s" % (name.id, value_py)
        else:
            arg = value_py
        buf.append(arg)
    return ", ".join(buf)


def py_expr_grammar():
    self = Grammar()
        
    self.symbol("lambda", 20)
    self.symbol(":", 10)
    
    self.symbol("if", 20)
    self.symbol("else")
    
    self.infix_r("or", 30)
    self.infix_r("and", 40)
    self.prefix("not", 50)
    
    self.infix("in", 60);
    self.infix("not", 60) # in, not in
    
    self.infix("is", 60) # is, is not
    
    self.infix("<", 60)
    self.infix("<=", 60)
    self.infix(">", 60)
    self.infix(">=", 60)
    self.infix("<>", 60)
    self.infix("!=", 60)
    self.infix("==", 60)
    
    self.infix("|", 70)
    self.infix("^", 80)
    self.infix("&", 90)
    
    self.infix("<<", 100)
    self.infix(">>", 100)
    
    self.infix("+", 110)
    self.infix("-", 110)
    
    self.infix("*", 120)
    self.infix("/", 120)
    self.infix("//", 120)
    self.infix("%", 120)
    
    self.prefix("-", 130)
    self.prefix("+", 130)
    self.prefix("~", 130)
    
    self.infix_r("**", 140)
    
    self.symbol(".", 150)
    
    self.symbol("[", 150)
    self.symbol("]")
    
    self.symbol("(", 150)
    self.symbol(")")
    self.symbol(",")
    self.symbol("=")
    
    self.symbol("{", 150)
    self.symbol("}")
    
    self.symbol("(literal)").nud = lambda self: self
    self.symbol("(name)").nud = lambda self: self
    self.symbol("(end)")
    
    self.constant("None")
    self.constant("True")
    self.constant("False")
        
    @self.method("*")
    def py(self):
        if self.first:
            return "%s %s %s" % (self.first.py(), self.id, self.second.py())
        else:
            return self.value
        
    @self.method("**")
    def py(self):
        if self.first:
            return "%s %s %s" % (self.first.py(), self.id, self.second.py())
        else:
            return self.value

    @self.method("(")
    def nud(self):
        self.first = []
        comma = False
        if self.token.id != ")":
            while 1:
                if self.token.id == ")":
                    break
                self.first.append(self.expression())
                if self.token.id == ",":
                    comma = True
                    self.advance(",")
                else:
                    break
        self.advance(")")
        if not self.first or comma:
            return self # tuple
        else:
            return self.first[0]

    @self.method("(")
    def led(self, left):
        self.first = left
        self.second = []
        if self.token.id != ")":
            while 1:
                name = None
                if self.token.id in ('*', '**'):
                    name = self.token
                    self.advance(self.token.id)
                    value = self.expression()
                else:
                    t = self.expression()
                    if self.token.id == "=":
                        if t.id != "(name)":
                            raise ParseError("Expected a name, got '%r'" % arg)
                        self.advance("=")
                        name = t
                        value = self.expression()
                    else:
                        value = t
                        
                self.second.append((name, value))
                if self.token.id != ",":
                    break
                self.advance(",")
        self.advance(")")
        self.id = "(call)"
        return self
    
    @self.method("(")
    def py(self):
        if self.second:
            return "%s(%s)" % (self.first.py(), call_list_py(self.second))
        else:
            return "(%s)" % ", ".join(i.py() for i in self.first)
            
    @self.method("if")
    def led(self, left):
        self.first = left
        self.second = self.expression()
        self.advance("else")
        self.third = self.expression()
        return self
    
    @self.method("if")
    def py(self):
        return "%s if %s else %s" % (self.first.py(),
                                     self.second.py(),
                                     self.third.py())
            
    @self.method(".")
    def led(self, left):
        if self.token.id != "(name)":
            ParseError("Expected an attribute name, got '%r'" % self.token)
        self.first = left
        self.second = self.token
        self.advance()
        return self
    
    @self.method(".")
    def py(self):
        return "%s.%s" % (self.first.py(), self.second.py())
            
    @self.method("[")
    def nud(self):
        self.first = []
        while self.token.id != "]":
            self.first.append(self.expression())
            if self.token.id == ",":
                self.advance(",")
            else:
                break
        self.advance("]")
        return self
    
    @self.method("[")
    def led(self, left):
        self.id = "(index)"
        self.first = left
        self.second = self.expression()
        self.advance("]")
        return self
    
    @self.method("[")
    def py(self):
        if self.second:
            return "%s[%s]" % (self.first,
                               ", ".join(i.py() for i in self.second))
        else:
            return "[%s]" % ", ".join(i.py() for i in self.first)
            
    @self.method("{")
    def nud(self):
        self.first = []
        while self.token.id != "}":
            self.first.append(self.expression())
            advance(":")
            self.first.append(self.expression())
            if token.id == ",":
                self.advance(",")
            else:
                break
        self.advance("}")
        return self
    
    @self.method("{")
    def py(self):
        return "{%s}" % (", ".join("%s: %s" % (i[0].py(), i[1].py())
                                   for i in self.first))
            
    @self.method("lambda")
    def nud(self):
        if self.token.id != ":":
            self.first = self.argument_list(in_lambda=True)
        else:
            self.first = []
        self.advance(":")
        self.second = self.expression()
        return self
    
    @self.method("lambda")
    def py(self):
        return "lambda %s: %s" % (arg_list_py(self.first), self.second.py())
        
    @self.method("not")
    def led(self, left):
        if self.token.id != "in":
            raise ParseError("Expected 'in', got '%r'" % self.token)
        self.advance()
        self.id = "not in"
        self.first = left
        self.second = self.expression(60)
        return self
    
    @self.method("is")
    def led(self, left):
        if self.token.id == "not":
            self.advance()
            self.id = "is not"
        self.first = left
        self.second = self.expression(60)
        return self

    @self.common
    def advance_name(self):
        if self.token.id != "(name)":
            ParseError("Expected an argument name, got '%r'" % self.token)
        t = self.token
        self.advance()
        return t
        
    @self.common
    def argument_list(self, in_lambda=False):
        arglist = []
        while 1:
            val = None
            type = None
            if self.token.id == "*":
                arg = self.token
                self.advance("*")
                if self.token.id == ",":
                    arg.value = "*"
                else:
                    arg = self.advance_name()
                    arg.value = "*" + arg.value
            elif self.token.id == "**":
                self.advance("**")
                arg = self.advance_name()
                arg.value = "**" + arg.value
            else:
                arg = self.advance_name()
                
                if self.token.id == "=":
                    self.advance("=")
                    val = self.expression()
                    
                if not in_lambda:
                    if self.token.id == ":":
                        self.advance(":")
                        type = self.expression()
                    
            arglist.append((arg, val, type))
                
            if self.token.id == ",":
                self.advance(",")
            else:
                break
        return arglist
        
    return self


class PyExprParser(Parser):
    grammar = py_expr_grammar()
    
    def parse_bare_arglist(self, source):
        self.next = self.gen_python_symbols(source.strip()).next
        self.token = self.next()
        arglist = self.token.argument_list()
        if self.token.id != "(end)":
            raise ParseError("Expected end, got '%r'" % self.token)
        return arglist


if __name__ == '__main__':
    parser = PyExprParser()
    res = parser.parse_bare_arglist("fsrc, fdst, length=16*1024")
    print res

