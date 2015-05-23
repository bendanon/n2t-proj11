from JackTokenizer import TokenType, Tokenizer
from SymbolTable import SymbolTable, CategoryUtils, SymbolTableEntry, Categories
import sys
import os

class Keyword:
    CLASS = 'class'
    METHOD = 'method'
    FUNCTION = 'function'
    CONSTRUCTOR = 'constructor'
    INT = 'int'
    BOOLEAN = 'boolean'
    CHAR = 'char'
    VOID = 'void'
    VAR = 'var'
    STATIC = 'static'
    FIELD = 'field'
    LET = 'let'
    DO = 'do'
    IF = 'if'
    ELSE = 'else'
    WHILE = 'while'
    RETURN = 'return'
    TRUE = 'true'
    FALSE = 'false'
    NULL = 'null'
    THIS = 'this'


op_symbols = {'+' : 'add', '-' : 'sub', '*' : 'call Math.multiply 2', '/' : 'call Math.divide 2', '&amp;' : 'and' , '|' : 'or', "&lt;" : 'lt' , "&gt;" : 'gt', '=' : 'eq'}
unary_symbols = {'-' : 'neg', '~' : 'not'}

subroutine_types = [Keyword.CONSTRUCTOR, Keyword.FUNCTION, Keyword.METHOD]

