#!/usr/bin/python

import operator
import sys

# Parametros en sys.argv

filename = ''

if len(sys.argv) > 2:
	print 'Sintaxis incorrecta. Debe usar el programa del siguiente modo:'
	print 'cuentaPalabras.py [fichero] \n'
	print 'o bien\n'
	print 'python cuentaPalabras.py [fichero]\n'
	print '(Los corchetes ([]) indican la opcionalidad de su contenido)'
elif len(sys.argv) == 1:
	filename = raw_input('Introduzca el nombre exacto del fichero a procesar: ')
else:
	filename = sys.argv[1]
	
dicc = {}

# with cierra el fichero
with open(filename, 'r') as file:
	linea = file.readline()
	linea=linea.replace('\n', '')
	while linea != '':
		for palabra in linea.split():
			if palabra not in dicc.keys():
				dicc[palabra] = 1
			else:
				dicc[palabra] += 1
		linea = file.readline()

total = sum(dicc.values())

listaOrdenada = sorted(dicc.items(), key=operator.itemgetter(1))
listaOrdenada.reverse()



with open('informe.txt', 'w') as file:
	for (palabra,valor) in listaOrdenada:
		file.write(palabra.ljust(15) + '%i  %2.2f %%' % (valor,(valor/float(total)*100.0))+'\n')

