#!/usr/bin/python3

'''
TODO Tipos de datos con <.*>\[.*\]
TODO Revisar el for
TODO Deteccion mejorada interfaces -> (public)? interface\s*\b(?P<name>\w+\b<>)\s*(extends\s*(?P<inames>(((\w+\.?)*<?\w*>?,?\s*))+))?\s*{?
'''

import re
import sys, os
import getopt

RECURSIVE = False
PRIVACY_PREFIXES = {'private':'__', 'protected':'_', 'public':''}

def quickTask(line, regex, replacement=None, foutput=None):
	'''
	Optionally, makes a quick replacement task 
	and detects a situation for returning True to continue the loop
	:param line: the line for processing
	:param regex: the regular expression to find or replace
	:param replacement: the replacement for the regex if found
	:param foutput: the foutput to write to if there is a match
	'''
	match = re.search(regex, line)
	if match and line and foutput:
		line = re.sub(regex, replacement, line)
		foutput.write(line)
	return bool(match)

def processArgs(args):
	'''
	Process the arguments for the Java method removing modifiers and types
	:param args: the args to be processed
	'''
	processed=''
	if args and len(args):
		processed=args[:]
		processed = re.sub(r'(((\b\w+\b[\[\]]*\s+)+))(?P<arg>\b\w+,?)', r'\g<arg>', processed) # TODO Meter '*' en tipo array o List/arrayList
	return processed

def transform(javaFile, pyFile):
	'''
	With a java file as input produces a python file as output
	'''
	with open(javaFile, 'r') as jFile:
		with open(pyFile, 'w+') as pFile:
			replacements = {}
			privModifsExp = r'\s*(?P<priv>((\bpublic\b\s*|\bprivate\b\s*|\bprotected\b\s*))+)?'
			vmodifsExp = r'(?P<vmodifs>\b(static\s*|final\s*|transient\s*|volatile\s*)+)?'
			fmodifsExp = r'(?P<fmodifs>\b(abstract\s*|static\s*|synchronized\s*|native\s*)+)?'
			datatypeExp = r'\b(?P<type>\w+)(<.*?>)?\[?\]?\s*'
			varDecExp = r'^(?P<space>\s*)' + privModifsExp + vmodifsExp + datatypeExp + r'\b(?P<vname>\w+)\s*(?P<value>=.*)?;'
			funDecExp = r'^(?P<space>\s*)<?[^=\.\(\)]*?>?\s*' + privModifsExp + fmodifsExp + datatypeExp + r'\b(?P<fname>\w+)\((?P<fargs>.*)\)\s*\{?'
			
			# Esto es lo que usaremos en las iteraciones
			varPattern = re.compile(varDecExp)
			funPattern = re.compile(funDecExp)
			
			className = None
			interfaceName = None
			for oldLine in jFile:
				line = oldLine[:]
				line = line.rstrip()
				line = line + os.linesep
				
				if quickTask(line, r'^(\s*)package', r'\1#package', pFile):
					continue

				if quickTask(line, r'^(\s*)import', r'\1#import', pFile):
					continue
				
				if quickTask(line, r'//', r'#', pFile):
					continue
				
				if quickTask(line, r'/\*|\*/', r'"""', pFile):
					continue

				if quickTask(line, r'^\s*}\s*\r?\n'):
					continue
				
				if quickTask(line, r'^\s*\r?\n'):
					continue

				# CLASS DECLARATION
				classDefLine = re.search(r'\bclass (?P<name>\w+)', line)
				interfaceDefLine = re.search(r'\binterface (?P<name>\w+)', line)
				consMatch = None
				if className:
					consMatch = re.search(r'\b'+className+r'\b\((?P<args>.*)\)\s*\{?', line)	
				
				returnMatch = re.search(r'return .*;', line)	
				varMatch = re.search(varPattern, line)
				funMatch = re.search(funPattern, line)

				if classDefLine:
					className = classDefLine.group('name')
					line = re.sub(r'(.*?)\w* class \b(?P<name>\w+)\b(.*?)\s*{(?P<nline>\r?\n?)', r'\1class \g<name>(): \3\g<nline>', line)
					# Adds the parents
					line = re.sub(r'\(\).*\bextends (?P<parents>([ .\w]*))\s*?(?P<nline>\r?\n?)', r'(\g<parents>):\g<nline>', line)	
					# Adds the interfaces if there were no parents
					line = re.sub(r'\(\).*\bimplements (?P<contracts>(.*))', r'(\g<contracts>)', line)
					# Adds the interfaces if there were parents
					line = re.sub(r'\((?P<parents>.+?).*\bimplements (?P<contracts>\S*)\s*', r'(\g<parents>,\g<contracts>', line)
				elif interfaceDefLine:
					interfaceName = interfaceDefLine.group('name')
					line = re.sub(r'(.*?)\w* interface \b(?P<name>\w+)\b(.*?)\s*{(?P<nline>\r?\n?)', r'\1class \g<name>(): \3\g<nline>', line)
				elif consMatch:
					args = processArgs(consMatch.group('args'))
					if className:
						self_='self'
						if len(args):
							self_ += ', '
						args = self_ + args
						
					line = re.sub(r'\b'+className+r'\b\((?P<args>.*)\)\s*\{?', r'__init__('+args+'):', line)
					line = os.linesep + line
				elif returnMatch:
					line = re.sub(r';', '', line)
				elif varMatch:
					space = varMatch.group('space')
					priv = varMatch.group('priv').rstrip() if varMatch.group('priv') else ''

