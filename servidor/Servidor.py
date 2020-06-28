#############################################################
##########   LIBRERIAS QUE VAMOS A IMPORTAR #################
#############################################################
import paho.mqtt.client as mqtt
import time
import logging
import socket
import binascii
import os 
import threading
from DatosBroker import *
from ConfirmarUsuario import *
from SuscripcionesTopic import *
from ComandoMensaje import *
#############################################################
######################   DEFINICIONES  ##########################
#############################################################
SERVER_IP   = '167.71.243.238'  #RDSS IP DEL SERVIDOR
SERVER_PORT = 9821              #RDSS PUERTO A UTILIZAR TCP
BUFFER_SIZE = 65536             #RDSS CANTIDAD DE BYTES QUE VAMOS A TRANSFERIR EN CADA ENVIO
qos = 2

COMANDOS = 'comandos'
USUARIOS = 'usuarios'
GRUPO = 21
COMANDO_FRR = b'\x02'
COMANDO_ACK = b'\x05'
COMANDO_OK = b'\x06'
COMANDO_NO = b'\x07'

Archivo_mensajes = 'mensajes.log' #RDSS aca vamos a guardar los mensajes que llegan de los topics
############################################################
#############CONFIGURAMOS ES LOGGING #######################
############################################################
#Configuracion inicial de logging
logging.basicConfig(
    level = logging.INFO, 
    format = '[%(levelname)s] (%(threadName)-10s) %(message)s'
    )
##############################################################
################### CLASE SERVIDOR TCP #######################
##############################################################
class ServerTCP (object):
    def __init__(self):
        logging.basicConfig(
            level = logging.INFO, 
            format = '[%(levelname)s] (%(threadName)-10s) %(message)s'
        )
        self.parametrosServer()
    
    def inicioServerTCP(self, ip, puerto, sock, usuariocola):
        server_address = (ip,puerto)#RDSS LE DAMOS LOS PARAMETROS DE IP Y PUERTO
        logging.info('Conectando a {} en el puerto {}'.format(*server_address))
        sock.bind(server_address) #RDSS Levanta servidor con parametros especificados
        sock.listen(usuariocola) #RDSS El argumento indica la cantidad de conexiones en cola

    def parametrosServer(self):
        ip = SERVER_IP
        puerto = SERVER_PORT
        usuariocola = 10 #RDSS indica la cantidad de conexiones en cola
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #RDSS LE INDICAMOS QUE VAMOS A TRABAJAR CON IPV4 Y CON TCP
        self.inicioServerTCP(ip,puerto,sock,usuariocola)
        
##############################################################
######################## CLASE MQTT ##########################
##############################################################

class claseMQTT (object):
    def __init__(self):
        logging.basicConfig(
            level=logging.INFO,
            format='[%(levelname)s](%(threadName)-10s) %(message)s'
        )
        self.logging=logging
        self.ConfiguracionMQTT()
        self.Archivo_mensajes = Archivo_mensajes

    def ConfClienteMQTT(self, address, port, usuario, contrasena):
        self.mqttc = mqtt.Client(clean_session=True)
        self.mqttc.on_message = self.on_message
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_publish = self.on_publish
        self.mqttc.username_pw_set(usuario,contrasena)
        self.mqttc.connect(address,port)

    def suscripcionesTopic(self):      #creamos una lista para almacenar los datos de cada linea del archivo
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
            NuevoSuscriptor = COMANDOS+'/'+str(GRUPO)+'/'+str(datos[i][0]) #agragamos el usuario a la cadena para suscribirnos al topic
            Nusuarios.insert(0,NuevoSuscriptor) #le indicamos que vamos a agregar la suscripcion al principio de la lista Nusuarios y corremos qos
            TuplaNusuarios = tuple(Nusuarios)   #convertimos la lista a tuplas 
            suscripciones.append(TuplaNusuarios) #agregamos la tupla a la lista de suscripciones
        self.mqttc.subscribe(suscripciones) #nos suscribimos a todos los usuarios que estan en la lista
        self.mqttThread=thread.Thread(target=self.mqttc.loop_start,name = 'Recepcion Comandos MQTT', daemon = True)
        self.mqttThread.start()

    def ConfiguracionMQTT(self):
        direccion = MQTT_HOST
        puerto = MQTT_PORT
        usuario = MQTT_USER
        contrasena = MQTT_PASS
        self.ConfClienteMQTT(direccion,puerto,usuario,contrasena)
        self.SuscripcionesTopic()

    def publishData(self, topicName, data): #Publicador simple
        self.mqttc.publish(topic = topic, payload = data,qos=0)

    def ACK(self, qos=0, retain=False):
        topic = COMANDOS+'/'+str(GRUPO)+'/'
        mensaje = COMANDO_ACK+b'$'+bytes(usuariogrupo,'utf-8')
        self.mqttc.publish(topic,mensaje,qos,retain)

    def on_connect(client, userdata, rc): 
        logging.info("Conectado al broker")  #Callback que se ejecuta cuando nos conectamos al broker

    def on_message(client, userdata, msg): #Callback que se ejecuta cuando llega un mensaje al topic suscrito
        logging.info("Ha llegado el mensaje al topic: " + str(msg.topic))  #Se muestra en pantalla informacion que ha llegado
        logging.info("El contenido del mensaje es: " + str(msg.payload))   #vamos a almacenar el mensaje en un archivo.
        MensajeRecibido = 'echo '+str(msg.payload) + ' > '+ Archivo_mensajes
        os.system(MensajeRecibido)

    def on_publish(client, userdata, mid):   #Handler en caso se publique satisfactoriamente en el broker MQTT
        publishText = "Publicacion satisfactoria"
        logging.debug(publishText)

