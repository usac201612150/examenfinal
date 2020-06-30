#############################################################
##########   LIBRERIAS QUE VAMOS A IMPORTAR #################
#############################################################
import paho.mqtt.client as mqtt
import time
import logging
import socket
import binascii
import os 
import sys
import threading
from DatosBroker import *
from datetime import datetime, timedelta
#############################################################
######################   DEFINICIONES  ##########################
#############################################################
SERVER_IP   = '167.71.243.238'  #RDSS IP DEL SERVIDOR
SERVER_PORT = 9821              #RDSS PUERTO A UTILIZAR TCP
BUFFER_SIZE = 65536             #RDSS CANTIDAD DE BYTES QUE VAMOS A TRANSFERIR EN CADA ENVIO
qos = 2

COMANDOS = 'comandos'
USUARIOS = 'usuarios'
SALAS = 'salas'
GRUPO = 21

COMANDO_FRR = b'\x02'
COMANDO_ACK = b'\x05'
COMANDO_OK = b'\x06'
COMANDO_NO = b'\x07'

##############################################################
######################## CLASE MQTT ##########################
##############################################################
#logging.basicConfig(
#                    level=logging.INFO,
#                    format='[%(levelname)s](%(threadName)-10s) %(message)s'
#                    )

class claseMQTT (object):
    def __init__(self):
        logging.basicConfig(
            level=logging.INFO,
            format='[%(levelname)s](%(threadName)-10s) %(message)s'
        )
        self.logging=logging
        #self.inicioMQTT()  #DRRP lo voy a inicializar abajo
        self.ServerTCP = ServerTCP()
        self.ServerTCP.parametrosServer()
        self.diccionario, self.listausuarios, self.listasalas = self.DiccReg(USUARIOS,SALAS)

    def ConfClienteMQTT(self, address, port, usuario, contrasena): # RDSS setupmqtt, nos conectamos al broker
        self.mqttc = mqtt.Client(clean_session=True)
        self.mqttc.on_message = self.on_message
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_publish = self.on_publish
        self.mqttc.username_pw_set(usuario,contrasena)
        self.mqttc.connect(address,port)

    def suscripcionesTopic(self):
        datos = []      #RDSS creamos una lista para almacenar los datos de cada linea del archivo
        suscripciones = []         #RDSS creamos la lista donde almacenaremos las tuplas de los topics
        qos = 2                    #RDSS qos valor que nos servira para indicar que forma de transferencia preferimos

        archivo = open(USUARIOS, 'r') #RDSS abrimos el archivo usuarios en modo lectura
        for linea in archivo:         #RDSS for para cada line del archivo
            registro = linea.split(',') #RDSSva a separar cada vez que encuentre una coma
            registro[-1] = registro[-1].replace('\n', '')  #RDSS elimina el salto de linea que encuentra al final de cada linea
            datos.append(registro) #RDSS agrega la lista registros dentro de la lista datos
        archivo.close() #RDSS Cerramos el archivo

        for i in range(len(datos)):  #RDSS For que nos recorre la lista datos
            Nusuarios = [qos]        #RDSS creamos una lista para los N usuarios con el valor de qos ya definido
            NuevoSuscriptor = COMANDOS+'/'+str(GRUPO)+'/'+str(datos[i][0]) #RDSS agragamos el usuario a la cadena para suscribirnos al topic
            Nusuarios.insert(0,NuevoSuscriptor) #RDSS le indicamos que vamos a agregar la suscripcion al principio de la lista Nusuarios y corremos qos
            TuplaNusuarios = tuple(Nusuarios)   #RDSS convertimos la lista a tuplas 
            suscripciones.append(TuplaNusuarios) #RDSS agregamos la tupla a la lista de suscripciones
        self.mqttc.subscribe(suscripciones) #RDSS nos suscribimos a todos los usuarios que estan en la lista
        #self.mqttc.loop_start()    DRRP la idea era que corriera en el hilo principal, pero no jalo entonces lo voy a meter a un hilo demonio
        self.mqttThread=threading.Thread(target=self.mqttc.loop_start,name="MQTT",daemon=True)
        self.mqttThread.start()
        
        
        #hiloAlives = threading.Thread(name="hiloAlives", DRRP lo voy a iniciar abajo
        #                            target=self.Alives,
        #                            daemon=True
        #                            )
        #hiloAlives.start()

    def inicioMQTT(self): #RDSS datos e inicio del clienteMQTT
        direccion = MQTT_HOST
        puerto = MQTT_PORT
        usuario = MQTT_USER
        contrasena = MQTT_PASS
        self.ConfClienteMQTT(direccion,puerto,usuario,contrasena)
        self.suscripcionesTopic()
        #DRRP el hilo del alive tambien va ser demonio
        #****************descomentar lo siguinete***************
        #*******************************************************
        self.theylive=threading.Thread(target=self.Alives, name="Alive", daemon=True)
        self.theylive.start()
        self.interfaz()

    def publishData(self, topic, data): #RDSS Publicador simple
        self.mqttc.publish(topic = topic, payload = data,qos=0)


    def recepcionMensaje(self, data):
        data=(str(data[0],data[1])) #RDSS topic en [0]   , codigo$usuarioID $tamaño
        datos = []
        datos = data[1].decode().split('$')
        Ingresotopic = []
        Ingresotopic = data[0].decode().split('/')
        emisor = Ingresotopic[2]
        self.emisormensaje=emisor
        if len(datos) == 3: #RDSS si se recibieron 3 datos comando, usuario, tamaño
            ComandoRecibido = datos[0]
            self.usuariodestino = datos[1]
            self.tamanoarchivo = datos[2]
        elif len(datos) == 2: #RDSS si se recibieron 2 datos comandos, usuario
            ComandoRecibido = datos[0]
            self.usuariovivo = datos[1]
        
        if ComandoRecibido == '\x04':  #RDSS verificamos si es un mensaje de ALIVE
            self.cambiodeestado(self.usuariovivo) #cambiamos de estado en el diccionario 
            #logging.info('enviar loggin')
            self.ACK(self.usuariovivo)     #RDSS Enviamos un ACK al client
        elif ComandoRecibido == '\x03' and len(self.usuariodestino)==9:  #RDSS verificamos si es un solicitud de transferencia a un usuario
            self.OKusuario(self.usuariodestino,self.emisormensaje,self.tamanoarchivo)
        elif ComandoRecibido == '\x03' and len(self.usuariodestino)==5: #RDSS verificamos si es una solicitud de transferencia a una sala
            self.OKsalas(self.usuariodestino, self.emisormensaje,self.tamanoarchivo)
                #self.NotiparaEnviar(usuariogrupo, tamañoarchivo)
    
    def ACK(self, usuariogrupo, qos=0, retain=False): #RDSS publica un ACK en el topic
        topic = COMANDOS+'/'+str(GRUPO)+'/'+self.usuariovivo
        mensaje = COMANDO_ACK+b'$'+bytes(self.usuariovivo,'utf-8')
        self.mqttc.publish(topic,mensaje,qos,retain)

    def OK(self, usuariogrupo, qos = 0, retain=False): #RDSS le manda un OK si se cumplen las condiciones
        topic = COMANDOS+'/'+str(GRUPO)+'/'+usuariogrupo
        mensaje = COMANDO_OK+b'$'+bytes(usuariogrupo,'utf-8')
        self.mqttc.publish(topic,mensaje,qos,retain)

    def NO(self, usuariogrupo, qos = 0, retain=False): #RDSS manda un NO si no se cumplen las condiciones
        topic = COMANDOS+'/'+str(GRUPO)+'/'+usuariogrupo
        mensaje = COMANDO_NO+b'$'+bytes(usuariogrupo,'utf-8')
        self.mqttc.publish(topic,mensaje,qos,retain)  

    def FRR(self, usuariogrupo,tamanoarchivo, qos = 0, retain=False):#RDSS manda una solicitud de FRR al destinatario
        topic = COMANDOS+'/'+str(GRUPO)+'/'+usuariogrupo
        mensaje = COMANDO_FRR+b'$'+bytes(usuariogrupo,'utf-8')+bytes(tamanoarchivo,'utf-8')
        self.mqttc.publish(topic,mensaje,qos,retain)

    def on_connect(self, client, userdata, rc): 
        logging.info("Conectado al broker")  #Callback que se ejecuta cuando nos conectamos al broker

    def on_message(self, client, userdata, msg): #Callback que se ejecuta cuando llega un mensaje al topic suscrito
        self.recepcionMensaje((msg.topic,msg.playload))

    def on_publish(self, client, userdata, mid):   #Handler en caso se publique satisfactoriamente en el broker MQTT
        publishText = "Publicacion satisfactoria"
        logging.info(publishText)   

    def segundo (self): #RDSS lo utilizaremos para obtener el segundo actual
        formato = "%S"
        now = datetime.today()
        tiempo = now.strftime(formato)
        return tiempo  

    def DiccReg (self,ArchivoUsuarios, ArchivoSalas): #RDSS nos dara un diccionario, una lista de usuarios y una lista de salas
        #RDSS nos sirve para obtener los datos del archivo usuarios
        datos = []
        datossala = []
        lectura = open(ArchivoUsuarios,'r')
        for line in lectura:
            registro = line.split(',')
            registro[-1] = registro[-1].replace('\n','')
            datos.append(registro)
        lectura.close()
        diccionario = {}      #RDSS nos sirve para crear el diccionario a partir de la lista de datos
        for i in range(len(datos)):
            diccionario[datos[i][0]] = [False, int(self.segundo())]
        #RDSS vamos a hacer una lista con todas las salas validas para el grupo 21S
        leer = open(ArchivoSalas,'r')
        salas = []
        for linea in leer:
            salas.append(linea)
        leer.close()
        for i in range(len(salas)):
            salas[i] = salas[i].replace('\n','')
        return diccionario, registro, salas #RDSS Regresamos un Diccionario para alives, Lista de usuarios, Lista de salas

    def borrar (self, diccionario): #RDSS estara verificando quienes tienen 6 o mas de 6 segundos y les cambiara el estado
        for i in diccionario:    
            if diccionario[i][1] <= int(self.segundo())-6:
                diccionario[i] = [False, int(self.segundo())]

    def cambiodeestado (self, usuariosID): #RDSS cambia de estado para el usuario en el diccionario a un TRUE
        self.diccionario[usuariosID] = [True, int(self.segundo())]

    def Alives(self):
        while True:
            for i in self.diccionario:
                if self.diccionario[i][0]: #[trueofalse]
                    usuariosID = self.diccionario[i]
                    topic = COMANDOS+'/'+str(GRUPO)+'/'+usuariosID
                    mensaje = COMANDO_ACK+b'$'+bytes(usuariosID,'utf-8')
                    self.mqttc.publish(topic,mensaje)
                self.borrar(self.diccionario)
    
    def OKusuario(self, usuarioID, emisor, tamanoarchivo):
        for i in range(len(self.listausuarios)): #RDSS lo utilizamos para recorrer la lista de usuarios
            if (usuarioID in self.listausuarios[i]) and (self.diccionario[usuarioID][0]): #RDSS verificamos si el destinatario esta en la lista y si está activo
                usuariovalido = True
        if usuariovalido:
            self.OK(emisor)  #RDSS enviamos el acuse de OK al emisor
            self.FRR(usuarioID, tamanoarchivo)
            self.Audiothread=threading.Thread(name="Audio",target=self.ServerTCP.RecepcionAudio,daemon=False)
            self.Audiothread.start()
        else:
            self.NO(emisor)
        ############**********Tanto aqui como en ok salas al final tiene que ir la activacion del hilo de recepcion*****####



    def OKsalas(self, sala, emisor,tamanoarchivo):#RDSS verificamos las condiciones para la transferencia a una sala
        usuariosActivos = 0  #RDSS contador que nos servira para saber cuantas personas de la sala estan activas
        if sala in self.listasalas: #RDSS Nos indica si es una sala valida para dentro de 21S01 a 21S99
            for i in range(len(self.listausuarios)): #RDSS recorremos la lista de usuarios 
                if (emisor in self.listausuarios[i]) and (sala in self.listausuarios[i]):#RDSS buscamos si el emisor pertenece a la sala a donde quiere enviar
                    for j in range(len(self.listausuarios)): #volvemos a recorrer la lista de usuarios pero ahora para buscar los usuarios de la sala
                        if (sala in self.listausuarios[j]) and self.diccionario[self.listausuarios[j][0]][0]: #si la sala esta en cierta linea 201612150,Rubén Simon, 21S01
                            usuariosActivos = usuariosActivos + 1 #si está activo va a sumar 1 al contador
                    if usuariosActivos > 0: #RDSS si hay mas de 1 cliente activo enviara un ok, enviara un FRR y emepzara la emision de audio 
                        self.OK(emisor)
                        self.FRR(sala,tamanoarchivo)
                        logging.info("Espera de audio")
                        self.Audiothread=threading.Thread(name="Audio",target=self.ServerTCP.RecepcionAudio,daemon=False)
                        self.Audiothread.start()
                    else:
                        self.NO(emisor)

    #DRRP   el servidor no necesita interfaz pero me va servir para ver donde se esta trabando el
    #       programa, muy probablemente lo deje así 

    def interfaz(self):
        while True:
            salida = input("Si desea salir ingrese la palabra 'salir': ") #DRRP como input es una funcion bloqueante 
            if salida=="salir":                                            #     segun yo debería ejecutarse una vez
                logging.warning("Esta por salir del servidor, los servicios se caeran")#a menos que alguien la toque
                if self.mqttThread.is_alive():                            #     de esa forma da chance a hacer lo demaas
                    self.mqttThread._stop()
                self.mqttc.disconnect()
                sys.exit()
                    
                


