#!/usr/bin/python3
r"""
    This is my humble intent of making a source code translator from Java to Python. It pretends to, having a Java file or
    a directory as an input, process all Java files it can find in that context for producing the Python equivalent source code files.

    Having into account that Python is a language where the whitespace and indenting is so important, I encourage the
    user to enter well indented and formatted Java code, following conventions and short lines.

    Thus, the task will be more manageable and the result will be the best.

    This is a tool made for my enjoyment. It can be also used for learning purposes
    and can ease even more the Python learning curve for those programmers coming
    from Java or similar languages (C, C++) even if this does not translate C or C++ code.
    It would be nice to do it in a future, though.
"""
# TODO - Ganar un minimo de eficiencia con un diccionario de matchs. Si el diccionario tiene un solo elemento, no buscar el resto de matchs
# TODO        Mas tarde podemos ver si el match es de tipo 'func', 'var', 'return', etc...
# TODO - Revisar el for: Buscar expresion mejorada para el for (dividirlo en dos o tres partes y resolverlo en base a operadores :,<=,<,>)
# TODO - Llamada / invocacion a metodo toString() u otros: Regex de algo que puede invocar un metodo es (?P<obj>(\w+(?P<parenth>\(.*?\))?\.)+)nombreMetodo\(\)

import re
import sys
import os
import getopt


PRIVACY_PREFIXES = {'private': '__', 'protected': '_', 'public': ''}
TAB = ' ' * 4

# In Java, a variable may be belong to one out of three kinds of privacy
EX_PRIV_MODIFS = r'(?P<priv>((\bpublic\b\s*|\bprivate\b\s*|\bprotected\b\s*))+)?'

# Modifiers for variables and functions
EX_VAR_MODIFS = r'(?P<vmodifs>\b(static\s*|final\s*|transient\s*|volatile\s*)+)?'
EX_FUN_MODIFS = r'(?P<fmodifs>\b(abstract\s*|static\s*|synchronized\s*|native\s*)+)?'
EX_CLASS_MODIFS = r'(?P<cmodifs>\b(abstract\s*|final\s*)+)?'

# Data type for a variable or the function returned value
EX_DATA_TYPE = r'\b(?P<basictype>\w+)(?P<gen><.*>)?(?P<bracks>(\[\])+)?\s*'

# The whole of variable or function declaration
EX_VAR_DECL = r'^(?P<space>\s*)' + EX_PRIV_MODIFS + EX_VAR_MODIFS + EX_DATA_TYPE + r'\b(?P<vname>\w+)\s*(?P<assign>=.*)?;'
EX_FUN_DECL = r'^(?P<space>\s*)<?[^=\.\(\)]*?>?\s*' + EX_PRIV_MODIFS + EX_FUN_MODIFS + EX_DATA_TYPE + r'\b(?P<fname>\w+)\((?P<fargs>.*)\)\s*\{?'
EX_CLASS_DECL = r'^(?P<space>\s*)' + EX_PRIV_MODIFS + EX_CLASS_MODIFS + r'class\s*(?P<className>\w+)(<.*>)?\s*(extends\s*(?P<parent>\w+)\s*)?(implements\s*(?P<ifaces>((\w+,?\s*)*\w+)))?\s*\{?'
EX_ENUM_DECL = r'(public)?\s*\benum\b\s*\b(?P<name>\w+)\b\s*\{?'
EX_BASIC_FOR = r'\bfor\b.*\(.*(\w+)\W*=\W*(\w+)\W*;.*<\W*([\w\.\(\)\[\]]+);.*\).*\{?.*(?P<nline>\r?\n?)\s*\{?'
EX_LT_FOR = r'\bfor\b.*\(.*(\w+)\W*=\W*(\w+)\W*;.*<=\W*([\w\.\(\)\[\]]+);.*\).*\{?.*(?P<nline>\r?\n?)\s*\{?'
EX_EACH_FOR = r'\bfor\b.*\(.*\b(\w+)\b.*:.*\b(\w+)\b.*\).*\{?.*(?P<nline>\r?\n?)\s*\{?'

