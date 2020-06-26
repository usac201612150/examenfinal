#############################################################
##########   LIBRERIAS QUE VAMOS A IMPORTAR #################
#############################################################
import paho.mqtt.client as mqtt
import time
import logging
import socket
import binascii
import os 
from DatosBroker import *
from ConfirmarUsuario import *
from SuscripcionesTopic import *
from ComandoMensaje import *
#############################################################
###########   DATOS DEL SERVIDOR   ##########################
#############################################################
SERVER_IP   = '167.71.243.238'  #RDSS IP DEL SERVIDOR
SERVER_PORT = 9821              #RDSS PUERTO A UTILIZAR TCP
BUFFER_SIZE = 65536             #RDSS CANTIDAD DE BYTES QUE VAMOS A TRANSFERIR EN CADA ENVIO

#RDSS Se crea socket TCP
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #RDSS LE INDICAMOS QUE VAMOS A TRABAJAR CON IPV4 Y CON TCP

#RDSS Se conecta al puerto donde el servidor se encuentra a la escucha
server_address = (SERVER_IP, SERVER_PORT)   #RDSS LE DAMOS LOS PARAMETROS DE IP Y PUERTO
print('Conectando a {} en el puerto {}'.format(*server_address))
sock.bind(server_address)  #RDSS Levanta servidor con parametros especificados

# Habilita la escucha del servidor en las interfaces configuradas
sock.listen(10) #RDSS El argumento indica la cantidad de conexiones en cola


############################################################
#############CONFIGURAMOS ES LOGGING #######################
############################################################
#Configuracion inicial de logging
logging.basicConfig(
    level = logging.INFO, 
    format = '[%(levelname)s] (%(threadName)-10s) %(message)s'
    )

##############################################################
################### CONFIGURACION MQTT #######################
##############################################################

Archivo_mensajes = 'mensajes.log' #RDSS aca vamos a guardar los mensajes que llegan de los topics

#Callback que se ejecuta cuando nos conectamos al broker
def on_connect(client, userdata, rc):
    logging.info("Conectado al broker")

#Callback que se ejecuta cuando llega un mensaje al topic suscrito
def on_message(client, userdata, msg):
    #Se muestra en pantalla informacion que ha llegado
    logging.info("Ha llegado el mensaje al topic: " + str(msg.topic))
    logging.info("El contenido del mensaje es: " + str(msg.payload))
    #vamos a almacenar el mensaje en un archivo.
    MensajeRecibido = 'echo '+str(msg.payload) + ' > '+ Archivo_mensajes
    os.system(MensajeRecibido)

#Handler en caso se publique satisfactoriamente en el broker MQTT
def on_publish(client, userdata, mid): 
    publishText = "Publicacion satisfactoria"
    logging.debug(publishText)

###################################################################
client = mqtt.Client(clean_session=True) #Nueva instancia de cliente
client.on_connect = on_connect #Se configura la funcion "Handler" cuando suceda la conexion
client.on_message = on_message #Se configura la funcion "Handler" que se activa al llegar un mensaje a un topic subscrito
client.on_publish = on_publish #Se configura la funcion "Handler" que se activa al publicar algo
client.username_pw_set(MQTT_USER, MQTT_PASS) #Credenciales requeridas por el broker
client.connect(host=MQTT_HOST, port = MQTT_PORT) #Conectar al servidor remoto

#Nos conectaremos a distintos topics:
qos = 2
######################################################
########### SUSCRIPCION A LOS TOPIC ##################
######################################################

#Subscripcion simple con tupla (topic,qos)
#utilizamos suscripcionesTopic() porque nos arroja todos los usuarios permitidos a partir del archivo usuarios.txt
client.subscribe(suscripcionesTopic()) #nos suscribimos a todos los usuarios que estan en la lista
#######################################################
#Publicador simple
def publishData(topicRoot, topicName, value, qos = 2, retain = False):
    topic = topicRoot + "/" + topicName
    client.publish(topic, value, qos, retain)


#Iniciamos el thread (implementado en paho-mqtt) para estar atentos a mensajes en los topics subscritos
client.loop_start()
#client.loop_forever()

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
    try:
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