##############################################################
################### CLASE SERVIDOR TCP #######################
##############################################################
class ServerTCP (object):
    def __init__(self):
        logging.basicConfig(
            level = logging.INFO, 
            format = '[%(levelname)s] (%(threadName)-10s) %(message)s'
        )
    
    def inicioServerTCP(self, ip, puerto, sock, usuariocola):
        server_address = (ip,puerto)#RDSS LE DAMOS LOS PARAMETROS DE IP Y PUERTO
        #logging.info('Conectando a {} en el puerto {}'.format(*server_address))
        self.sock.bind(server_address) #RDSS Levanta servidor con parametros especificados
        self.sock.listen(usuariocola) #RDSS El argumento indica la cantidad de conexiones en cola

    def parametrosServer(self):
        ip = SERVER_IP
        puerto = SERVER_PORT
        self.BUFFER_SIZE=BUFFER_SIZE
        usuariocola = 10 #RDSS indica la cantidad de conexiones en cola
        self.sock = socket.socket() #RDSS LE INDICAMOS QUE VAMOS A TRABAJAR CON IPV4 Y CON TCP
        self.inicioServerTCP(ip,puerto,self.sock,usuariocola)

    def RecepcionAudio (self):                          #DRRP metodos de recepcion de audio y envio arreglados
        try:
            while True:
                conn, addr= self.sock.accept()
                buff=conn.recv(self.BUFFER_SIZE)
                archivo=open("audiotransmision.wav","wb")
                while buff:
                    archivo.write(buff)
                    buff=conn.recv(self.BUFFER_SIZE)
                archivo.close()
                conn.close()
        finally:
            self.TransmisioAudio()
                

    def TransmisioAudio(self):
        try:
            while True:
                conn, addr = self.sock.accept()
                logging.info("conexion establecida desde: ", addr)
                logging.info("enviando audio")
                with open('audiotransmision.wav','rb') as env:
                    conn.sendall(env, 0)
                    env.close()
                conn.close()
        finally:
            logging.info("Enviado")


examenproyectos980=claseMQTT()
examenproyectos980.inicioMQTT()


"""""
Tenemos implementado el servidor y el cliente mqtt en clases, tenemos el protocolo de negociacion
pero tuvimos problemas con la ejecucion del servidor, al momento de pasar a clases todo, tuve problemas,
no supe como hacer para iniciar y que se quedara ejecutando. intentamos poner una "interfaz" 
para saber que estaba pasando y no pudimos tener más detalles. hicimos algunas pruebas publicando
un mensaje fijo para ver si se suscribia o si conectaba al broker, y si pudimos ver que estuvo enviando 
el mensaje, pero no nos saltaba ningun loggin de que se estaba corriendo correctamente. trate de armar
el servidor por partes pero de la misma forma no supe como mantener ejecutado siempre la clase.
"""""