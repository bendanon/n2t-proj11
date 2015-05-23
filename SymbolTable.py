import sys

class Categories:
    VAR = 0,
    ARGUMENT = 1,
    STATIC = 2,
    FIELD = 3,
    CLASS = 4,
    SUBROUTINE = 5,
    NONE = 6

conversion = {"var" : Categories.VAR, "argument" : Categories.ARGUMENT ,"static" : Categories.STATIC, "field" : Categories.FIELD , "class" : Categories.CLASS, "function" : Categories.SUBROUTINE, "method" : Categories.SUBROUTINE, "constructor" : Categories.SUBROUTINE}

conversion_mirror = {Categories.VAR : "var", Categories.ARGUMENT : "argument" , Categories.STATIC : "static", Categories.FIELD : "field", Categories.CLASS : "class",Categories.SUBROUTINE : "subroutine"}

indexed = {Categories.VAR : "local" , Categories.ARGUMENT : "argument", Categories.STATIC : "static", Categories.FIELD : "this"}

class CategoryUtils:

    @staticmethod    
    def FromString(categoryStr):
        if categoryStr in conversion.keys():
            return conversion[categoryStr]
        else:
            return None
    @staticmethod
    def ToString(category):
        if category in conversion_mirror.keys():
            return conversion_mirror[category]
        else:
            return None

    @staticmethod
    def IsIndexed(category):
        return category in indexed.keys()

    @staticmethod
    def BelongsInSymbolTable(keyword):
        return keyword in conversion.keys()

    @staticmethod
    def GetSegment(category):        
        return indexed[category]

class SymbolTableEntry(object):
    
    def __init__(self):
        self.name = None
        self.category = Categories.NONE
        self.index = -1
        self.segment = None
        self.type = None
    
    def SetCategory(self, categoryStr):
        self.category = CategoryUtils.FromString(categoryStr)
        if CategoryUtils.IsIndexed(self.category):
            self.segment = CategoryUtils.GetSegment(self.category)
        
    def SetName(self, name):
        self.name = name

class SymbolTable(object):

    def __init__(self):
        self.SymbolMap = {}
        self.indexList = [0, 0, 0, 0]

    def InsertEntry(self, entry):
        if CategoryUtils.IsIndexed(entry.category):
            entry.index = self.indexList[entry.category[0]]
            self.indexList[entry.category[0]] += 1

        self.SymbolMap[entry.name] = entry

    def SymbolIndex(self, name):
        return self.SymbolMap[name].index

    def GetEntry(self, name):   
        if name in self.SymbolMap.keys():
            return self.SymbolMap[name]
        else:
            return None

def main():
    st = SymbolTable([0,0,0,0])
    st.InsertSymbol("var", "name1")
    st.InsertSymbol("var", "name2")
    print "index of name1 is " + str(st.SymbolIndex("name1")) + " should be 0"
    print "index of name2 is " + str(st.SymbolIndex("name2")) + " should be 1"
    st.InsertSymbol("argument", "name3")
    st.InsertSymbol("argument", "name4")
    print "index of name3 is " + str(st.SymbolIndex("name3")) + " should be 0"
    print "index of name4 is " + str(st.SymbolIndex("name4")) + " should be 1"
    st.InsertSymbol("class", "name5")
    st.InsertSymbol("argument", "name6")
    st.InsertSymbol("subroutine", "name7")
    print "index of name5 is " + str(st.SymbolIndex("name5")) + " should be -1"
    print "index of name6 is " + str(st.SymbolIndex("name6")) + " should be 2"
    print "index of name6 is " + str(st.SymbolIndex("name7")) + " should be -1"
        
if __name__ == '__main__':
    main()



