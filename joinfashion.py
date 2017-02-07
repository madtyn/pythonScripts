#!/usr/bin/python
'''
1.- Comentar lineas del fichero xml
2.- Ejecutar la generacion de servicios
3.- Descomentar lineas del fichero xml
4.- Ejecutar compilacion portlets
5.- Despliegue descomprimiendo fichero .war
	a.- Borrar directorio destino
	b.- Descomprimir a directorio destino
'''

import sys
import os
import re
import zipfile
import getopt

#Directorios relevantes en funcion del sistema operativo
if os.name == 'nt':
	ROOT = 'C:\\'
else:
	ROOT = '/cygdrive/c'
	os.environ['DISPLAY']=':0'
	
'''try:
import Tkinter as tk
root = tk.Tk()
root.withdraw()
tkMessageBox.showinfo("Say Hello", "Hello World")

#Your other choice is to not use tkMessageBox, but instead put your message in the root window. The advantage of this approach is you can make the window look exactly like you want it to look.

import Tkinter as tk
root = tk.Tk()
root.title("Say Hello")
label = tk.Label(root, text="Hello World")
label.pack(side="top", fill="both", expand=True, padx=20, pady=20)
button = tk.Button(root, text="OK", command=lambda: root.destroy())
button.pack(side="bottom", fill="none", expand=True)
root.mainloop()
... except ImportError:
		print 'package not found'
... except _tkinter.TclError:
...     print 'display not configured'
'''
PORTLETS_DIR = os.path.join(ROOT, 'Workspace', 'RRHHJoinFashionLiferay', 'APPWEB-PluginsPortlets')
PORTLETS_WAR_FILE = os.path.join(ROOT, 'Workspace', 'RRHHJoinFashionLiferay', 'APPWEB-PluginsPortlets', 'appweb-portaljoinfashion-portlet', 'target', 'deploy', 'appweb-portaljoinfashion-portlet.war')
PORTLETS_DEPLOY_DIR = os.path.join(ROOT, 'Liferay', 'liferay-portal-6.2-ee-sp3', 'tomcat-7.0.42', 'webapps', 'appweb-portaljoinfashion-portlet')
THEMES_DIR = os.path.join(ROOT, 'Workspace', 'RRHHJoinFashionLiferay', 'APPWEB-PluginsTemas')
THEMES_WAR_FILE = os.path.join(ROOT, 'Workspace\RRHHJoinFashionLiferay', 'APPWEB-PluginsTemas', 'appweb-portaljoinfashion-theme', 'target', 'deploy', 'appweb-portaljoinfashion-theme.war')
THEMES_DEPLOY_DIR = os.path.join(ROOT, 'Liferay', 'liferay-portal-6.2-ee-sp3', 'tomcat-7.0.42', 'webapps', 'appweb-portaljoinfashion-theme')

TOMCAT_DIR = os.path.join(ROOT, 'Liferay', 'liferay-portal-6.2-ee-sp3', 'tomcat-7.0.42')

# Expresiones regulares de lineas de configuracion a comentar/descomentar
TARGET_LINE1 = r'<liferay.plugin.precompile.dir>.*</liferay.plugin.precompile.dir>'
TARGET_LINE2 = r'<liferay.auto.deploy.dir>.*</liferay.auto.deploy.dir>'
TARGET_LINES = [TARGET_LINE1, TARGET_LINE2]
commentsMade = 0

def replaceLine(pattern, replacement, line, adding):
	''' 
	Reemplaza la linea si encaja con la expresion regular 
	y actualiza el numero de comentarios realizados	con el parametro adding
	'''
	global commentsMade
	match = re.search(pattern, line)
	if match:
		line = re.sub(pattern, replacement, line)
		commentsMade += adding
	return line