class CompilationEngine:
    def __init__(self):
        self.symbolTables = []
        self.typeSizeMap = {"int" : 1, "bool" : 1, "char" : 1}
        self.uniqueLabelIndex = 0
    
    def SetClass(self, inputPath, outputPath):
        self.tokenizer = Tokenizer(inputPath)
        self.outputFile = open("{0}.xml".format(outputPath), 'w')
        self.codeFile = open(outputPath, 'w')
        self.tokenizer.advance()
        self.indentLevel = 0
        
        self.currentSymbolTableEntry = None
        self.currentClassName = None
        self.currentSubName = None

    def GenerateUniqueLabel(self):
        self.uniqueLabelIndex+=1
        return "pfl{0}".format(self.uniqueLabelIndex-1)

    def CompileClass(self):
        """
        Compiles a complete class.
        """
        self.EnterScope("class")
        self.symbolTables.append(SymbolTable())

        self.ConsumeKeyword([Keyword.CLASS])
        self.ConsumeDeclaration("class", None)

        self.ConsumeSymbol('{')

        totalSize = 0
        while (self.IsKeyword([Keyword.STATIC, Keyword.FIELD])):
            totalSize += self.CompileClassVarDec()

        self.typeSizeMap[self.currentClassName] = totalSize

        # subroutineDec*
        while (self.IsKeyword(subroutine_types)):
            self.CompileSubroutine()

        self.ConsumeSymbol('}')

        self.symbolTables.pop()
        self.ExitScope("class")
        self.outputFile.close()

    def CompileClassVarDec(self):
        """
        Compiles a static declaration or a field declaration.
        """
        self.EnterScope("classVarDec")
        amount = 0
        category = self.tokenizer.keyword()
        self.ConsumeKeyword([Keyword.STATIC, Keyword.FIELD])        
        varType = self.ConsumeType()
        self.ConsumeDeclaration(category, varType)
        amount+=1
        while (self.IsSymbol([','])):
            self.ConsumeSymbol(',')
            self.ConsumeDeclaration(category, varType)
            amount+=1

        self.ConsumeSymbol(';')

        self.ExitScope("classVarDec")
        
        return self.typeSizeMap[varType]*amount

    def CompileSubroutine(self):
        """
        Compiles a complete method, function, or constructor.
        """
        self.EnterScope("subroutineDec")
        self.symbolTables.append(SymbolTable())

        subType = self.tokenizer.keyword()
        self.ConsumeKeyword([Keyword.CONSTRUCTOR, Keyword.FUNCTION,
                             Keyword.METHOD])
        if (self.IsKeyword([Keyword.VOID])):
            self.ConsumeKeyword([Keyword.VOID])
        else:
            self.ConsumeType()
        
        #The first param is converted to internal rep. the second is preserved
        self.ConsumeDeclaration(subType, subType)

        self.ConsumeSymbol('(')
        self.CompileParameterList()
        self.ConsumeSymbol(')')

        self.CompileSubroutineBody()

        self.symbolTables.pop()
        self.ExitScope("subroutineDec")

    def CompileSubroutineBody(self):
        self.EnterScope("subroutineBody")

        nVars=0
        self.ConsumeSymbol('{')
        while (self.IsKeyword([Keyword.VAR])):
            nVars+=self.CompileVarDec()

        self.WriteCode("function {0}.{1} {2}".format(self.currentClassName, self.currentSubName, str(nVars)))
        
        entry = self.SymbolTableLookup(self.currentSubName)

        if entry.type  == "constructor":
            self.WriteCode("push constant {0}".format(self.typeSizeMap[self.currentClassName]))
            self.WriteCode("call Memory.alloc 1")
            self.WriteCode("pop pointer 0")
        elif entry.type == "method":
            self.WriteCode("push argument 0")
            self.WriteCode("pop pointer 0")

        self.CompileStatements()
        self.ConsumeSymbol('}')

        self.ExitScope("subroutineBody")

    def ConsumeDeclaration(self, category, type):
        entry = SymbolTableEntry()
        entry.SetCategory(category)
        entry.name = self.ConsumeIdentifier()
        entry.type = type
        if category == "class":
            self.currentClassName = entry.name
        elif category in subroutine_types:
            self.currentSubName = entry.name

        self.GetTopSymbolTable().InsertEntry(entry)

    def CompileParameterList(self):
        """
        Compiles a (possibly empty) parameter list,
        not including the enclosing "()".
        """
        self.EnterScope("parameterList")
        nVars = 0

        if (not self.IsSymbol([')'])):
            varType = self.ConsumeType()
            self.ConsumeDeclaration("argument", varType)
            nVars+=1

        while(self.IsSymbol([','])):
            self.ConsumeSymbol(',')
            varType = self.ConsumeType()
            self.ConsumeDeclaration("argument", varType)
            nVars+=1

        self.ExitScope("parameterList")

        return nVars

    def CompileVarDec(self):
        """
        Compiles a var declaration.
        """
        self.EnterScope("varDec")
        nVars = 0
        self.ConsumeKeyword([Keyword.VAR])
        varType = self.ConsumeType()
        self.ConsumeDeclaration("var", varType)
        nVars+=1
        while (self.IsSymbol([','])):
            self.ConsumeSymbol(',') 
            self.ConsumeDeclaration("var", varType)
            nVars+=1
        
        self.ConsumeSymbol(';')

        self.ExitScope("varDec")

        return nVars

    def CompileStatements(self):
        """
        Compiles a sequence of statements, not including the
        enclosing "{}".
        """
        self.EnterScope("statements")

        while self.IsKeyword([Keyword.LET, Keyword.IF, Keyword.WHILE,
                              Keyword.DO, Keyword.RETURN]):
            if self.IsKeyword([Keyword.LET]):
                self.CompileLet()

            if self.IsKeyword([Keyword.IF]):
                self.CompileIf()

            if self.IsKeyword([Keyword.WHILE]):
                self.CompileWhile()

            if self.IsKeyword([Keyword.DO]):
                self.CompileDo()

            if self.IsKeyword([Keyword.RETURN]):
                self.CompileReturn()

        self.ExitScope("statements")

    def CompileDo(self):
        """
        Compiles a do statement.
        """
        self.EnterScope("doStatement")
        self.ConsumeKeyword([Keyword.DO])
        prefix = self.ConsumeIdentifier()
        calleeLocation = None
        subName = None
        
        if self.IsSymbol(['.']):
            self.ConsumeSymbol('.')
            entry = self.SymbolTableLookup(prefix)
            if entry is not None and entry.category != Categories.CLASS:
                calleeLocation = "{0} {1}".format(entry.segment, entry.index)
                prefix = entry.type
            postfix = self.ConsumeIdentifier()
            subName = "{0}.{1}".format(prefix ,postfix)
        else:
            subName = "{0}.{1}".format(self.currentClassName, prefix)
            calleeLocation = "pointer 0"
        
        nArgs = 0
        #This means we are calling an instance method, so we push it first
        if calleeLocation != None:
            self.WriteCode("push {0} //Pushing callee".format(calleeLocation))
            nArgs+=1
    
        self.ConsumeSymbol('(')
        nArgs += self.CompileExpressionList()
        self.ConsumeSymbol(')')
        self.ConsumeSymbol(';')
        
        self.WriteCode("call {0} {1}".format(subName, nArgs))

        self.ExitScope("doStatement")

    def CompileLet(self):
        """
        Compiles a let statement.
        """
        self.EnterScope("letStatement")

        self.ConsumeKeyword([Keyword.LET])
        varName = self.ConsumeIdentifier()
        if self.IsSymbol(['[']):
            self.ConsumeSymbol('[')
            self.CompileExpression()
            self.ConsumeSymbol(']')
        self.ConsumeSymbol('=')
        self.CompileExpression()
        self.ConsumeSymbol(';')
    
        self.ExitScope("letStatement")
        
        entry = self.SymbolTableLookup(varName)
        self.WriteCode("pop {0} {1}".format(entry.segment, entry.index))

    def CompileWhile(self):
        """
        Compiles a while statement.
        """
        self.EnterScope("whileStatement")

        self.ConsumeKeyword([Keyword.WHILE])
        L1 = self.GenerateUniqueLabel()
        L2 = self.GenerateUniqueLabel()
        
        #While entry point
        self.WriteCode("label {0}".format(L1))

        #while loop condition
        self.ConsumeSymbol('(')
        self.CompileExpression()
        self.ConsumeSymbol(')')
        
        #Jump to L2 if condition doesn't hold
        self.WriteCode("not")
        self.WriteCode("if-goto {0}".format(L2))

        #While loop logic
        self.ConsumeSymbol('{')
        self.CompileStatements()
        self.ConsumeSymbol('}')
        
        #Go back to L1 for another iteration
        self.WriteCode("goto {0}".format(L1))

        #While termination point
        self.WriteCode("label {0}".format(L2))

        self.ExitScope("whileStatement")

    def CompileReturn(self):
        """
        Compiles a return statement.
        """
        self.EnterScope("returnStatement")

        self.ConsumeKeyword([Keyword.RETURN])
        if not self.IsSymbol([';']):
            self.CompileExpression()
        self.ConsumeSymbol(';')

        self.WriteCode("return")

        self.ExitScope("returnStatement")

    def CompileIf(self):
        """
        Compiles an if statement, possibly with a trailing
        else clause.
        """
        self.EnterScope("ifStatement")

        self.ConsumeKeyword([Keyword.IF])
        L1 = self.GenerateUniqueLabel()
        L2 = self.GenerateUniqueLabel()
        
        #The if statement condition
        self.ConsumeSymbol('(')
        self.CompileExpression()
        self.ConsumeSymbol(')')
        
        #Jump to L1 if condition doesn't hold
        self.WriteCode("not")
        self.WriteCode("if-goto {0}".format(L1))

        self.ConsumeSymbol('{')
        self.CompileStatements()
        self.ConsumeSymbol('}')
        
        #Done
        self.WriteCode("goto {0}".format(L2))
        
        self.WriteCode("label {0}".format(L1))
        if self.IsKeyword([Keyword.ELSE]):
            self.ConsumeKeyword([Keyword.ELSE])
            self.ConsumeSymbol('{')
            self.CompileStatements()
            self.ConsumeSymbol('}')
        
        self.WriteCode("label {0}".format(L2))
            

        self.ExitScope("ifStatement")

    def CompileExpression(self):
        """
        Compiles an expression.
        """
        self.EnterScope("expression")

        self.CompileTerm()
        while (self.IsSymbol(op_symbols.keys())):
            op = self.ConsumeSymbol(self.tokenizer.symbol())
            self.CompileTerm()
            self.WriteCode(op_symbols[op])

        self.ExitScope("expression")
    
        
    def CompileTerm(self):
        """
        Compiles a term.
        """
        self.EnterScope("term")

        keyword_constants = [Keyword.TRUE, Keyword.FALSE, Keyword.NULL,
                             Keyword.THIS]
        termName = None
                
        if self.IsType(TokenType.INT_CONST):
            self.WriteCode("push constant {0}".format(self.ConsumeIntegerConstant()))

        elif self.IsType(TokenType.STRING_CONST):
            self.ConsumeStringConstant()

        elif self.IsKeyword(keyword_constants):
                keyword = self.ConsumeKeyword(keyword_constants)
                if keyword == "false":
                    self.WriteCode("push constant 0")
                elif keyword == "true":
                    self.WriteCode("push constant 0")
                    self.WriteCode("not")
                elif keyword == "this":
                    self.WriteCode("push pointer 0")

        elif self.IsSymbol(['(']):
            self.ConsumeSymbol('(')
            self.CompileExpression()
            self.ConsumeSymbol(')')

        elif self.IsSymbol(unary_symbols.keys()):
            symbol = self.ConsumeSymbol(self.tokenizer.symbol())
            self.CompileTerm()
            self.WriteCode(unary_symbols[symbol])
        else:
            termName = self.ConsumeIdentifier()
            entry = self.SymbolTableLookup(termName)
            if entry != None:
                if CategoryUtils.IsIndexed(entry.category):
                    self.WriteCode("push {0} {1} //{2}".format(CategoryUtils.GetSegment(entry.category), entry.index, termName))
            
            if self.IsSymbol(['[']):    # varName '[' expression ']'
                self.ConsumeSymbol('[')
                self.CompileExpression()
                self.ConsumeSymbol(']')
            elif self.IsSymbol(['(']):  # subroutineCall
                self.ConsumeSymbol('(')
                self.WriteCode("call {0} {1}".format(termName, self.CompileExpressionList()))
                self.ConsumeSymbol(')')
            elif self.IsSymbol(['.']):
                self.ConsumeSymbol('.')
                funcName = self.ConsumeIdentifier()
                self.ConsumeSymbol('(')
                self.WriteCode("call {0}.{1} {2}".format(termName, funcName, self.CompileExpressionList()))
                self.ConsumeSymbol(')')

        self.ExitScope("term")
        
        return termName

    def CompileExpressionList(self):
        """
        Compiles a (possibly empty) comma-separated
        list of expressions.
        """
        self.EnterScope("expressionList")
        nArgs = 0
        if not self.IsSymbol(')'):
            self.CompileExpression()
            nArgs+=1

        while self.IsSymbol([',']):
            self.ConsumeSymbol(',')
            self.CompileExpression()
            nArgs+=1

        self.ExitScope("expressionList")
    
        return nArgs

    def IsKeyword(self, keyword_list):
        return (self.IsType(TokenType.KEYWORD) and
                self.tokenizer.keyword() in keyword_list)

    def IsSymbol(self, symbol_list):
        return (self.IsType(TokenType.SYMBOL) and
                self.tokenizer.symbol() in symbol_list)

    def IsType(self, tokenType):
        return self.tokenizer.tokenType() == tokenType

    def ConsumeType(self):
        if (self.tokenizer.tokenType() == TokenType.IDENTIFIER):
            return self.ConsumeIdentifier()
        else:
            return self.ConsumeKeyword([Keyword.INT, Keyword.CHAR, Keyword.BOOLEAN])

    def ConsumeKeyword(self, keywordList):
        self.VerifyTokenType(TokenType.KEYWORD)
        actual = self.tokenizer.keyword()
        if actual not in keywordList:
            raise Exception("Expected keywords: {}, Actual: {}".
                            format(keywordList, actual))

        self.OutputTag("keyword", actual)
        if self.tokenizer.hasMoreTokens():
            self.tokenizer.advance()

        return actual

    def ConsumeSymbol(self, symbol):
        self.VerifyTokenType(TokenType.SYMBOL)
        actual = self.tokenizer.symbol()
        if actual != symbol:
            raise Exception("Expected symbol: {}, Actual: {}".
                            format(symbol, actual))
        self.OutputTag("symbol", actual)
        if self.tokenizer.hasMoreTokens():
            self.tokenizer.advance()
        
        return actual

    def ConsumeIntegerConstant(self):
        self.VerifyTokenType(TokenType.INT_CONST)
        actual = self.tokenizer.intVal()
        self.OutputTag("integerConstant", self.tokenizer.intVal())
        if self.tokenizer.hasMoreTokens():
            self.tokenizer.advance()
        
        return actual

    def ConsumeStringConstant(self):
        self.VerifyTokenType(TokenType.STRING_CONST)
        actual = self.tokenizer.stringVal()
        self.OutputTag("stringConstant", self.tokenizer.stringVal())
        if self.tokenizer.hasMoreTokens():
            self.tokenizer.advance()
        
        return actual
    '''
    def IsIdentifierBeingDefined(self):
        return self.currentSymbolTableEntry != None

    def FinishIdentifierDefinition(self):   
        self.currentSymbolTableEntry.SetName(self.tokenizer.identifier())
        self.GetTopSymbolTable().InsertEntry(self.currentSymbolTableEntry)
        self.currentSymbolTableEntry = None        
    
    def OutputIdentifierDetails(self):

        self.EnterScope("identifierDetails=========")

        self.OutputTag("beingDefined", str(self.IsIdentifierBeingDefined()))

        if self.IsIdentifierBeingDefined():
            self.FinishIdentifierDefinition()

        entry = self.SymbolTableLookup(self.tokenizer.identifier())

        if entry != None:
            if CategoryUtils.IsIndexed(entry.category):
                self.OutputTag("index", self.GetTopSymbolTable().SymbolIndex(entry.name))
            self.OutputTag("identifierCategory", CategoryUtils.ToString(entry.category))
        else:
            self.OutputTag("identifierCategory", "no definition present")
            self.OutputTag("index", "no definition present")

        self.ExitScope("identifierDetails=========")
    '''

    def ConsumeIdentifier(self):
        self.VerifyTokenType(TokenType.IDENTIFIER)
        actual = self.tokenizer.identifier()
        self.OutputTag("identifierName", self.tokenizer.identifier())        
        #self.OutputIdentifierDetails()
        if self.tokenizer.hasMoreTokens():
            self.tokenizer.advance()
        
        return actual

    def VerifyTokenType(self, tokenType):
        actual = self.tokenizer.tokenType()
        if actual != tokenType:
            raise Exception("Expected token type: {}, Actual: {}".
                            format(tokenType, actual))

    def EnterScope(self, name):
        self.Output("<{}>".format(name))
        self.indentLevel += 1

    def ExitScope(self, name):
        self.indentLevel -= 1
        self.Output("</{}>".format(name))

    def GetTopSymbolTable(self):
        if len(self.symbolTables) != 0:
            return self.symbolTables[len(self.symbolTables) - 1]
        else:
            return None

    def SymbolTableLookup(self, name):
        for st in reversed(self.symbolTables):
            entry = st.GetEntry(name)
            if entry != None:
                return entry
        return None

    def WriteCode(self, line):
        self.codeFile.write(line + '\n')

    def OutputTag(self, tag, value):
        self.Output("<{}> {} </{}>".format(tag, value, tag))

    def Output(self, text):
        self.outputFile.write(("  " * self.indentLevel) + text + '\n')
        # print ("  " * self.indentLevel) + text


def main(args):
    if len(args) != 1:
        print "Usage: (python) CompilationEngine.py <inputPath>"
        return

    jack_file_path = args[0]

    sources = []

    if not jack_file_path.endswith(".jack"):
        sources += [os.path.join(jack_file_path, source_file) for source_file
                    in os.listdir(jack_file_path) if source_file.endswith('.jack')]
    else:
        sources = [jack_file_path]

    engine = CompilationEngine()
    for source_file in sources:
        engine.SetClass(source_file, source_file.replace(".jack", ".vm"))
        engine.CompileClass()

    #engine.WriteCode("call Main.main 0")

if __name__ == '__main__':
    main(sys.argv[1:])