# For better performance, we compile the patterns for declaration statements
PAT_VAR_DECL = re.compile(EX_VAR_DECL)
PAT_FUN_DECL = re.compile(EX_FUN_DECL)
PAT_CLASS_DECL = re.compile(EX_CLASS_DECL)

def twoBlankLines(l1, l2):
    """
    Detects if two lines are blank lines.
    This is for detecting two consecutive blank lines , so that one of them is redundant and superfluous
    :param l1: a text line
    :param l2: a text line
    :return: True if the two lines are blank and False otherwise
    """
    return re.search(r'^\s*$', l1) and re.search(r'^\s*$', l2)

def quickTask(line, regex, replacement, foutput, lastLine):
    """
    Optionally, makes a quick replacement task
    and detects a situation for returning True to continue the loop
    :param line: the line for processing
    :param regex: the regular expression to find or replace
    :param replacement: the replacement for the regex if found
    :param foutput: the output file to write to if there is a match
    :param lastLine: the last line processed, for not accumulating whitespace lines
    """
    match = re.search(regex, line)
    if match and line:
        line = re.sub(regex, replacement, line)
        if not twoBlankLines(lastLine, line):
            foutput.write(line)
        return line
    else:
        return None


def processArgs(args):
    """
    Process the arguments passed into a Java method removing modifiers and types
    :param args: the args to be processed
    """
    processed = ''
    if args and len(args):
        processed = args[:]
        # TODO Meter '*' en tipo array o List/arrayList
        processed = re.sub(r'(?P<dataType>((\b\w+\b[\[\]]*\s+)+))(?P<arg>\b\w+,?)', r'\g<arg>', processed)
    return processed


def prependSelf(args):
    """
    Inserts the 'self' word before arguments when doing OOP
    :param args: the args already processed for a python method
    :return: the args string with the 'self' inserted at beginning and an optional comma
    """
    self_ = 'self'
    if len(args):
        self_ += ', '
    args = self_ + args
    return args


def processVarLine(varMatch, replacements, className, interfaceName, line):
    """
    Processes an already detected Java variable assignment or declaration line and returns
    the text line processed to be an approximate Python source code line
    :param varMatch: the match object with the whitespace and variable name already captured
    :param replacements: a dictionary with the variables names in this source code and their python equivalents
    :param className: in OOP, the name of the current class
    :param interfaceName: in OOP, the name of the current interface
    :param line: the java source code line to be processed
    :return: the processed line
    """
    space = varMatch.group('space')
    vname = varMatch.group('vname')

    # We apply privacy prefixes to variable name if needed
    priv = varMatch.group('priv').rstrip() if varMatch.group('priv') else ''
    vname = PRIVACY_PREFIXES.get(priv, '') + vname

    vmodifs = varMatch.group('vmodifs')
    if vmodifs and 'static' in vmodifs:
        token = className or interfaceName
        replacements[varMatch.group('vname')] = token + '.' + vname
    else:
        replacements[varMatch.group('vname')] = vname

    # Non assignment statement
    if varMatch.group('bracks'):
        # If it's an array without assignment, we make the [] initialisation with the semicolon (;) ending
        line = re.sub(r'(.*?)((\[\])+)(?P<tail>[^=]*);', r'\1\g<tail> = '+varMatch.group('bracks')+';', line)
    else:
        # If it's not an array, first value will be None
        line = re.sub(r'^([^=]*);', r'\1 = None;', line)
    line = re.sub(PAT_VAR_DECL, space + vname + r' \g<assign>', line)
    return line


def processConsDefLine(className, consMatch, line):
    """
    Processes an already detected Java constructor declaration line and returns
    the text line processed to be an approximate Python source code line
    :param className: the class name
    :param consMatch: the match object with the args already captured
    :param line: the java source code line to be processed
    :return: the processed line
    """
    args = processArgs(consMatch.group('args'))
    space = consMatch.group('space')
    if className:
        args = prependSelf(args)
    line = re.sub(EX_PRIV_MODIFS + r'\b' + className + r'\b\((?P<args>.*)\)\s*\{?', r'def __init__(' + args + '):', line)
    line = os.linesep + line
    line += space + TAB + 'super().__init__()' + os.linesep
    return line


