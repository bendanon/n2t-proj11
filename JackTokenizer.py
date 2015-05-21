import sys


class TokenType:
    KEYWORD = 1
    SYMBOL = 2
    IDENTIFIER = 3
    INT_CONST = 4
    STRING_CONST = 5

Keywords = ['class', 'method', 'function', 'constructor', 'int', 'boolean',
            'char', 'void', 'var', 'static', 'field', 'let', 'do', 'if',
            'else', 'while', 'return', 'true', 'false', 'null', 'this']

Symbols = ['{', '}', '(', ')', '[', ']', '.', ',', ';', '+',
           '-', '*', '/', '&', '|', '<', '>', '=', '~']


class Tokenizer(object):

    def __init__(self, filePath):
        """
        Opens the input file and get ready to tokenize it.
        """
        self.file = open(filePath)
        self.current_token = None
        self.current_token_type = None

        self.next_token = None
        self.next_token_type = None
        self.readNextToken()

    def hasMoreTokens(self):
        """
        Do we have more tokens in the input?
        """
        return self.next_token is not None

    def advance(self):
        """
        Gets the next token from the input and makes it the current
        token. This method should only be called if hasMoreTokens()
        is true. Initially there is no current token.
        """
        if not self.hasMoreTokens():
            raise "hasMoreTokens() is false."
        self.current_token = self.next_token
        self.current_token_type = self.next_token_type
        self.readNextToken()

    def tokenType(self):
        """
        Returns the type of the current token.
        """
        return self.current_token_type

    def keyword(self):
        """
        Returns the keyword which is the current token. Should be
        called only when tokenType() is KEYWORD.
        """
        if self.tokenType() is not TokenType.KEYWORD:
            raise "tokenType() is not KEYWORD"
        return self.current_token

    def symbol(self):
        """
        Returns the character which is the current token. Should
        be called only when tokenType() is SYMBOL.
        """
        if self.tokenType() is not TokenType.SYMBOL:
            raise "tokenType() is not SYMBOL"
        return self.replaceUnsafeXmlSafeChars(self.current_token)

    def identifier(self):
        """
        Returns the identifier which is the current token. Should
        be called only when tokenType() is IDENTIFIER.
        """
        if self.tokenType() is not TokenType.IDENTIFIER:
            raise "tokenType() is not IDENTIFIER"
        return self.current_token

    def intVal(self):
        """
        Returns the integer value which is the current token.
        Should be called only when tokenType() is INT_CONST.
        """
        if self.tokenType() is not TokenType.INT_CONST:
            raise "tokenType() is not INT_CONST"
        return int(self.current_token)

    def stringVal(self):
        """
        Returns the string value which is the current token. Should
        be called only when tokenType() is STRING_CONST.
        """
        if self.tokenType() is not TokenType.STRING_CONST:
            raise "tokenType() is not STRING_CONST"
        return self.replaceUnsafeXmlSafeChars(self.current_token)

    def readNextToken(self):
        self.readNullCharacters()

        c = self.peekChar()

        if c == '':  # EOF
            self.next_token = None
            self.next_token_type = None
            self.file.close()
            return

        if c == '"':  # String constant
            self.next_token = self.readStringConstant()
            self.next_token_type = TokenType.STRING_CONST
            return

        if c == '/':  # Comment or symbol
            c = self.readChar()
            if (self.peekChar() in ['/', '*']):  # Comment
                self.readComment()
                self.readNextToken()
                return
            else:  # Symbol
                self.next_token = c
                self.next_token_type = TokenType.SYMBOL
                return

        if c in Symbols:  # Definitely symbol
            self.next_token = self.readChar()
            self.next_token_type = TokenType.SYMBOL
            return

        if c.isdigit():  # Integer constant
            self.next_token = self.readIntegerConstant()
            self.next_token_type = TokenType.INT_CONST
            return

        if (c.isalpha() or (c == '_')):
            self.next_token = self.readKeywordOfIdentifier()
            if self.next_token in Keywords:
                self.next_token_type = TokenType.KEYWORD
            else:
                self.next_token_type = TokenType.IDENTIFIER
            return

        raise "Bad character"

    def readComment(self):
        #  One '/' already read
        c = self.readChar()
        if (c == '/'):  # Single line comment
            while (self.readChar() not in ['\r', '\n']):
                pass
        elif (c == '*'):  # Multi-line comment
            first = self.readChar()
            second = self.readChar()
            while not (first == '*' and second == '/'):
                first = second
                second = self.readChar()
                if second == '':
                    raise "Error reading comment: reached EOF"
        else:
            raise "Error reading comment."

    def readStringConstant(self):
        string = ''
        self.readChar()
        while self.peekChar() not in ['"', '\n']:
            string += self.readChar()
        c = self.readChar()
        if c == '\n':
            raise "new-line is not a legal string character"
        return string

    def readIntegerConstant(self):
        int_string = ''
        while self.peekChar().isdigit():
            int_string += self.readChar()
        if int(int_string) > 32767:
            raise "Integer out of bounds"
        return int_string

    def readKeywordOfIdentifier(self):
        def isIdentifierChar(c):
            return c.isdigit() or c.isalpha() or c == '_'

        temp_string = ''
        while isIdentifierChar(self.peekChar()):
            temp_string += self.readChar()

        return temp_string

    def readNullCharacters(self):
        while (self.peekChar() in [' ', '\r', '\n', '\t']):
            self.readChar()

    def readChar(self):
        return self.file.read(1)

    def peekChar(self):
        pos = self.file.tell()
        char = self.file.read(1)
        self.file.seek(pos)
        return char

    def replaceUnsafeXmlSafeChars(self, s):
        return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def main(args):
    if len(args) != 1:
        print "Usage: (python) JackTokenizer.py <inputPath>"
        return

    inputPath = args[0]

    tokenizer = Tokenizer(inputPath)
    print "<tokens>"

    while (tokenizer.hasMoreTokens()):
        tokenizer.advance()
        t = tokenizer.tokenType()

        if t is TokenType.KEYWORD:
            print "<keyword> {} </keyword>".format(tokenizer.keyword())
            continue

        if t is TokenType.SYMBOL:
            print "<symbol> {} </symbol>".format(tokenizer.symbol())
            continue

        if t is TokenType.IDENTIFIER:
            print "<identifier> {} </identifier>".format(tokenizer.identifier())
            continue

        if t is TokenType.INT_CONST:
            print "<integerConstant> {} </integerConstant>".format(tokenizer.intVal())
            continue

        if t is TokenType.STRING_CONST:
            print "<stringConstant> {} </stringConstant>".format(tokenizer.stringVal())
            continue

    print "</tokens>"

if __name__ == '__main__':
    main(sys.argv[1:])
