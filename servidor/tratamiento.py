###################################################################
######### NOS REGRESARA EL TOPIC,  Y EL PAYLOAD   #################
###################################################################
def leerMensaje ():    
    Archivo_mensaje = 'mensajes.log'  #RDSS seleccionamos el archivo mensajes   

    archivo = open(Archivo_mensaje, 'r') #RDSS abrimos el archivo mensajes en modo lectura
    for linea in archivo:         #RDSS for para cada line del archivo
        print (linea)
        lineaNueva = linea[2:-1] #RDSS seleccionamos solo los caracteres que esten dentro de este rango
        print(lineaNueva)
        registro = lineaNueva.split('b Diego&Simon$ b') #RDSS va a separar cada vez que encuentre una coma
        registro[0] = registro[0].replace('\\x', '')  #RDSS elimina los caracteres que no nos importan
        print(registro)
    archivo.close() #Cerramos el archivo
    if len(registro) == 2:
        return registro[0], registro[1] #regresa msg.topic y msg.payload

s = leerMensaje()

print(leerMensaje)