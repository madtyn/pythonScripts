#!/usr/bin/python3

r"""
TODO
- Proceso de argumentos por linea de comandos mejorado para que no importe el orden de las opciones
- Variable estatica: static final String DESC = "patata" => ClassName.DESC = "patata"
- Declaracion de clase mejorada:
    (?P<modifs>(\b\w+\s*)*)class\s*(?P<className>\w+)(<.*>)?\s*
    (extends\s*(?P<parent>\w+)\s*)?
    (implements\s*(?P<ifaces>((\w+,?\s*)*\w+)))?
    \s*\{?
- Declaracion Enum mejorada:
    enum\s*(?P<name>\w+)\s*
    (implements\s*(?P<ifaces>((\w+,?\s*)*\w+)))?
    \s*{?
- Tipos de datos con r'<.*>\[.*\]'
- Revisar el for
    Buscar una expresion mejorada para el for (dividirlo en dos o tres partes y resolverlo en base a operadores :,<=,<,>)
- Metodo toString en declaracion de metodo
- Constructor Enum
- Llamada / invocacion a metodo toString() u otros:
    Regex de algo que puede invocar un metodo es (?P<obj>(\w+(?P<parenth>\(.*?\))?\.)+)nombreMetodo\(\)
- Usar @abc.abstractmethod justo encima de los metodos abstractos?
- Usar class Abstract([metaclass=ABCMeta]|ABC) para las abstractas (Python +3 y +3.4 respectivamente)
- Deteccion mejorada interfaces :
    (public)? interface\s*\b(?P<name>\w+\b<>)
    \s*(extends\s*(?P<inames>(((\w+\.?)*<?\w*>?,?\s*))+))?\s*{?
"""

import re
import sys
import os
import getopt

PRIVACY_PREFIXES = {'private': '__', 'protected': '_', 'public': ''}

# In Java, a variable may be belong to one out of three kinds of privacy
EX_PRIV_MODIFS = r'\s*(?P<priv>((\bpublic\b\s*|\bprivate\b\s*|\bprotected\b\s*))+)?'

# Modifiers for variables and functions
EX_VAR_MODIFS = r'(?P<vmodifs>\b(static\s*|final\s*|transient\s*|volatile\s*)+)?'
EX_FUN_MODIFS = r'(?P<fmodifs>\b(abstract\s*|static\s*|synchronized\s*|native\s*)+)?'

# Data type for a variable or the function returned value
EX_DATA_TYPE = r'\b(?P<type>\w+)(<.*?>)?\[?\]?\s*'

# The whole of variable or function declaration
EX_VAR_DECL = r'^(?P<space>\s*)' + EX_PRIV_MODIFS + EX_VAR_MODIFS + EX_DATA_TYPE + r'\b(?P<vname>\w+)\s*(?P<value>=.*)?;'
EX_FUN_DECL = r'^(?P<space>\s*)<?[^=\.\(\)]*?>?\s*' + EX_PRIV_MODIFS + EX_FUN_MODIFS + EX_DATA_TYPE + r'\b(?P<fname>\w+)\((?P<fargs>.*)\)\s*\{?'
EX_ENUM_DECL = r'(public)?\s*\benum\b\s*\b(?P<name>\w+)\b\s*\{?'
EX_BASIC_FOR = r'\bfor\b.*\(.*(\w+)\W*=\W*(\w+)\W*;.*<\W*([\w\.\(\)\[\]]+);.*\).*\{?.*(?P<nline>\r?\n?)\s*\{?'
EX_LT_FOR = r'\bfor\b.*\(.*(\w+)\W*=\W*(\w+)\W*;.*<=\W*([\w\.\(\)\[\]]+);.*\).*\{?.*(?P<nline>\r?\n?)\s*\{?'
EX_EACH_FOR = r'\bfor\b.*\(.*\b(\w+)\b.*:.*\b(\w+)\b.*\).*\{?.*(?P<nline>\r?\n?)\s*\{?'

# For better performance, we compile the patterns for declaration statements
PAT_VAR_DECL = re.compile(EX_VAR_DECL)
PAT_FUN_DECL = re.compile(EX_FUN_DECL)