def processClassDefLine(classDefLine, line):
    """
    Processes an already detected Java class declaration line and returns
    the Java class name and the text line processed to be an approximate Python source code line
    :param classDefLine: the match object with the className captured
    :param line: the java source code line to be processed
    :return: a tuple with the className and the processed line (className,processedLine)
    """

    className = classDefLine.group('className')
    priv = classDefLine.group('priv')
    modifs = classDefLine.group('cmodifs') # abstract and/or final
    isAbstractClass = modifs and 'abstract' in modifs

    # We retrieve into a list the parent and ifaces groups from the re match
    ancestors = [classDefLine.group(groupName) for groupName in ['parent', 'ifaces'] if classDefLine.group(groupName)]
    if isAbstractClass:
        ancestors.append('metaclass=ABCMeta')
    if len(ancestors):
        ancestors = ', '.join(ancestors)
    else:
        ancestors = 'object'

    line = re.sub(PAT_CLASS_DECL, r'\g<space>class \g<className>('+ancestors+'):', line)
    # TODO - Usar class Abstract([metaclass=ABCMeta]|ABC) para las abstractas (Python +3 y +3.4 respectivamente)
    return className, line


def processFuncLine(funMatch, className, interfaceName, replacements, line):
    """
    Processes an already detected Java function declaration line and returns
    the text line processed to be an approximate Python source code line
    :param funMatch: the match object with whitespace, function name and modifiers already captured
    :param className: the class name, if any
    :param interfaceName: the interface name, if any
    :param replacements: a dictionary with the variables names in this source code and their python equivalents
    :param line:  the java source code line to be processed
    :return: the processed line
    """
    # TODO - Usar @abc.abstractmethod justo encima de los metodos abstractos?
    # TODO - Metodo toString en declaracion de metodo
    space = funMatch.group('space')
    priv = funMatch.group('priv').rstrip() if funMatch.group('priv') else ''
    fmodifs = funMatch.group('fmodifs').rstrip() if funMatch.group('fmodifs') else ''
    # ftype = funMatch.group('type')
    fname = PRIVACY_PREFIXES.get(priv, '') + funMatch.group('fname')
    if fname == 'toString':
        fname = '__str__'
    elif fname == 'equals':
        fname = '__eq__'
    else:
        replacements[funMatch.group('fname')] = fname
    args = processArgs(funMatch.group('fargs'))
    if className and 'static' not in fmodifs:
        args = prependSelf(args)
    line = re.sub(PAT_FUN_DECL, space + r'def ' + fname + r'(' + args + '):', line)
    line = re.sub(r'throws (\w*Exception,?\s*)+[ \t]*[{;]?', r'', line)
    if 'abstract' in fmodifs:
        line = space + '@abstractmethod' + os.linesep + line
    if 'static' in fmodifs:
        line = space + '@staticmethod' + os.linesep + line
    if interfaceName or 'abstract' in fmodifs:
        line += space + TAB + 'pass' + os.linesep
    return line

def processCondition(line):
    """
    Process all the condition operators and expressions contained within a line
    :param line: the java source code line to be processed
    :return: the processed line
    """
    result = re.sub(r'.equals\((.*)\)', r' == \1', line)
    result = re.sub(r'\s*!=\s*null', r'', result)
    result = re.sub(r'==\s*null', r'is None', result)
    result = re.sub(r'!\s*\(', r'not (', result)
    result = re.sub(r'!\s*\b(\w+)\b', r'not \1', result)
    result = re.sub(r'&&', 'and', result)
    result = re.sub(r'\|\|', 'or', result)
    result = re.sub(r'\b(\w+)\b[ \t]*==[ \t]*true', r'\1', result)
    result = re.sub(r'\b(\w+)\b[ \t]*==[ \t]*false', r'not \1', result)

    result = re.sub(r'\btrue\b', 'True', result)
    result = re.sub(r'\bfalse\b', 'False', result)
    return result

