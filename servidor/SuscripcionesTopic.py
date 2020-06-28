def suscripcionesTopic ():    
    USUARIOS = 'usuarios'  #seleccionamos el archivo usuarios.txt
    datos = []                 #creamos una lista para almacenar los datos de cada linea del archivo
    suscripciones = []         #creamos la lista donde almacenaremos las tuplas de los topics
    qos = 2                    #qos valor que nos servira para indicar que forma de transferencia preferimos

    archivo = open(USUARIOS, 'r') #abrimos el archivo usuarios en modo lectura
    for linea in archivo:         #for para cada line del archivo
        registro = linea.split(',') #va a separar cada vez que encuentre una coma

        registro[-1] = registro[-1].replace('\n', '')  #elimina el salto de linea que encuentra al final de cada linea

        datos.append(registro) #agrega la lista registros dentro de la lista datos

    archivo.close() #Cerramos el archivo

    for i in range(len(datos)):  #For que nos recorre la lista datos
        Nusuarios = [qos]        #creamos una lista para los N usuarios con el valor de qos ya definido
        NuevoSuscriptor = "comandos/21/"+str(datos[i][0]) #agragamos el usuario a la cadena para suscribirnos al topic
        Nusuarios.insert(0,NuevoSuscriptor) #le indicamos que vamos a agregar la suscripcion al principio de la lista Nusuarios y corremos qos
        TuplaNusuarios = tuple(Nusuarios)   #convertimos la lista a tuplas 
        suscripciones.append(TuplaNusuarios) #agregamos la tupla a la lista de suscripciones
    
    return suscripciones #retornamos la lista de suscripciones a partir del archivo usuarios.txt

