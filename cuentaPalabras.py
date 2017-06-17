#!/usr/bin/python3

import operator
import sys
import re
from collections import defaultdict


def main():
    '''
    Flujo principal del programa
    '''
    filename = ''
    dicc = defaultdict(int)  # Si no hay clave, se utiliza int para inicializarla a 0 y recuperarla

    # Parametros en sys.argv
    if len(sys.argv) > 2:
        print('Sintaxis incorrecta. Debe usar el programa del siguiente modo:')
        print('cuentaPalabras.py [fichero] \n')
        print('o bien\n')
        print('python cuentaPalabras.py [fichero]\n')
        print('(Los corchetes ([]) indican la opcionalidad de su contenido)')
        exit(2)
    elif len(sys.argv) == 1:
        filename = input('Introduzca el nombre exacto del fichero a procesar: ')
        exit(1)
    else:
        filename = sys.argv[1]

    # with cierra el fichero
    with open(filename, 'r') as fdesc:
        linea = fdesc.readline().replace('\n', '')
        while linea != '':
            for palabra in re.findall(r'\b\w+\b', linea):
                dicc[palabra] += 1
            linea = fdesc.readline()

    total = sum(dicc.values())
    print(total)
    listaOrdenada = sorted(list(dicc.items()), key=operator.itemgetter(1), reverse=True)

    with open('informe.txt', 'w') as foutput:
        for (palabra, valor) in listaOrdenada:
            foutput.write('{0!s: <20} {1:d}  {2:2.2%}\n'.format(palabra, valor, valor / total))


if __name__ == '__main__':
    main()
