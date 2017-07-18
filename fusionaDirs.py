import os, filecmp, shutil

BASE_DIR = os.getcwd()


listaDirs = [x for x in os.listdir(BASE_DIR) if os.path.isdir(x)]


def moveFiler(sourceDir, destinyDir):
	'''	This function will move all files from the Xxx dir to the xxx dir trying not to overwrite any of them.

	input: Relative path to the directory which we are going to replicate
	output: None
	postcondition: All distinct files remain and all duplicated files get erased.'''

	fileList = [i for i in os.listdir(sourceDir) if os.path.isfile(os.path.join(sourceDir, i))]
	dirList = [j for j in os.listdir(sourceDir) if os.path.isdir(os.path.join(sourceDir, j))]

	print('files: ', len(fileList), 'subdirs: ', len(dirList))

	for actualFile in fileList:
		# No existe fichero con el mismo nombre => copiamos
		if not os.path.exists(os.path.join(destinyDir, actualFile)):
			#print("mv "+os.path.join(sourceDir,actualFile)+" "+destinyDir)
			shutil.move(os.path.join(sourceDir,actualFile),destinyDir)
		# Existe fichero con mismo nombre, comprobamos y si no es igual => Copiamos renombrando
		elif not filecmp.cmp(os.path.join(sourceDir,actualFile), os.path.join(destinyDir,actualFile)):
			destinyFile=actualFile.split('.')
			destinyFile[0]=actualFile[0]+'Bis'
			destinyFile='.'.join(actualFile)
			#print('mv '+os.path.join(sourceDir,actualFile)+' '+destinyDir)
			shutil.move(os.path.join(sourceDir,actualFile),os.path.join(destinyDir,destinyFile))

	for actualDir in dirList:
		print('Procesando ', os.path.join(sourceDir, actualDir))
		if not os.path.exists(os.path.join(destinyDir, actualDir)):
			#print('mkdir '+ os.path.join(destinyDir, actualDir))
			os.mkdir(os.path.join(destinyDir, actualDir))

		moveFiler(os.path.join(sourceDir,actualDir), os.path.join(destinyDir,actualDir))
		#print('rmtree '+os.path.join(sourceDir,actualDir))
		shutil.rmtree(os.path.join(sourceDir,actualDir))


# Programa principal
for upperDir in listaDirs:
	if os.path.isdir(upperDir) and upperDir[0].isupper():
		# El directorio empieza por mayuscula
		lowerDir = upperDir[0].lower()+upperDir[1:];
		if lowerDir in listaDirs:
			# Existe el correspondiente con minuscula, que sera el destino
			moveFiler(upperDir, lowerDir)
			#print 'rmtree '+upperDir
			shutil.rmtree(upperDir)