######################################################
## DATOS RECIBIDOS COMANDO, USUARIO, PESO ARCHIVO#####
######################################################
mqttcomando, mqttusuario, mqtttamano = leerMensaje()      

########## CLASE COMANDOS #################
class comandosmqtt (object):

    #METODO CONSTRUCTOR
    def __init__ (self, comando, IDusuario, tamano):
        self.comando = comando
        self.IDusuario = IDusuario
        self.tamano = tamano

    def Alive_Ack (self):
        comando = b'\x05'
        usuario = bytes(self.IDusuario,'utf-8')
        tramaACK= comando+b'$'+usuario
        topicComandos = '21/'+self.IDusuario
        if self.comando == '02':
            return publishData('comandos',topicComandos,tramaACK, qos = 0, retain = False)
    def FRR (self):
        comando = b'\x02'
        usuario = bytes(self.IDusuario,'utf-8')
        tamano = bytes(self.tamano,'utf-8')
        tramaFRR = comando+b'$'+usuario+b'$'+tamano
        topicComandos = '21/'+self.IDusuario
        if self.comando == '03':
            return publishData('comandos',topicComandos,tramaFRR, qos = 0, retain = False)


########## ENVIAMOS A LA CLASE comandosmqtt##########
Accion = comandosmqtt(mqttcomando, mqttusuario, mqtttamano)

def RecepcionAudio ():
    while True:
        try:
            while True:       
                buff = sock.recv(BUFFER_SIZE)
                archivo = open('notadevoz.wav','wb')
                while buff:
                    buff = sock.recv(BUFFER_SIZE)
                    archivo.write(buff)
                archivo.close()
        finally:
            sock.close()

def TransmisioAudio():
    try:
        while True:
            conn, addr = sock.accept()
            logging.info("conexion establecida desde: ", addr)
            logging.info("enviando audio")
            with open('notadevoz.wav','rb') as env:
                conn.sendfile(env, 0)
                env.close()
            conn.close()
    finally:
        sock.close()




while True:
    # Esperando conexion
    print('Esperando conexion remota')
    connection, clientAddress = sock.accept()
    try:
        print('Conexion establecida desde', clientAddress)

        # Se envia informacion en bloques de BUFFER_SIZE bytes
        # y se espera respuesta de vuelta
        while True:
            data = connection.recv(BUFFER_SIZE) #data ordena a tcp partir la informacion en cierto numero de bytes
            print('Recibido: {!r}'.format(data)) #decodificamos de binario a str
            if data: #Si se reciben datos (o sea, no ha finalizado la transmision del cliente)
                print('Enviando data de vuelta al cliente')
                connection.sendall(data) #envia todo lo que recibimos al cliente
            else:
                print('Transmision finalizada desde el cliente ', clientAddress)
                break
    
    except KeyboardInterrupt:
        sock.close()
        logging.warning("Desconectando del broker...")

    finally:
        # Se baja el servidor para dejar libre el puerto para otras aplicaciones o instancias de la aplicacion
        client.loop_stop() #Se mata el hilo que verifica los topics en el fondo
        client.disconnect() #Se desconecta del broker
        logging.info("Desconectado del broker. Saliendo...")
        connection.close()
        print('\n\nConexion finalizada con el servidor')