# 					vmodifs = varMatch.group('vmodifs')
# 					vtype = varMatch.group('type')
					vname = PRIVACY_PREFIXES.get(priv, '') + varMatch.group('vname')
					replacements[varMatch.group('vname')] = vname
					
					#Si es array, lo convertimos a una inicializacion a [] con ; de Java
					line = re.sub(r'(.*)(?P<arr>(\[\])+)([^=]*);', r'\1\3 = \g<arr>;', line)
					# Si no es array, inicializamos a None
					line = re.sub(r'^([^=]*);', r'\1 = None;', line)
					line = re.sub(varPattern, space + vname + r' \g<value>', line)
				elif funMatch:
					space = funMatch.group('space')
					priv = funMatch.group('priv').rstrip() if funMatch.group('priv') else ''

					fmodifs = funMatch.group('fmodifs').rstrip() if funMatch.group('fmodifs') else ''
# 						ftype = funMatch.group('type')
					fname = PRIVACY_PREFIXES.get(priv, '') + funMatch.group('fname')
					replacements[funMatch.group('fname')] = fname

					args = processArgs(funMatch.group('fargs'))
					
					if className and not 'static' in fmodifs:
						self_='self'
						if len(args):
							self_ += ', '
						args = self_ + args
					
					line = re.sub(funPattern, space+r'def ' + fname + r'('+args+'):', line)
					line = re.sub(r'throws (\w*Exception,?\s*)+[ \t]{?', r'', line)
					if 'static' in fmodifs:
						line = space +'@staticmethod\n' + line
					if interfaceName or 'abstract' in fmodifs:
						line += space + '\tpass\n'
					line = os.linesep + line

				line = re.sub(r'new ArrayList(<\b\w*\b>)?\(.*\)?', r'[]',line)
				line = re.sub(r'\bList(<\b\w*\b>)', r'',line)

				# Control structures
				line = re.sub(r'(\w+).equals\((.*)\)', r'\1 == \2', line)
				line = re.sub(r'!=\s*null', r'', line)
				line = re.sub(r'==\s*null', r'is None', line)
				line = re.sub(r'!\s*\(', r'not (', line)
				line = re.sub(r'!\s*\b(\w+)\b', r'not \1', line)
				line = re.sub(r'&&', 'and', line)
				line = re.sub(r'\|\|', 'or', line)
				line = re.sub(r'\bwhile\b\s*\((?P<cond>.*)\).*{', r'while \g<cond>: #TODO Check condition', line)
				line = re.sub(r'\belse if\b\s*\((?P<cond>.*)\).*{', r'elif \g<cond>: #TODO Check condition', line)
				line = re.sub(r'if\s*\((?P<cond>.*)\).*{', r'if \g<cond>: #TODO Check condition', line)
				line = re.sub(r'(\s*)}?.*\belse\b.*{?', r'\1else:', line)
				line = re.sub(r'\bfor\b.*\(.*(\w+)\W*=\W*(\w+)\W*;.*<\W*([\w\.\(\)\[\]]+);.*\).*\{?.*(?P<nline>\r?\n?)\s*\{?', r'for \1 in range(\2, \3): # FIXME \g<nline>', line)
				line = re.sub(r'\bfor\b.*\(.*(\w+)\W*=\W*(\w+)\W*;.*<=\W*([\w\.\(\)\[\]]+);.*\).*\{?.*(?P<nline>\r?\n?)\s*\{?', r'for \1 in range(\2, \3+1): # FIXME \g<nline>', line)
				line = re.sub(r'\bfor\b.*\(.*\b(\w+)\b.*:.*\b(\w+)\b.*\).*\{?.*(?P<nline>\r?\n?)\s*\{?', r'for \1 in \2: #TODO Check condition\g<nline> ' , line)

				line = re.sub(r'\bthrow\b', r'raise', line)
				line = re.sub(r'\btry\b\s*{', 'try:', line)
				line = re.sub(r'catch.*\(\s*(?:final)?\s*(?P<class>\b\w*Exception\b)\s+\b(?P<name>\w+)\b\)\s*{', r'except \g<class> as \g<name>:', line)
				line = re.sub(r'\bfinally\b\s*{', 'else:' , line)
				
				line = re.sub(r'Integer.valueOf\((.+)\)', r'int(\1)', line)
				line = re.sub(r'(\w+).toString()', r'str(\1)', line)

				# Comments
				line = re.sub(r';', '', line)
				line = re.sub(r'@param', ':param', line)

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
				line = re.sub(r'@\w+', '', line)

				'''Because of structures like 
					'} else {' 
					or 
					'} catch(Exception e) {' 
					we delete the spaces after the closing bracket'''
				line = re.sub(r'}\s*', '', line)

				# If no thing remains, make the line blank
				line = re.sub(r'^\s*$', '', line)

				# Some reserved words
				line = re.sub(r'\bthis\b', 'self', line)
				line = re.sub(r'\btrue\b', 'True', line)
				line = re.sub(r'\bfalse\b', 'False', line)
				line = re.sub(r'(\W)\b(this)\b(\W)', r'\1self\3', line)
				line = re.sub(r'(\W)\b(null)\b(\W)', r'\1None\3', line)
				line = re.sub(r'System\.out\.println\((?P<content>.*)\)', r'print(\g<content> + ' + os.linesep + r')', line)
				line = re.sub(r'System\.out\.print\(', r'print(', line)
				
				for k,v in replacements.items():
					line = re.sub(r'\b'+k+r'\b', v, line)

				pFile.write(line)