def quickTask(line, regex, replacement=None, foutput=None):
    """
    Optionally, makes a quick replacement task
    and detects a situation for returning True to continue the loop
    :param line: the line for processing
    :param regex: the regular expression to find or replace
    :param replacement: the replacement for the regex if found
    :param foutput: the output file to write to if there is a match
    """
    match = re.search(regex, line)
    if match and line and foutput:
        line = re.sub(regex, replacement, line)
        foutput.write(line)
    return bool(match)


def processArgs(args):
    """
    Process the arguments passed into a Java method removing modifiers and types
    :param args: the args to be processed
    """
    processed = ''
    if args and len(args):
        processed = args[:]
        # TODO Meter '*' en tipo array o List/arrayList
        processed = re.sub(r'(((\b\w+\b[\[\]]*\s+)+))(?P<arg>\b\w+,?)', r'\g<arg>', processed)
    return processed


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

        for oldLine in jFile:
            line = oldLine[:]

            '''
            Remove not leading whitespace
            Negative lookbehind (means no previous whitespace [ \t])
            Negative lookahead (first thing in regex before consuming chars, not being at the line start)
            '''
            line = re.sub(r'(?<![ \t])(?!^)[ \t]+', r' ', line)
            line = line.rstrip()
            line = line + os.linesep

            taskMade = False
            # 1-Change replacements tasks which can be made and allow to go on with the next line if made
            for task in quickTaskList:
                taskMade = quickTask(line, task[0], task[1], pFile)
                if taskMade:
                    break

            if taskMade:
                continue

            classDefLine = re.search(r'\bclass (?P<name>\w+)', line)
            interfaceDefLine = re.search(r'\binterface (?P<name>\w+)', line)
            consMatch = None
            if className:
                consMatch = re.search(r'\b' + className + r'\b\((?P<args>.*)\)\s*\{?', line)

            returnMatch = re.search(r'return .*;', line)
            enumMatch = re.search(EX_ENUM_DECL, line)
            varMatch = re.search(PAT_VAR_DECL, line)
            funMatch = re.search(PAT_FUN_DECL, line)

            # Removing annotations
            line = re.sub(r'@\w+', '', line)

            if classDefLine:
                className, line = processClassDefLine(classDefLine, line)
            elif interfaceDefLine:
                interfaceName = interfaceDefLine.group('name')
                line = re.sub(r'(.*?)\w* interface \b(?P<name>\w+)\b(.*?)\s*{(?P<nlin>\r?\n?)', r'\1class \g<name>(): \3\g<nlin>', line)
                # Adds the parents
                line = re.sub(r'\(\).*\bextends (?P<parents>([ .\w]*))\s*?(?P<nline>\r?\n?)', r'(\g<parents>):\g<nline>', line)
            elif enumMatch:
                line = re.sub(EX_ENUM_DECL, r'class \g<name>(Enum):', line)
            elif consMatch:
                line = processConsDefLine(className, consMatch, line)
            elif returnMatch:
                line = re.sub(r';', '', line)
            elif varMatch:
                space = varMatch.group('space')
                priv = varMatch.group('priv').rstrip() if varMatch.group('priv') else ''

                # vmodifs = varMatch.group('vmodifs')
                # vtype = varMatch.group('type')
                vname = PRIVACY_PREFIXES.get(priv, '') + varMatch.group('vname')
                replacements[varMatch.group('vname')] = vname

                # If it's an array, we make the [] initialisation with the semicolon (;) ending
                line = re.sub(r'(.*)(?P<arr>(\[\])+)([^=]*);', r'\1\3 = \g<arr>;', line)
                # If it's not an array, first value will be None
                line = re.sub(r'^([^=]*);', r'\1 = None;', line)
                line = re.sub(PAT_VAR_DECL, space + vname + r' \g<value>', line)
            elif funMatch:
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
                    line += space + '\tpass' + os.linesep

            line = re.sub(r'new ArrayList(<\w*>)?\(.*\)?', r'[]', line)
            line = re.sub(r'new LinkedList(<\w*>)?\(.*\)?', r'[]', line)
            line = re.sub(r'\bList(<\b\w*\b>)', r'', line)

            # Control structures
            line = re.sub(r'.equals\((.*)\)', r' == \1', line)
            line = re.sub(r'\s*!=\s*null', r'', line)
            line = re.sub(r'==\s*null', r'is None', line)
            line = re.sub(r'!\s*\(', r'not (', line)
            line = re.sub(r'!\s*\b(\w+)\b', r'not \1', line)
            line = re.sub(r'&&', 'and', line)
            line = re.sub(r'\|\|', 'or', line)
            line = re.sub(r'\bwhile\b\s*\((?P<cond>.*)\).*{', r'while \g<cond>: #TODO Check condition', line)
            line = re.sub(r'\belse\s*if\b\s*\((?P<cond>.*)\).*{', r'elif \g<cond>: #TODO Check condition', line)
            line = re.sub(r'\bif\b\s*\((?P<cond>.*)\).*{', r'if \g<cond>: #TODO Check condition', line)
            line = re.sub(r'(\s*)}?.*\belse\b.*{?', r'\1else:', line)

            line = re.sub(EX_BASIC_FOR, r'for \1 in range(\2, \3): # FIXME \g<nline>', line)
            line = re.sub(EX_LT_FOR, r'for \1 in range(\2, \3+1): # FIXME \g<nline>', line)
            line = re.sub(r'range\(0,\s*', r'range(', line)
            line = re.sub(EX_EACH_FOR, r'for \1 in \2: #TODO Check condition\g<nline> ', line)

            line = re.sub(r'\bthrow\b', r'raise', line)
            line = re.sub(r'\btry\b\s*{', 'try:', line)
            line = re.sub(r'catch.*\(\s*(?:final)?\s*(?P<class>\b\w*Exception\b)\s+\b(?P<name>\w+)\b\)\s*{', r'except \g<class> as \g<name>:', line)
            line = re.sub(r'\bfinally\b\s*{', 'else:', line)

            line = re.sub(r'Integer.valueOf\((.+)\)', r'int(\1)', line)
            line = re.sub(r'([\w]+).toString\(\)', r'str(\1)', line)

            # Some operator replacements
            line = re.sub(r'(\w+)\+\+', r'\1 += 1', line)
            line = re.sub(r'(\w+)--', r'\1 -= 1', line)

            # Anonymous class declared
            line = re.sub(r'new\s*\b(?P<name>\w+)\b\((.*)\)\s*{$', r'class \g<name>: #TODO Revisar \2', line)

            # Tokens to be completely deleted
            line = re.sub(r';', '', line)
            line = re.sub(r'\bnew\b ', '', line)
            line = re.sub(r'\bvoid\b ', '', line)
            line = re.sub(r'\bstatic\b ', '', line)
            line = re.sub(r'\bprotected\b ', '', line)
            line = re.sub(r'\bfinal\b ', '', line)

            '''Because of structures like
                '} else {'
                or
                '} catch(Exception e) {'
                we delete the spaces after the closing bracket'''
            line = re.sub(r'}[ \t]*', '', line)

            # If no thing remains, make the line blank
            line = re.sub(r'^[ \t]*$', '', line)

            # Some reserved words
            line = re.sub(r'\bthis\b', 'self', line)
            line = re.sub(r'\btrue\b', 'True', line)
            line = re.sub(r'\bfalse\b', 'False', line)
            line = re.sub(r'(\W)\b(this)\b(\W)', r'\1self\3', line)
            line = re.sub(r'(\W)\b(null)\b(\W)', r'\1None\3', line)
            line = re.sub(r'System\.out\.println\(', r'print(', line)
            line = re.sub(r'System\.out\.print\((?P<content>.*)\)', r'print(\g<content>,)', line)

            for k, v in replacements.items():
                line = re.sub(r'\b' + k + r'\b', v, line)

            pFile.write(line)


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
    if className:
        args = prependSelf(args)
    line = re.sub(r'\b' + className + r'\b\((?P<args>.*)\)\s*\{?', r'__init__(' + args + '):', line)
    line = os.linesep + line
    return line