def transform(javaFile, pyFile):
    """
    With a java file as input produces a python file as output
    """
    quickTaskList = []
    quickTaskList.append((r'^(\s*)package', r'\1#package'))
    quickTaskList.append((r'^(\s*)import', r'\1#import'))

    # COMMENTS
    quickTaskList.append((r'^\s*}\s*\r?\n?$', os.linesep))
    quickTaskList.append((r'//', r'#'))
    # Block comment begin/end and block comment middle line with or without param
    quickTaskList.append((r'/\*\*?|\*/', r'"""'))
    quickTaskList.append((r'^(\s*)\*\s*@param', r'\1:param'))
    quickTaskList.append((r'^(\s*)\*\s*', r'\1'))

    with open(javaFile, 'r') as jFile, open(pyFile, 'w+') as pFile:
        # For variable names replacements
        replacements = {}
        className = None
        interfaceName = None
        mainMethod = False
        lastLine=''

        for oldLine in jFile:
            line = oldLine[:]

            '''
            Remove not leading whitespace
            Negative lookbehind (means no previous whitespace [ ])
            Negative lookahead (first thing in regex before consuming chars, not being at the line start)
            '''
            line = re.sub(r'\t', TAB, line)
            line = re.sub(r'(?<![ \t])(?!^)[ \t]+', r' ', line)
            line = line.rstrip()
            line = line + os.linesep

            lineResult = None
            # 1-Change replacements tasks which can be made and allow to go on with the next line if made
            for task in quickTaskList:
                lineResult = quickTask(line, task[0], task[1], pFile, lastLine)
                if lineResult:
                    break

            if lineResult:
                lastLine = lineResult
                continue

            classDefLine = re.search(PAT_CLASS_DECL, line)
            interfaceDefLine = re.search(r'\binterface (?P<name>\w+)', line)

            consMatch = None
            # For constructor line, we check for this className, but not in an instance creation
            if className and not re.search(r'\bnew[ \t]*', line):
                consMatch = re.search(r'(?P<space>[ \t]*)' + EX_PRIV_MODIFS + r'\b' + className + r'\b\((?P<args>.*)\)\s*\{?', line)

            returnMatch = re.search(r'\breturn\b .*;', line)
            throwMatch = re.search(r'\bthrow\b .*;', line)
            enumMatch = re.search(EX_ENUM_DECL, line)
            varMatch = re.search(PAT_VAR_DECL, line)
            funMatch = re.search(PAT_FUN_DECL, line)

            # Removing annotations
            line = re.sub(r'@\w+', '', line)

            if classDefLine:
                className, line = processClassDefLine(classDefLine, line)
            elif interfaceDefLine:
                # TODO - Deteccion mejorada interfaces :
                """
                (public)? interface\s*\b(?P<name>\w+\b<>)\s*(extends\s*(?P<inames>(((\w+\.?)*<?\w*>?,?\s*))+))?\s*{?
                """
                interfaceName = interfaceDefLine.group('name')
                line = re.sub(r'(.*?)\w* interface \b(?P<name>\w+)\b(.*?)\s*{(?P<nlin>\r?\n?)', r'\1class \g<name>(): \3\g<nlin>', line)
                # Adds the parents
                line = re.sub(r'\(\).*\bextends (?P<parents>([ .\w]*))\s*?(?P<nline>\r?\n?)', r'(\g<parents>):\g<nline>', line)
            elif throwMatch:
                line = re.sub(r'\bthrow\b', r'raise', line)
            elif enumMatch:
                # TODO - Constructor Enum
                # TODO Declaracion Enum mejorada:
                """
                enum\s*(?P<name>\w+)\s*
                (implements\s*(?P<ifaces>((\w+,?\s*)*\w+)))?
                \s*{?
                """
                line = re.sub(EX_ENUM_DECL, r'class \g<name>(Enum):', line)
            elif consMatch:
                line = processConsDefLine(className, consMatch, line)
            elif returnMatch:
                line = re.sub(r';', '', line)
            elif varMatch:
                line = processVarLine(varMatch, replacements, className, interfaceName, line)
            elif funMatch:
                if not mainMethod:
                    mainMethod = ';' not in line and re.search('public\s*static\s*void\s*main\(', line)
                line = processFuncLine(funMatch, className, interfaceName, replacements, line)

            line = re.sub(r'new ArrayList(<\w*>)?\(.*\)?', r'[]', line)
            line = re.sub(r'new LinkedList(<\w*>)?\(.*\)?', r'[]', line)
            line = re.sub(r'\bList(<\b\w*\b>)', r'', line)

            # Control structures
            line = processCondition(line)

            line = re.sub(r'\bwhile\b\s*\((?P<cond>.*)\).*{', r'while \g<cond>:', line)
            line = re.sub(r'\belse\s*if\b\s*\((?P<cond>.*)\).*{', r'elif \g<cond>:', line)
            line = re.sub(r'\bif\b\s*\((?P<cond>.*)\).*{', r'if \g<cond>:', line)
            line = re.sub(r'(\s*)}?.*\belse\b.*{?', r'\1else:', line)

            line = re.sub(EX_BASIC_FOR, r'for \1 in range(\2, \3):\g<nline>', line)
            line = re.sub(EX_LT_FOR, r'for \1 in range(\2, \3+1):\g<nline>', line)
            line = re.sub(r'range\(0,\s*', r'range(', line)
            line = re.sub(EX_EACH_FOR, r'for \1 in \2:\g<nline> ', line)

            line = re.sub(r'\btry\b\s*{', 'try:', line)
            line = re.sub(r'catch.*\(\s*(?:final)?\s*(?P<class>\b\w*Exception\b)\s+\b(?P<name>\w+)\b\)\s*{', r'except \g<class> as \g<name>:', line)
            line = re.sub(r'\bfinally\b\s*{', 'else:', line)

            line = re.sub(r'Integer.valueOf\((.+)\)', r'int(\1)', line)
            line = re.sub(r'([\w]+).toString\(\)', r'str(\1)', line)
            line = re.sub(r'(?P<struct>\b\w+(\(.*\))?(\.\w+(\(.*\))?)+)\.size\(\)', r'len(\g<struct>)', line)
            line = re.sub(r'(?P<struct>\b\w+(\(.*\))?(\.\w+(\(.*\))?)+)\.length', r'len(\g<struct>)', line)

            # Some operator replacements
            line = re.sub(r'(\w+)\+\+', r'\1 += 1', line)
            line = re.sub(r'(\w+)--', r'\1 -= 1', line)

            # Anonymous class declared
            line = re.sub(r'new\s*\b(?P<name>\w+)\b\((.*)\)\s*{$', r'class \g<name>: #TODO Revisar \2', line)

            # Tokens to be completely deleted
            line = re.sub(r'\bnew\b ', '', line)
            line = re.sub(r'\bvoid\b ', '', line)
            line = re.sub(r'\bstatic\b ', '', line)
            line = re.sub(r'\bprotected\b ', '', line)
            line = re.sub(r'\bfinal\b ', '', line)
            line = re.sub(r';', '', line)

            '''Because of structures like
                '} else {'
                or
                '} catch(Exception e) {'
                we delete only the spaces after the closing bracket'''
            line = re.sub(r'}[ \t]*', '', line)

            # If no thing remains, make the line blank
            line = re.sub(r'^[ \t]*$', '', line)

            # Some reserved words
            line = re.sub(r'\bthis\b', 'self', line)

            line = re.sub(r'(\W)\b(this)\b(\W)', r'\1self\3', line)
            line = re.sub(r'(\W)\b(null)\b(\W)', r'\1None\3', line)
            line = re.sub(r'System\.out\.println\(', r'print(', line)
            line = re.sub(r'System\.out\.print\((?P<content>.*)\)', r'print(\g<content>,)', line)

            # Replacements applies the conventions for variable names with dunder prefixes, eg: '__privateVar'
            for k, v in replacements.items():
                line = re.sub(r'\b' + k + r'\b', v, line)

            two_blank_lines = twoBlankLines(lastLine, line)
            lastLine = line
            if not two_blank_lines:
                pFile.write(line)

        # We end processing line by line, still in the current file,
        # didn't go to the next file yet
        if mainMethod:
            addMainMethod(pFile, className)