def processDir(dirName):
	'''
	Processes all files in a directory just using the parent directory name.
	This,is the absolute path 
	'''
	os.chdir(dirName)
	for actualDir, subDirs, dirFiles in os.walk(dirName):
		# With recursive flag on
		if RECURSIVE:
			for subdirName in subDirs:
				processDir(subdirName)

		for filename in dirFiles:
			processFile(os.path.join(actualDir, filename))

def processFile(filename):
	'''
	Processes a single file
	'''
	match = re.match(r'.*\.java', filename, re.I)
	if match:
		# This line makes a regular expression with re.compile() to capture a java file name
		# and then sub() replaces the extension in it with "py"
		pyFilename = re.compile(r'java$', re.I).sub('py', filename)
		transform(filename, pyFilename)
	else:
		print(os.path.basename(filename) + ' is not a java file')


def main(argv):
	'''
	First we process options, then we do the code translation from java to python
	'''
	# BASE_DIR is the current working directory
	BASE_DIR = os.getcwd()

	try:
		# Options and arguments processing
		print('processing opts')
		opts, args = getopt.getopt(argv, "f:d:rR", ["file", "dir", "recursive"])
		print('opts processed: ' + str(opts))
		print('args processed: ' + str(args))
	except getopt.GetoptError:
		# Errors with options and arguments
		print('Invalid usage')
		print('Proper usage is java2py [-r] -f fileName | -d dirName ')
		sys.exit(-1)

	# Proceeding to the code translation
	for opt, val in opts:
		RECURSIVE = opt in ['-r', '-R', '--recursive']

		print('value is ' + val)
		if opt in ['-d', '--dir']:
			isRelativeDir = val[0] != os.path.sep and val[0].isalnum()
			if isRelativeDir:
				BASE_DIR = os.path.join(BASE_DIR, val)
			else:
				BASE_DIR = val
			processDir(BASE_DIR)
		elif opt in ['-f', '--file']:
			processFile(os.path.join(BASE_DIR, val))
		else:
			os.chdir(BASE_DIR)
			if os.path.isdir(val):
				BASE_DIR = os.path.join(BASE_DIR, val)
				processDir(BASE_DIR)
			else:
				processFile(os.path.join(BASE_DIR, val))
	sys.exit(0)

if __name__ == "__main__":
	main(sys.argv[1:])
