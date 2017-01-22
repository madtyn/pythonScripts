#!/usr/bin/python

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
			for oldLine in jFile:
				line = oldLine
				
				match = re.search(r'^(\s*)package', line)
				if match:
					line = re.sub(r'^(\s*)package', r'\1#package', line)
					continue
				
				match = re.search(r'^(\s*)import', line)
				if match:
					line = re.sub(r'^(\s*)import', r'\1#import', line)
					continue

				# CLASS DECLARATION
				className = None
				match = re.search(r'class (?P<name>\w+)', line)
				if match:
					className = match.group('name')
					className = re.compile(className)
				line = re.sub(r'(.*?)\w* class (?P<name>\w+)(.*){.*(?P<nline>\r?\n?)', r'\1def class \g<name>(): \3\g<nline>', line)

				# Adds the parents
				line = re.sub(r'\(\).*extends (?P<parents>(.*))', r'(\g<parents>):', line)

				# Adds the interfaces if there were no parents
				line = re.sub(r'\(\).*implements (?P<contracts>(.*))', r'(\g<contracts>)', line)
				# Adds the interfaces if there were parents
				line = re.sub(r'\((?P<parents>.+?).*implements (?P<contracts>\S*)\s*', r'(\g<parents>,\g<contracts>',line)


				# Operators
				line = re.sub(r'!', 'not ', line)
				line = re.sub(r'&&', 'and', line)
				line = re.sub(r'\|\|', 'or', line)
				line = re.sub(r'try\s*{', 'try:', line)
				line = re.sub(r'catch.*\(\s*(?:final)?\s*(?P<class>\w*Exception)\s+(?P<name>\w*)\)\s*{', r'except \g<class> as \g<name>:', line)
				line = re.sub(r'finally\s*{', 'else:' ,line)

				# Type erasure
				line = re.sub(r'String (.*)', r'\1', line)
				line = re.sub(r'int (.*)', r'\1', line)
				line = re.sub(r'Integer (.*)', r'\1', line)
				line = re.sub(r'[Dd]ouble (.*)', r'\1', line)
				line = re.sub(r'[Ff]loat (.*)', r'\1', line)
				line = re.sub(r'[Bb]oolean (.*)', r'\1', line)
				
				# Variable declaration
				line = re.sub(r'public (.*);', r'\1', line)
				line = re.sub(r'private (.*);', r'\1', line)
				line = re.sub(r'protected (.*);', r'\1', line)
				line = re.sub(r'[A-Z]\w* (?P<vname>\w+)\s?=(?P<val>.*);', r'\g<vname> = \g<val>', line)
				line = re.sub(r';(\s*)$', '\n', line)
				
				line = re.sub(r'while\s*\(','while', line)
				line = re.sub(r'if\s*\(','if ', line)
				line = re.sub(r'}?.*else.*{?', r'else:', line)
				line = re.sub(r'for.*\(.*(\w+)\W*=\W*(\w+)\W*;.*<\W*(\w+);.*\).*\{?.*(?P<nline>\r?\n?)', r'for \1 in range(\2, \3): # FIXME \g<nline>', line)
				line = re.sub(r'for.*\(.*(\w+).*:.*(\w+).*\).*\{?.*(?P<nline>\r?\n?)', r'for \1 in \2:\g<nline>', line)
				
				# Method declaration
				print '*',line
				raw_input('')
				line = re.sub(r'([public |private |protected ])(.*?)(?P<fname>\w*)\(\) *{', r'def \g<fname>(self):', line)
				line = re.sub(r'([public |private |protected ])(.*?)(?P<fname>\w*\()(?P<args>.*\)).+{', r'def \g<fname>self,\g<args>: ', line)
				print '<<',line
				if className:
					line = re.sub(className, '__init__', line)
				
				# Tokens to be completely deleted
				line = re.sub(r'new ', '', line)
				line = re.sub(r'void ', '', line)
				line = re.sub(r'static ', '', line)
				line = re.sub(r'protected ', '', line)
				line = re.sub(r'final ', '', line)
				line = re.sub(r'@\w+', '', line)
				
				# Because of structures like '} else {' or '} catch(Exception e) {' we delete the spaces after the closing bracket
				line = re.sub(r'}\s*', '', line) 
				
				# If no thing remains, make the line blank
				line = re.sub(r'^\s*$', '', line)
				
				line = re.sub(r'//', '#', line)
				line = re.sub(r'/\*|\*/', '"""',  line)
				line = re.sub(r'(\w+)\+\+', r'\1 \+= 1', line)
				line = re.sub(r'(\w+)--', r'\1 -= 1', line)
				line = re.sub(r'this', 'self', line)
				line = re.sub(r'true', 'True', line)
				line = re.sub(r'false', 'False', line)
				line = re.sub(r'\)\s*{(.*)$', r':\1', line)
				line = re.sub(r'(\W)(this)(\W)', r'\1self\3', line)
				line = re.sub(r'(\W)(null)(\W)', r'\1None\3', line)

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
		print os.path.basename(filename)+' is not a java file'
        

def main(argv):
	'''
	First we process options, then we do the code translation from java to python
	'''
	# BASE_DIR is the current working directory
	BASE_DIR = os.getcwd()

	try:
		# Options and arguments processing
		print 'processing opts'
		opts, args = getopt.getopt(argv, "f:d:r", ["file", "dir", "recursive"])
		print 'opts processed: '+ str(opts)
		print 'args processed: '+str(args)
	except getopt.GetoptError:
		# Errors with options and arguments
		print 'Invalid usage'
		print 'Proper usage is java2py [-r] -f fileName | -d dirName '
		sys.exit(-1)

	# Proceeding to the code translation
	for opt,val in opts:
		RECURSIVE = opt in ['-r', '--recursive']
		
		print 'value is '+val
		if opt in ['-d', '--dir']:
			BASE_DIR = os.path.join(BASE_DIR, val)
			processDir(BASE_DIR)
		elif opt in ['-f', '--file']:
			processFile(BASE_DIR, val)
		else:
			os.chdir(BASE_DIR)
			if os.path.isdir(val):
				BASE_DIR = os.path.join(BASE_DIR, val)
				processDir(BASE_DIR)
			else:
				processFile(os.path.join(BASE_DIR, val))

if __name__ == "__main__":
	main(sys.argv[1:])