def processClassDefLine(classDefLine, line):
    """
    Processes an already detected Java class declaration line and returns
    the Java class name and the text line processed to be an approximate Python source code line
    :param classDefLine: the match object with the className captured
    :param line: the java source code line to be processed
    :return: a tuple with the className and the processed line (className,processedLine)
    """
    className = classDefLine.group('name')
    isAbstractClass = re.search(r'abstract', line)
    line = re.sub(r'(.*?)\w* class \b(?P<name>\w+)\b(.*?)\s*{(?P<nline>\r?\n?)', r'\1class \g<name>(): \3\g<nline>', line)
    # Adds the parents
    line = re.sub(r'\(\).*\bextends (?P<parents>([ .\w]*))\s*?(?P<nline>\r?\n?)', r'(\g<parents>):\g<nline>', line)
    # Adds the interfaces if there were no parents
    line = re.sub(r'\(\).*\bimplements (?P<ifaces>(.*))', r'(\g<ifaces>)', line)
    # Adds the interfaces if there were parents
    line = re.sub(r'\((?P<parents>.+?).*\bimplements (?P<ifaces>\S*)\s*', r'(\g<parents>,\g<ifaces>', line)
    if isAbstractClass:
        line = re.sub(className + r'\((?P<ancestors>(\w+, )*\w+)\)\s*:', className + r'(\g<ancestors>, metaclass=ABCMeta):', line)
        line = re.sub(className + r'\(\s*\)\s*:', className + r'(metaclass=ABCMeta):', line)
    else:
        line = re.sub(r'\(\):', r'(object):', line)
    return className, line


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