def addMainMethod(pFile, className):
    pFile.write(os.linesep + "if __name__ == '__main__':" + os.linesep)
    pFile.write("{}{c}.main()".format(TAB, c=className) + os.linesep)


def processFile(filename):
    """
    Processes a single file
    """
    try:
        match = re.match(r'.*\.java', filename, re.I)
        if match:
            # This line makes a regular expression with re.compile() to capture a java file name
            # and then sub() replaces the extension in it with "py"
            pyFilename = re.compile(r'java$', re.I).sub('py', filename)
            transform(filename, pyFilename)
        else:
            print(os.path.basename(filename) + ' is not a java file')
    except Exception as e:
        print('Error when processing '+filename)
        print(str(e))
        print(repr(e))
        raise e



def processDir(dirName, recursive):
    """
    Processes all files in a directory just using the parent directory name.
    :param dirName: the directory name from which the executions starts
    :param recursive: if the behaviour of the execution is to be recursive
    """
    os.chdir(dirName)
    for actualDir, subDirs, dirFiles in os.walk(dirName):
        for filename in dirFiles:
            processFile(os.path.join(actualDir, filename))

        # With RECURSIVE flag off, we definitely finish the processing no matter what
        if not recursive:
            break


def showHelp():
    """
    Prints the help on the screen
    """
    print('Proper usage is, in strict order: java2py [-r|-R] -f FileName.java | -d dirName\n')
    print("-f FileName.java: Process the java source code file with name 'FileName.java' and stops")
    print("-d dirName:       Process all java source code files in the directory with name 'dirName' ")
    print('-r |-R:           Recursive behaviour. Subdirectories will be processed recursively')
    print('\nYou can also execute: java2py resourceName being the resource the file name or the directory name ')


