########################################################################## 
####################        LIBRERIAS               ###################### 
##########################################################################
import paho.mqtt.client as mqtt          
import logging                          
import time
import os
import threading
import sys
import socket
##########################################################################
####################         DEFINICIONES           ######################
########################################################################## #DRRP
grupo=21

MQTT_HOST = "167.71.243.238"            #Necesarios para MQTT
MQTT_PORT = 1883
MQTT_USER = "proyectos"
MQTT_PASS = "proyectos980"
qos = 2

TCP_HOST="167.71.243.238"               #Necesarias para la transferencia de archivos
TCP_PORT=9821 
BUFFER_SIZE=64*1024

ItLives=2                               #2segundos para ALIVE
AmIDead=0.1                             #0.1segundos para ALIVE
dead=0                                  #Contador de ALIVE
EstoyMuriendo=False                     #Bandera de ALIVE

COMANDOS="comandos"                     #Definicion para archivos
USUARIOS="usuarios"
SALAS="salas"


class MyMQTTClass(object):                                                  #DRRP   Clase que maneja el proceso principal
    def __init__(self):                                                     #       Configuracion de las instancias
        logging.basicConfig(                                                #       Indica como trabajara el logging
            level=logging.INFO,
            format='[%(levelname)s] (%(threadName)-10s) %(message)s'
        )
      
    def setupMQTTClient(self,address,port,usuario,contraseña):              #DRRP   Configuraciones iniciales del cliente de MQTT
        self.userid=self.Whatsmyname()
        self.mqttc=mqtt.Client(clean_session=True)
        self.mqttc.on_message=self.on_message
        self.mqttc.on_connect=self.on_connect
        self.mqttc.on_publish=self.on_publish
        self.mqttc.username_pw_set(usuario,contraseña)
        self.mqttc.connect(address,port)
    #notese que se configuro el cliente de manera que pudiera ser alcanzado por toda la clase
    def subscribeMe(self):                                                  #DRRP   Metodo que realiza las suscripciones
        commandTopic=COMANDOS+"/"+str(grupo)+"/"+"201603188"
        self.mqttc.subscribe(commandTopic)
        self.mqttThread=threading.Thread(target=self.mqttc.loop_start,name="Recepcion mensajes MQTT",daemon=True)
        self.mqttThread.start()                                             #Tambien se inicia el hilo del mqtt cliente

    def initMQTTClient(self):                                               #DRRP   Metodo que inicializa toda la magia
        Host = MQTT_HOST
        Puerto = MQTT_PORT 
        nombre = MQTT_USER
        contra = MQTT_PASS
        self.setupMQTTClient(Host,Puerto,nombre,contra)
        self.subscribeMe()
        self.keepAliveThread=threading.Thread(target=self.mqttAlive,name="Alive",daemon=True)
        self.keepAliveThread.start()                                        #Notese la forma en la que se crea el hilo del ALIVE
                
    def publishData(self, topic,data):                                      #DRRP   Metodo que publicara en los topics correspondientes
        self.mqttc.publish(topic=topic,payload=data,qos=0)
    
    def clientevivo(self,qos=0,retain=False):                               #DRRP   Se publica el ALIVE (\x04)
        topic=COMANDOS+"/"+str(grupo)+"/"+"201603188"
        mensaje=b'\x05'+b'$'+b'201603188'
        self.mqttc.publish(topic,mensaje,qos,retain)

    def mqttAlive(self):
        while True:
            if self.AliveRqst:
                self.clientevivo()
            
            
    def mensajeria(self,data):                                              #DRRP   metodo que manejara los topics y redirigira en caso 
        data=(str(data[0]),data[1])                                         #       sea necesario.
        registro=[]
        trama=data[1].decode("utf-8")
        if data[0][:8]==COMANDOS:
            registro=trama.split("$")       #DRRP   Se aprovecha la ventaja del split para trabajar mas rapido
            if registro[0]=="\x04":
                    self.AliveRqst=True    #DRRP   Apaga bandera que acelera el tiempo
                    

########################
########################

    def on_message(self, mqttc,obj,msg):    #DRRP   metodo exlusivo de MQTT (redirige la informacion)
        self.mensajeria((msg.topic,msg.payload))
        
    def on_connect(self,mqttc,obj,flags,rc):#DRRP   metodo exlusivo de MQTT, indica la coneccion
        logging.info("Conectado correctamente")
    
    def on_publish(self,mqttc,obj,mid):     #DRRP   metodo exlusivo de MQTT, indica si la publicacion fue satisfactoria
        logging.debug("Publicacion exitosa")
 

ExamenProyectos980=MyMQTTClass()
ExamenProyectos980.initMQTTClient()