def processDir(dirName, isRecursive):
    """
    Processes all files in a directory just using the parent directory name.
    :param dirName: the directory name from which the executions starts
    :param isRecursive: if the behaviour of the execution is to be recursive
    """
    os.chdir(dirName)
    for actualDir, subDirs, dirFiles in os.walk(dirName):
        # With RECURSIVE flag on
        if isRecursive:
            for subdirName in subDirs:
                processDir(subdirName, isRecursive)

        for filename in dirFiles:
            processFile(os.path.join(actualDir, filename))


def processFile(filename):
    """
    Processes a single file
    """
    match = re.match(r'.*\.java', filename, re.I)
    if match:
        # This line makes a regular expression with re.compile() to capture a java file name
        # and then sub() replaces the extension in it with "py"
        pyFilename = re.compile(r'java$', re.I).sub('py', filename)
        transform(filename, pyFilename)
    else:
        print(os.path.basename(filename) + ' is not a java file')


def main(argv):
    """
    First we process options, then we do the code translation from java to python
    """

    try:
        # Options and arguments processing
        print('processing opts')
        opts, args = getopt.getopt(argv, "f:d:rRh", ["file", "dir", "recursive"])
        print('opts processed: ' + str(opts))
        print('args processed: ' + str(args))
    except getopt.GetoptError:
        # Errors with options and arguments
        print('Invalid usage')
        showHelp()
        sys.exit(-1)

    # BASE_DIR is the current working directory, if assigned is assgined only once
    BASE_DIR = os.getcwd()

    # Proceeding to the code translation
    for opt, val in opts:
        if opt in ['-h', '--help']:
            showHelp()
            sys.exit(0)

        RECURSIVE = opt in ['-r', '-R', '--recursive'] or False

        if opt in ['-d', '--dir']:
            # Initial char is not the os system folder separator and is alphanum
            IS_RELATIVE_DIR = val[0] != os.path.sep and val[0].isalnum()
            # If relative, there is user input for directory we build absolute path from the working directory
            # If not relative, the user input is already an absolute path to work with
            BASE_DIR = os.path.join(BASE_DIR, val) if IS_RELATIVE_DIR else val
            processDir(BASE_DIR, RECURSIVE)
        elif opt in ['-f', '--file']:
            processFile(os.path.join(BASE_DIR, val))
        else:
            os.chdir(BASE_DIR)
            if os.path.isdir(val):
                BASE_DIR = os.path.join(BASE_DIR, val)
                processDir(BASE_DIR, RECURSIVE)
            else:
                processFile(os.path.join(BASE_DIR, val))
    sys.exit(0)


def showHelp():
    """
    Prints the help on the screen
    """
    print('Proper usage is, in strict order: java2py [-r|-R] -f FileName.java | -d dirName\n')
    print("-f FileName.java: Process the java source code file with name 'FileName.java' and stops")
    print("-d dirName:       Process all java source code files in the directory with name 'dirName' ")
    print('-r |-R:           Recursive behaviour. Subdirectories will be processed recursively')
    print('\nYou can also execute: java2py resourceName being the resource the file name or the directory name ')


if __name__ == "__main__":
    main(sys.argv[1:])
