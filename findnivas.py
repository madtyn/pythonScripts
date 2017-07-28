#!/usr/bin/python

import re
import sys, os
import getopt

def transform(inFile, outFile):
	'''
	With a java file as input produces a python file as output
	'''
	processed={}
	processed['elem'] = False
	processed['niva'] = False
	nextElement = ''
	with open(inFile, 'r') as iFile:
		with open(outFile, 'w+') as oFile:
			for oldLine in iFile:
				line = oldLine

				match = re.search(r'<idFactura>(.*)</idFactura>', line)
				if match and not processed['elem']:
					nextElement += re.sub(r'^(\s*)<idFactura>(.*)</idFactura>(\s*)$', r'\2', line) + ';'
					processed['elem'] = True
					continue

				match = re.search(r'<nivaEmisor>(.*)</nivaEmisor>(\s*)$', line)
				if match and not processed['niva']:
					nextElement += re.sub(r'(\s*)<nivaEmisor>(.*)</nivaEmisor>', r'\2', line)
					processed['niva'] = True
					continue

				if processed['elem'] and processed['niva']:
					oFile.write(nextElement)
					nextElement = ''
					for key in processed:
						processed[key]= False



def processFile(filename):
	'''
	Processes a single file
	'''
	# This line makes a regular expression with re.compile() to capture a java file name
	# and then sub() replaces the extension in it with "py"
	outFilename = re.compile(r'(?P<name>.*)\.(?P<ext>\w*)$', re.I).sub(r'\g<name>_out.csv', filename)
	transform(filename, outFilename)


def main(argv):
	'''
	First we process options, then we do the code translation from java to python
	'''
	# BASE_DIR is the current working directory
	BASE_DIR = os.getcwd()

	try:
		# Options and arguments processing
		print('processing opts')
		opts, args = getopt.getopt(argv, "f:", ["file", ])
		print('opts processed: '+ str(opts))
		print('args processed: '+str(args))
	except getopt.GetoptError:
		# Errors with options and arguments
		print('Invalid usage')
		print('Proper usage is findnivas -f fileName  ')
		sys.exit(-1)

	# Proceeding to the code translation
	for opt,val in opts:
		print('value is '+val)
		if opt in ['-f', '--file']:
			print('Entra con '+BASE_DIR)
			processFile(os.path.join(BASE_DIR, val))
		else:
			os.chdir(BASE_DIR)
			processFile(os.path.join(BASE_DIR, val))

if __name__ == "__main__":
	main(sys.argv[1:])
