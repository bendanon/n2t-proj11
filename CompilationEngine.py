from JackTokenizer import TokenType, Tokenizer
import sys


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


class CompilationEngine:
    def __init__(self, inputPath, outputPath):
        self.tokenizer = Tokenizer(inputPath)
        self.outputFile = open(outputPath, 'w')
        self.tokenizer.advance()
        self.indentLevel = 0

    def CompileClass(self):
        """
        Compiles a complete class.
        """
        self.EnterScope("class")

        self.ConsumeKeyword([Keyword.CLASS])
        self.ConsumeIdentifier()  # className
        self.ConsumeSymbol('{')

        while (self.IsKeyword([Keyword.STATIC, Keyword.FIELD])):
            self.CompileClassVarDec()

        # subroutineDec*
        while (self.IsKeyword([Keyword.CONSTRUCTOR, Keyword.FUNCTION,
                               Keyword.METHOD])):
            self.CompileSubroutine()

        self.ConsumeSymbol('}')

        self.ExitScope("class")
        self.outputFile.close()

    def CompileClassVarDec(self):
        """
        Compiles a static declaration or a field declaration.
        """
        self.EnterScope("classVarDec")

        self.ConsumeKeyword([Keyword.STATIC, Keyword.FIELD])
        self.ConsumeType()
        self.ConsumeIdentifier()  # varName

        while (self.IsSymbol([','])):
            self.ConsumeSymbol(',')
            self.ConsumeIdentifier()  # varName

        self.ConsumeSymbol(';')

        self.ExitScope("classVarDec")

    def CompileSubroutine(self):
        """
        Compiles a complete method, function, or constructor.
        """
        self.EnterScope("subroutineDec")

        self.ConsumeKeyword([Keyword.CONSTRUCTOR, Keyword.FUNCTION,
                             Keyword.METHOD])
        if (self.IsKeyword([Keyword.VOID])):
            self.ConsumeKeyword([Keyword.VOID])
        else:
            self.ConsumeType()

        self.ConsumeIdentifier()  # subroutineName

        self.ConsumeSymbol('(')
        self.CompileParameterList()
        self.ConsumeSymbol(')')

        self.CompileSubroutineBody()

        self.ExitScope("subroutineDec")

    def CompileSubroutineBody(self):
        self.EnterScope("subroutineBody")

        self.ConsumeSymbol('{')
        while (self.IsKeyword([Keyword.VAR])):
            self.CompileVarDec()
        self.CompileStatements()
        self.ConsumeSymbol('}')

        self.ExitScope("subroutineBody")

    def CompileParameterList(self):
        """
        Compiles a (possibly empty) parameter list,
        not including the enclosing "()".
        """
        self.EnterScope("parameterList")

        if (not self.IsSymbol([')'])):
            self.ConsumeType()
            self.ConsumeIdentifier()

        while(self.IsSymbol([','])):
            self.ConsumeSymbol(',')
            self.ConsumeType()
            self.ConsumeIdentifier()

        self.ExitScope("parameterList")

    def CompileVarDec(self):
        """
        Compiles a var declaration.
        """
        self.EnterScope("varDec")

        self.ConsumeKeyword([Keyword.VAR])
        self.ConsumeType()
        self.ConsumeIdentifier()  # varName
        while (self.IsSymbol([','])):
            self.ConsumeSymbol(',')
            self.ConsumeIdentifier()  # varName

        self.ConsumeSymbol(';')

        self.ExitScope("varDec")

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
        self.ConsumeIdentifier()
        if self.IsSymbol(['.']):
            self.ConsumeSymbol('.')
            self.ConsumeIdentifier()
        self.ConsumeSymbol('(')
        self.CompileExpressionList()
        self.ConsumeSymbol(')')
        self.ConsumeSymbol(';')

        self.ExitScope("doStatement")

    def CompileLet(self):
        """
        Compiles a let statement.
        """
        self.EnterScope("letStatement")

        self.ConsumeKeyword([Keyword.LET])
        self.ConsumeIdentifier()
        if self.IsSymbol(['[']):
            self.ConsumeSymbol('[')
            self.CompileExpression()
            self.ConsumeSymbol(']')
        self.ConsumeSymbol('=')
        self.CompileExpression()
        self.ConsumeSymbol(';')

        self.ExitScope("letStatement")

    def CompileWhile(self):
        """
        Compiles a while statement.
        """
        self.EnterScope("whileStatement")

        self.ConsumeKeyword([Keyword.WHILE])
        self.ConsumeSymbol('(')
        self.CompileExpression()
        self.ConsumeSymbol(')')

        self.ConsumeSymbol('{')
        self.CompileStatements()
        self.ConsumeSymbol('}')

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

        self.ExitScope("returnStatement")

    def CompileIf(self):
        """
        Compiles an if statement, possibly with a trailing
        else clause.
        """
        self.EnterScope("ifStatement")

        self.ConsumeKeyword([Keyword.IF])
        self.ConsumeSymbol('(')
        self.CompileExpression()
        self.ConsumeSymbol(')')

        self.ConsumeSymbol('{')
        self.CompileStatements()
        self.ConsumeSymbol('}')

        if self.IsKeyword([Keyword.ELSE]):
            self.ConsumeKeyword([Keyword.ELSE])
            self.ConsumeSymbol('{')
            self.CompileStatements()
            self.ConsumeSymbol('}')

        self.ExitScope("ifStatement")

    def CompileExpression(self):
        """
        Compiles an expression.
        """
        self.EnterScope("expression")

        op_symbols = ['+', '-', '*', '/', '&amp;', '|', "&lt;", "&gt;", '=']
        self.CompileTerm()
        while (self.IsSymbol(op_symbols)):
            self.ConsumeSymbol(self.tokenizer.symbol())
            self.CompileTerm()

        self.ExitScope("expression")

    def CompileTerm(self):
        """
        Compiles a term.
        """
        self.EnterScope("term")

        keyword_constants = [Keyword.TRUE, Keyword.FALSE, Keyword.NULL,
                             Keyword.THIS]
        unary_symbols = ['-', '~']

        if self.IsType(TokenType.INT_CONST):
            self.ConsumeIntegerConstant()

        elif self.IsType(TokenType.STRING_CONST):
            self.ConsumeStringConstant()

        elif self.IsKeyword(keyword_constants):
                self.ConsumeKeyword(keyword_constants)

        elif self.IsSymbol(['(']):
            self.ConsumeSymbol('(')
            self.CompileExpression()
            self.ConsumeSymbol(')')

        elif self.IsSymbol(unary_symbols):
            self.ConsumeSymbol(self.tokenizer.symbol())
            self.CompileTerm()
        else:
            self.ConsumeIdentifier()
            if self.IsSymbol(['[']):    # varName '[' expression ']'
                self.ConsumeSymbol('[')
                self.CompileExpression()
                self.ConsumeSymbol(']')
            elif self.IsSymbol(['(']):  # subroutineCall
                self.ConsumeSymbol('(')
                self.CompileExpressionList()
                self.ConsumeSymbol(')')
            elif self.IsSymbol(['.']):
                self.ConsumeSymbol('.')
                self.ConsumeIdentifier()
                self.ConsumeSymbol('(')
                self.CompileExpressionList()
                self.ConsumeSymbol(')')

        self.ExitScope("term")

    def CompileExpressionList(self):
        """
        Compiles a (possibly empty) comma-separated
        list of expressions.
        """
        self.EnterScope("expressionList")

        if not self.IsSymbol(')'):
            self.CompileExpression()

        while self.IsSymbol([',']):
            self.ConsumeSymbol(',')
            self.CompileExpression()

        self.ExitScope("expressionList")

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
            self.ConsumeIdentifier()
        else:
            self.ConsumeKeyword([Keyword.INT, Keyword.CHAR, Keyword.BOOLEAN])

    def ConsumeKeyword(self, keywordList):
        self.VerifyTokenType(TokenType.KEYWORD)
        actual = self.tokenizer.keyword()
        if actual not in keywordList:
            raise Exception("Expected keywords: {}, Actual: {}".
                            format(keywordList, actual))
        self.OutputTag("keyword", actual)
        if self.tokenizer.hasMoreTokens():
            self.tokenizer.advance()

    def ConsumeSymbol(self, symbol):
        self.VerifyTokenType(TokenType.SYMBOL)
        actual = self.tokenizer.symbol()
        if actual != symbol:
            raise Exception("Expected symbol: {}, Actual: {}".
                            format(symbol, actual))
        self.OutputTag("symbol", actual)
        if self.tokenizer.hasMoreTokens():
            self.tokenizer.advance()

    def ConsumeIntegerConstant(self):
        self.VerifyTokenType(TokenType.INT_CONST)
        self.OutputTag("integerConstant", self.tokenizer.intVal())
        if self.tokenizer.hasMoreTokens():
            self.tokenizer.advance()

    def ConsumeStringConstant(self):
        self.VerifyTokenType(TokenType.STRING_CONST)
        self.OutputTag("stringConstant", self.tokenizer.stringVal())
        if self.tokenizer.hasMoreTokens():
            self.tokenizer.advance()

    def ConsumeIdentifier(self):
        self.VerifyTokenType(TokenType.IDENTIFIER)
        self.OutputTag("identifier", self.tokenizer.identifier())
        if self.tokenizer.hasMoreTokens():
            self.tokenizer.advance()

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

    def OutputTag(self, tag, value):
        self.Output("<{}> {} </{}>".format(tag, value, tag))

    def Output(self, text):
        self.outputFile.write(("  " * self.indentLevel) + text + '\n')
        # print ("  " * self.indentLevel) + text


def main(args):
    if len(args) != 2:
        print "Usage: (python) CompilationEngine.py <inputPath> <outputPath>"
        return

    inputPath = args[0]
    outputPath = args[1]

    #inputPath = r"ArrayTest\Main.jack"; outputPath = r"ArrayTest\_Main.xml";
    #inputPath = r"Square\Main.jack"; outputPath = r"Square\_Main.xml";
    #inputPath = r"Square\Square.jack"; outputPath = r"Square\_Square.xml";
    #inputPath = r"Square\SquareGame.jack"; outputPath = r"Square\_SquareGame.xml"
    #inputPath = r"ExpressionlessSquare\Main.jack"; outputPath = r"ExpressionlessSquare\_Main.xml"
    #inputPath = r"ExpressionlessSquare\Square.jack"; outputPath = r"ExpressionlessSquare\_Square.xml"
    #inputPath = r"ExpressionlessSquare\SquareGame.jack"; outputPath = r"ExpressionlessSquare\_SquareGame.xml"

    engine = CompilationEngine(inputPath, outputPath)
    engine.CompileClass()

if __name__ == '__main__':
    main(sys.argv[1:])