def commentLine(pattern, line):
	''' Comenta la linea si encaja con la expresion regular y actualiza el numero de comentarios realizados	'''
	# Queremos conservar espacios y retornos de carro antes y despues de la expresion a comentar
	# Si no, se van a juntar varias lineas en una y otros efectos no deseados
	# Asi que capturamos los espacios (seran los grupos \1 y \3), y la expresion deseada (sera el \2)
	lineToComment = r'(\s*)(' + pattern + r')(\s*)$'
	
	# Comentamos rodeando la expresion deseada \2 con <!-- --> 
	# y manteniendo los espacios \1 y \3 en su sitio
	return replaceLine(lineToComment, r'\1<!--\2-->\3', line, +1)


def uncommentLine(pattern, line):
	''' Descomenta la linea si encaja con la expresion regular y actualiza el numero de comentarios realizados	'''
	# Queremos conservar espacios y retornos de carro antes y despues de la expresion a comentar
	# Si no, se van a juntar varias lineas en una y otros efectos no deseados
	# Asi que capturamos los espacios (seran los grupos \1 y \3), y la expresion deseada (sera el \2)
	# Como buscamos la expresion comentada, la expresion debe llevar <!-- --> rodeando al segundo grupo
	lineToComment = r'(\s*)<!--(.*?' + pattern + r'.*?)-->(\s*)$'
	
	# Descomentamos al conservar solo la expresion deseada al no capturar arriba <!-- ni --> descartandolos
	# y manteniendo los espacios \1 y \3 en su sitio
	return replaceLine(lineToComment, r'\1\2\3', line, -1)

def commentLines(line):
	''' Para una linea te texto, prueba a comentarla 
	si contiene cualquiera de los dos tags a comentar (TARGET_LINES)
	'''
	global commentsMade
	if commentsMade < len(TARGET_LINES):
		for targetLine in TARGET_LINES:
			line = commentLine(targetLine, line)
	return line
	
def uncommentLines(line):
	''' 
	Para una linea te texto, prueba a descomentarla 
	si contiene cualquiera de los dos tags a descomentar (TARGET_LINES)
	'''
	global commentsMade
	if commentsMade > 0:
		for targetLine in TARGET_LINES:
			line = uncommentLine(targetLine, line)
	return line
	
def processPomFile(processFunction):
	'''
	Procesa el pom.xml completo linea por linea aplicando la funcion pasada como parametro.
	Dicha funcion recibe una linea de texto.
	'''
	try:
		# Con 'U' en el modo logramos que los retornos de carro sean los universales (tipo Unix)
		with open(os.path.join(PORTLETS_DIR,'pom.xml'), 'r+U') as pomFile:
			lines = pomFile.readlines() # Leemos todo el fichero
			# Nos posicionamos al principio 
			pomFile.seek(0)
			# Y borramos todo a partir del principio para escribir a continuacion
			pomFile.truncate()

			for line in lines:
				# Codigo para comentar las dos lineas
				line = processFunction(line)
				pomFile.write(line)
	except IOError:
		print('Hubo un error al tratar de procesar el pom.xml')

def deleteDirContent(absolutePathToDir):
	''' Con la ruta completa/absoluta del directorio, borra todo su contenido '''
	# Guardamos el directorio actual de trabajo donde estamos situados
	oldDir = os.getcwd()

	# Nos situamos en el directorio padre del que queremos eliminar
	os.chdir(os.path.join(absolutePathToDir, '..'))

	
	# Obtenemos el nombre del directorio a eliminar
	nameLastSubdir = absolutePathToDir.split(os.sep)[-1]
	
	# Eliminamos el directorio y volvemos a crearlo
	if os.name == 'nt':
		execute('rmdir '+nameLastSubdir +' /S /Q')
		execute('md '+nameLastSubdir)
	else:
		execute('rm -rf '+nameLastSubdir)
		execute('mkdir '+nameLastSubdir)
	
	# Restauramos el directorio de trabajo
	os.chdir(oldDir)

def showMessage(msg, title='Aviso'):
	''' Muestra un mensaje en la terminal '''
	print('%s: %s' % (title, msg))
	
def showMessageDialog(msg, title=''):
	''' Muestra una ventana de dialogo con un mensaje y titulo '''
	if os.name == 'nt':
		import ctypes
		ctypes.windll.user32.MessageBoxA(0, msg, title, 0)
	else:
		showMessage(msg, title)

