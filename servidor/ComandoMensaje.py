###################################################################
#########NOS REGRESARA EL COMANDO, EL USUARIO Y EL TAMANO##########
###################################################################
def leerMensaje ():    
    Archivo_mensaje = 'mensajes.log'  #RDSS seleccionamos el archivo mensajes   

    archivo = open(Archivo_mensaje, 'r') #RDSS abrimos el archivo mensajes en modo lectura
    for linea in archivo:         #RDSS for para cada line del archivo
        lineaNueva = linea[2:-1] #RDSS seleccionamos solo los caracteres que esten dentro de este rango
        registro = lineaNueva.split('$') #RDSS va a separar cada vez que encuentre una coma
        registro[0] = registro[0].replace('\\x', '')  #RDSS elimina los caracteres que no nos importan
    archivo.close() #Cerramos el archivo
    if len(registro) == 3:    #RDSS identificamos el ramaño de registro para saber si tiene 3 o 2 datos
        return registro[0], registro[1], registro[2] #regresamos Comando, Usuario, Tamaño
    if len(registro) == 2:
        return registro[0], registro[1] , 0 #regresamos comando, usuario, tamaño = 0
