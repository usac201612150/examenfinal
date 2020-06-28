def buscar (usuario, grupo):    
    USUARIOS = 'usuario'  #seleccionamos el archivo usuarios
    datos = []                 #creamos una lista para almacenar los datos de cada linea del archivo

    archivo = open(USUARIOS, 'r') #abrimos el archivo usuarios en modo lectura
    for linea in archivo:         #for para cada line del archivo
        registro = linea.split(',') #va a separar cada vez que encuentre una coma
        registro[-1] = registro[-1].replace('\n', '')  #elimina el salto de linea que encuentra al final de cada linea
        datos.append(registro) #agrega la lista registros dentro de la lista datos
    archivo.close() #Cerramos el archivo

    for i in range(len(datos)):  #For que nos servira para buscar los datos en la lista
        if str(usuario) in datos [i] and str(grupo) in datos[i]:
            return b'\x06' #enviamos un OK 0x06
        else: 
            return b'\x07' #enviamos un NO 0x07