def main(argv):
    """
    First we process options, then we do the code translation from java to python
    """
    try:
        # Options and arguments processing
        print('processing opts')
        opts, args = getopt.getopt(argv, "f:d:t:rRh", ["file", "dir", "tab", "recursive"])
        print('opts processed: ' + str(opts))
        print('args processed: ' + str(args))
    except getopt.GetoptError:
        # Errors with options and arguments
        print('Invalid usage')
        showHelp()
        sys.exit(-1)

    HELP = False
    RECURSIVE = False
    IS_RELATIVE_PATH = False
    DIRMODE = False
    FILEMODE = False

    # TARGET_PATH is the current working directory
    # if assigned is assigned only once wir a file path or dir path
    TARGET_PATH = os.getcwd()

    # TODO - Proceso de argumentos por linea de comandos mejorado (otra libreria?)
    # args processing
    for opt, val in opts:
        HELP = opt in ['-h', '--help'] or HELP
        RECURSIVE = opt in ['-r', '-R', '--recursive'] or RECURSIVE
        DIRMODE = opt in ['-d', '--dir'] or DIRMODE
        FILEMODE = opt in ['-f', '--file'] or FILEMODE
        TAB = ' ' * int(val) if opt in ['-t', '--tab'] else 4 * ' '

        if FILEMODE or DIRMODE:
            # Initial char is not the os system folder separator and is alphanum
            IS_RELATIVE_PATH = val[0] != os.path.sep and val[0].isalnum()
            # If relative, there is user input for directory we build absolute path from the working directory
            # If not relative, the user input is already an absolute path to work with
            TARGET_PATH = os.path.join(TARGET_PATH, val) if IS_RELATIVE_PATH else val

    # Proceeding to the code translation

    # We decide the output depending on the mode
    if HELP:
        showHelp()
        sys.exit(0)
    elif DIRMODE:
        processDir(TARGET_PATH, RECURSIVE)
    elif FILEMODE:
        processFile(TARGET_PATH)
    else:
        os.chdir(TARGET_PATH)
        if os.path.isdir(val):
            TARGET_PATH = os.path.join(TARGET_PATH, val)
            processDir(TARGET_PATH, RECURSIVE)
        else:
            processFile(os.path.join(TARGET_PATH, val))

    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv[1:])