def execute(command):
	''' Ejecuta en terminal un comando '''
	error = os.system(command)
	print('%s ha terminado con codigo %d' % (command, error))
	if error:
		errorMsg = '"%s" ha fallado \nError %s' % (command,str(error))
		processPomFile(uncommentLines)
		showMessageDialog(errorMsg, 'Error')
		print('\n')
		sys.exit(error)

def makePortletServices():
	''' Genera la capa de servicios de portlets '''
	os.chdir(os.path.join(PORTLETS_DIR, 'appweb-portaljoinfashion-portlet'))
	processPomFile(commentLines)
	execute('mvn liferay:build-service -Dmaven.test.skip=true -Dfile.encoding=UTF-8')
	processPomFile(uncommentLines)
	
def installPortlets():
	''' Realiza el install de portlets y su compilacion '''
	os.chdir(PORTLETS_DIR)
	processPomFile(uncommentLines)
	execute('mvn clean package -Plocal -Dmaven.test.skip=true -Dfile.encoding=UTF-8')

def deployTo(targetDir, warFilePath):
	''' Despliegue generalizado '''
	deleteDirContent(targetDir)
	try:
		with zipfile.ZipFile(warFilePath, 'r') as warFile:
			warFile.extractall(targetDir)
	except IOError:
		print('Hubo un problema al desplegar %s en %s' % (warFile, targetDir))
		sys.exit(-2)

def deployPortlets():
	''' Despliegue para portlets '''
	deployTo(PORTLETS_DEPLOY_DIR, PORTLETS_WAR_FILE)

def installThemes():
	''' Realiza el install de temas  '''
	os.chdir(THEMES_DIR)
	if os.name == 'nt':
		execute("mvn clean package -P local,!default -Dmaven.test.skip=true -Dfile.encoding=UTF-8")
	else:
		execute("mvn clean package -P 'local,!default' -Dmaven.test.skip=true -Dfile.encoding=UTF-8")
	
def deployThemes():
	''' Despliegue para portlets '''
	deployTo(THEMES_DEPLOY_DIR, THEMES_WAR_FILE)

def main(argv):
	#os.putenv('MAVEN_OPTS', '-Xms2048m -Xmx3072m -XX:MaxPermSize=3072m')
	os.environ['MAVEN_OPTS']='-Xms2048m -Xmx3072m -XX:MaxPermSize=3072m'
	if os.name == 'nt':
		execute('set MAVEN_OPTS="-Xms2048m -Xmx3072m -XX:MaxPermSize=3072m"')
	else:
		execute('export MAVEN_OPTS="-Xms2048m -Xmx4096m -XX:MaxPermSize=4096m"')
	
	try:
		opts, __ = getopt.getopt(argv, "spt", ["services", "portlets", "themes"])
	except getopt.GetoptError:
		print('Uso invalido')
		sys.exit(-1)
		
	successMsg=''

	if ('-s', '') in opts or '--services' in opts:
		# Generando servicios
		makePortletServices()
		successMsg = 'Servicios generados'
	
	if ('-p', '') in opts or '--portlets' in opts or len(opts) == 0:
		# Limpiamos los directorios temporales de Tomcat antes de nada	
		deleteDirContent(os.path.join(TOMCAT_DIR,'temp'))
		deleteDirContent(os.path.join(TOMCAT_DIR,'work'))
		
		# Instalando y desplegando portlets'
		installPortlets()
		deployPortlets()
		if successMsg:
			successMsg += '. \n'
		successMsg += 'Portlets compilados y desplegados'
	
	if ('-t','') in opts or '--themes' in opts:
		# Instalando y desplegando temas
		installThemes()
		deployThemes()
		if successMsg:
			successMsg += '. \n'
		successMsg += 'Temas compilados y desplegados'
	

	showMessageDialog(successMsg, 'Tarea terminada')
	print('\n')

if __name__ == "__main__":
	main(sys.argv[1:])