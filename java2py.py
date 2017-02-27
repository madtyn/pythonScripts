#!/usr/bin/python3

'''
TODO Detectar mejor declaracion de variables 
	(public |private |protected |final |static )*(?P<type>\w+ )(?P<var>\w+)\s*=(.*);
	(public |private |protected |final |static )*(?P<type>\w+ )(?P<var>\w+)\s*;
TODO Implementar con un diccionario un sistema de reemplazado de todas las variables locales

TODO en declaraciones de variables tambien se cumple:
\b(?P<tipo>\w*)\b \b\w*\b; 
o bien
\b(?P<tipo>\w*)\b \b\w*\b = (?P<valor); 
'''


import re
import sys, os
import getopt

RECURSIVE = False

def transform(javaFile, pyFile):
	'''
	With a java file as input produces a python file as output
	'''
	with open(javaFile, 'r') as jFile:
		with open(pyFile, 'w+') as pFile:
			className = None
			interfaceName = None
			for oldLine in jFile:
				line = oldLine[:]
				line.rstrip()
				
				match = re.search(r'^(\s*)package', line)
				if match:
					line = re.sub(r'^(\s*)package', r'\1#package', line)
					pFile.write(line)
					continue

				match = re.search(r'^(\s*)import', line)
				if match:
					line = re.sub(r'^(\s*)import', r'\1#import', line)
					pFile.write(line)
					continue
				
				match  = re.search(r'^\s*}\s*$', line)
				if match:
					line = re.sub(r'}', r'', line)
					pFile.write(line)
					continue

				# CLASS DECLARATION
				classDefLine = re.search(r'\bclass (?P<name>\w+)', line)
				if classDefLine:
					className = classDefLine.group('name')
				line = re.sub(r'(.*?)\w* class \b(?P<name>\w+)\b(.*?)\s*{(?P<nline>\r?\n?)', r'\1class \g<name>(): \3\g<nline>', line)
				
				interfaceDefLine = re.search(r'\binterface (?P<name>\w+)', line)
				if interfaceDefLine:
					interfaceName = interfaceDefLine.group('name')
				line = re.sub(r'(.*?)\w* interface \b(?P<name>\w+)\b(.*?)\s*{(?P<nline>\r?\n?)', r'\1class \g<name>(): \3\g<nline>', line)

				# Adds the parents
				line = re.sub(r'\(\).*\bextends (?P<parents>([ .\w]*))\s*?(?P<nline>\r?\n?)', r'(\g<parents>):\g<nline>', line)

				# Adds the interfaces if there were no parents
				line = re.sub(r'\(\).*\bimplements (?P<contracts>(.*))', r'(\g<contracts>)', line)
				# Adds the interfaces if there were parents
				line = re.sub(r'\((?P<parents>.+?).*\bimplements (?P<contracts>\S*)\s*', r'(\g<parents>,\g<contracts>', line)

				if not classDefLine and className:
					pattern='\b'+className
					line = re.sub(r'\b'+className+r'\b\(', '__init__(', line)

				# Declaration
				declaration = False
				declaration = re.search(r'\bpublic\b|\bprivate\b|\bprotected\b', line)
				if declaration:
					print('DECLARATION: '+line)
					isFinal = False
					isStatic = False
					prefix = ''
					privacy = ''
					privacy = declaration.group()
					if privacy == 'private':
						prefix = '__'
					elif privacy == 'protected':
						prefix = '_'
					isStatic = re.search(r'static ', line)
					if isStatic:
						line = re.sub(r'static ', '', line)
					isFinal = re.search(r'final ', line)
					if isFinal:
						line = re.sub(r'final ', '', line)
					
					if re.search(r'=',line):
						isMethod = False
						isMethodArgs = False
					elif not re.search(r';$', line):
						isMethod = bool(re.search(r'(.*?)\b(?P<fname>\w+)\b\(\) *{', line))
						isMethodArgs = bool(re.search(r'(.*?)(?P<fname>\b\w+\b\()(?P<args>.*\)).+{', line))
					elif interfaceName:
						isMethod = bool(re.search(r'(.*?)(?P<fname>\b\w+\b)\(\) *;', line))
						isMethodArgs = bool(re.search(r'(.*?)(?P<fname>\b\w+\b\()(?P<args>.*\)).+;', line))
						
					if isMethod:
						print('IS_METHOD')
						line = re.sub(r'(.*?)(?P<fname>\b\w+\b)\(\) *{', r'\1def '+prefix+r'\g<fname>(self):', line)
						line = re.sub(r'\w* def', r'def', line)
						if interfaceName:
							spaces = re.search(r'^\s*', line)
							line += os.linesep + spaces + '\tpass'
						if isStatic:
							re.search('(?P<name>\s+)', line).group()
							line = '@staticmethod\n' + line
						line = os.linesep + line
					elif isMethodArgs:
						print('IS_METHOD')
						line = re.sub(r'(.*?)(?P<fname>\b\w+\b\()(?P<args>.*\)).+{', r'\1def '+prefix+r'\g<fname>self,\g<args>: ', line)
						line = re.sub('\b\w+\b\s+\b(\w+)\b[,\)]', '\1,', line)
						line = re.sub(r'\w* def', r'def', line)
						if isStatic:
							re.search('(?P<name>\s+)', line).group()
							line = '@staticmethod\n' + line
						line = os.linesep + line
					else:
						print('IS_VARIABLE')
						#Si es array
						line = re.sub(r'(.*)(\[\](.*);)', r'\1\3 = []', line)
						line = re.sub(r'(.*)\[\](.*=)', r'\1\3 =', line)
						
						line = re.sub(r'\b\w*\b\s*\b(\w+)\b\s*=(.*);',prefix+r'\1 =\2',line)
						line = re.sub(r'\b\w*\b\s*\b(\w+)\b\s*;', prefix+r'\1 = None',line)
				
					line = re.sub(r'\bpublic ', '', line)
					line = re.sub(r'\bprivate ', '', line)
					line = re.sub(r'\bprotected ', '', line)
				
					# Type erasure
					line = re.sub(r'\bString \b(\w+)\b', r'\1', line)
					line = re.sub(r'\bint (\b\w+\b)', r'\1', line)
					line = re.sub(r'\bInteger \b(\w+)\b', r'\1', line)
					line = re.sub(r'\b[Dd]ouble \b(\w+)\b', r'\1', line)
					line = re.sub(r'\b[Ff]loat \b(\w+)\b', r'\1', line)
					line = re.sub(r'\b[Ll]ong \b(\w+)\b', r'\1', line)
					line = re.sub(r'\b[Bb]oolean \b(\w+)\b', r'\1', line)
					
				line = re.sub(r'new ArrayList(<\b\w+\b>)?\(.*\)?', r'[]',line)
				line = re.sub(r'\bList(<\b\w*\b>)', r'',line)
				line = re.sub(r';', '', line)

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
				line = re.sub(r'\bfor\b.*\(.*(\w+)\W*=\W*(\w+)\W*;.*<\W*([\w\.\(\)\[\]]+);.*\).*\{?.*(?P<nline>\r?\n?)', r'for \1 in range(\2, \3): # FIXME \g<nline>', line)
				line = re.sub(r'\bfor\b.*\(.*(\w+)\W*=\W*(\w+)\W*;.*<=\W*([\w\.\(\)\[\]]+);.*\).*\{?.*(?P<nline>\r?\n?)', r'for \1 in range(\2, \3+1): # FIXME \g<nline>', line)
				line = re.sub(r'\bfor\b.*\(.*\b(\w+)\b.*:.*\b(\w+)\b.*\).*\{?.*(?P<nline>\r?\n?)', r'for \1 in \2: #TODO Check condition\g<nline> ' , line)

				line = re.sub(r'\bthrow\b', r'raise', line)
				line = re.sub(r'\btry\b\s*{', 'try:', line)
				line = re.sub(r'catch.*\(\s*(?:final)?\s*(?P<class>\b\w*Exception\b)\s+\b(?P<name>\w+)\b\)\s*{', r'except \g<class> as \g<name>:', line)
				line = re.sub(r'\bfinally\b\s*{', 'else:' , line)
				
				line = re.sub(r'Integer.valueOf\((.+)\)', r'int(\1)', line)
				line = re.sub(r'(\w+).toString()', r'str(\1)', line)

				# Method declaration
# 				print '*', line
# 				raw_input('')
# 				print '<<', line
				# Comments
				line = re.sub(r'@param', ':param', line)
				line = re.sub(r'//', '#', line)
				line = re.sub(r'/\*|\*/', '"""', line)

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
		opts, args = getopt.getopt(argv, "f:d:r", ["file", "dir", "recursive"])
		print('opts processed: ' + str(opts))
		print('args processed: ' + str(args))
	except getopt.GetoptError:
		# Errors with options and arguments
		print('Invalid usage')
		print('Proper usage is java2py [-r] -f fileName | -d dirName ')
		sys.exit(-1)

	# Proceeding to the code translation
	for opt, val in opts:
		RECURSIVE = opt in ['-r', '--recursive']

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

if __name__ == "__main__":
	main(sys.argv[1:])
