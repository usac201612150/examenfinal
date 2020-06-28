import time
from datetime import datetime, timedelta

formato = "%S"
archivo = 'usuarios'
datos = []

def segundo ():
    while True:
        now = datetime.today()
        tiempo = now.strftime(formato)
        return tiempo   

lectura = open(archivo,'r')
for line in lectura:
    registro = line.split(',')
    registro[-1] = registro[-1].replace('\n','')
    datos.append(registro)
lectura.close()

diccionario = {}
for i in range(len(datos)):
    diccionario[datos[i][0]] = [False, int(segundo())]
print(datos)
print(diccionario)

def borrar (diccionario):
    for i in diccionario:
        diccionario[i][0]
        if diccionario[i][1] <= int(segundo())-6:
            diccionario[i] = [False, int(segundo())]
            print(diccionario)


while True:
    x = input('alive: ', )
    h = x.split('$')
    print( h, h[0][1:5], h[1])
    if h[0][1:5] == 'x02':
        print("diccionario 1: ",diccionario[h[1]])
        diccionario[h[1]] = [True, int(segundo())]
        print(diccionario)
    print(diccionario)
    borrar(diccionario)

