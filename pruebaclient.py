#Diego Roberto Roche Palacios
#Rubén David Simón Sicá

"""                                                                        #DRRP
Este codigo debe ser copiado a una carpeta en la que existan los siguientes archivos:
    -usuarios (Dentro de el, ingresar 201603188 o 201612150)
    -salas   (Dentro de el, ingresar salas validas Ej: 21S01)
"""
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

MQTT_HOST = "167.71.243.238" #Necesarios para MQTT
MQTT_PORT = 1883
MQTT_USER = "proyectos"
MQTT_PASS = "proyectos980"
qos = 2

TCP_HOST="167.71.243.238"
TCP_PORT=9821 
BUFFER_SIZE=64*1024

COMMAND_FTR=b'\x03'         #Definicion de comandos
COMMAND_ALIVE=b'\x04'

ItLives=2                   #2segundos para ALIVE
AmIDead=0.1                 #0.1segundos para ALIVE
dead=0                      #Contador de ALIVE
EstoyMuriendo=False         #Bandera de ALIVE

COMANDOS="comandos"         #Definicion para archivos
USUARIOS="usuarios"
SALAS="salas"
##########################################################################
####################           Clases              #######################
##########################################################################

class MyMQTTClass(object):
    def __init__(self):
        logging.basicConfig(
            level=logging.INFO,
            format='[%(levelname)s] (%(threadName)-10s) %(message)s'
        )
        self.logging=logging
        self.dead=dead
        self.EstoyMuriendo=EstoyMuriendo
        self.ItLives=ItLives
        self.AmIDead=AmIDead
        self.instru=Instructions()
        self.initMQTTClient()
 
    def Whatsmyname(self):
        file=open(USUARIOS,"r")
        for line in file:
            Yosoy=line
            Yosoy=Yosoy.replace("\n","")
        file.close()
        return Yosoy

    def setupMQTTClient(self,address,port,usuario,contraseña):
        self.userid=self.Whatsmyname()
        self.mqttc=mqtt.Client(clean_session=True)
        self.mqttc.on_message=self.on_message
        self.mqttc.on_connect=self.on_connect
        self.mqttc.on_publish=self.on_publish
        self.mqttc.username_pw_set(usuario,contraseña)
        self.mqttc.connect(address,port)

    def subscribeMe(self):
        file=open(SALAS,"r")
        finallist=[]
        for i in file:
            newlist=[]
            text=SALAS+"/"+str(grupo)+"/"+str(i)
            text=text.replace("\n","")
            newlist.append(text)
            newlist.append(qos)
            finallist.append(tuple(newlist))
        file.close()
        self.mqttc.subscribe(finallist)
        userTopic=USUARIOS+"/"+str(grupo)+"/"+self.userid
        self.mqttc.subscribe(userTopic)
        commandTopic=COMANDOS+"/"+str(grupo)+"/"+self.userid
        self.mqttc.subscribe(commandTopic)
        self.mqttThread=threading.Thread(target=self.mqttc.loop_start,name="Recepcion mensajes MQTT",daemon=True)
        self.mqttThread.start()

    def initMQTTClient(self):
        Host = MQTT_HOST
        Puerto = MQTT_PORT 
        nombre = MQTT_USER
        contra = MQTT_PASS
        self.setupMQTTClient(Host,Puerto,nombre,contra)
        self.subscribeMe()
        self.keepAliveThread=threading.Thread(target=self.mqttAlive,name="Alive",daemon=True)
        self.keepAliveThread.start()
        self.interfaz()

    def publishData(self, topic,data):
        self.mqttc.publish(topic=topic,payload=data,qos=0)
    
    def clientevivo(self,qos=0,retain=False):
        topic=COMANDOS+"/"+str(grupo)+"/"+self.userid
        mensaje=COMMAND_ALIVE+b'$'+bytes(self.userid,"utf-8")
        self.mqttc.publish(topic,mensaje,qos,retain)

    def mqttAlive(self):
        while True:
            self.clientevivo()
            self.dead+=1
            if self.dead>200:
                logging.critical("¡Vaya! Te has desconectado del servidor. \nPara continuar reinicia el programa.")
                sys.exit()
            elif self.dead==3:
                self.EstoyMuriendo=True
                time.sleep(self.ItLives)
            elif self.EstoyMuriendo==True and self.dead <=200:
                time.sleep(self.AmIDead)
            elif dead<=3:
                time.sleep(self.ItLives)
            else:
                logging.critical("¡Vaya! Te has desconectado del servidor. \nPara continuar reinicia el programa.")
                sys.exit()
            
    def mensajeria(self,data):
        data=(str(data[0]),data[1])
        logging.info(data)

    def on_message(self, mqttc,obj,msg):
        self.mensajeria((msg.topic,msg.payload))

    def on_connect(self,mqttc,obj,flags,rc):
        logging.info("Conectado correctamente")
    
    def on_publish(self,mqttc,obj,mid):
        logging.info("Publicacion exitosa")
    
    def interfaz(self):
        print("\n\nBienvenido al chat de proyectos980")
        try:
            while True:
                instruccion=input("Presiona enter para ver opciones o ingresa un comando: ")
                if instruccion=="\n":   
                    self.instru.inicial()
                elif instruccion=="1a": #Mensaje Directo
                    destin,mensaje=self.instru.direct()
                    Destinatario=USUARIOS+"/"+str(grupo)+"/"+destin
                    self.publishData(Destinatario,mensaje)
                elif instruccion=="1b": #Mensaje a grupo
                    destin, mensaje=Instructions.grupo(instruccion)
                    Destinatario=SALAS+"/"+str(grupo)+"/"+destin
                    self.publishData(Destinatario,mensaje)
                elif instruccion=="2":  #Audio
                    pass
                elif instruccion=="3":  #Desconectarme
                    Instructions.goodbye(instruccion)
                elif instruccion=="4":  #Menu
                    Instructions.inicial(instruccion)
                else:
                    print("\nIngrese un comando válido, Ej: \'1a\'")
        except KeyboardInterrupt:
            if self.mqttThread.is_alive():
                self.mqttThread._stop()
                logging.warning("Se esta saliendo del chat")
        finally:
            logging.info("¡Vaya! algo pasó.\nPara continuar reiniciar el programa.")
            self.mqttc.disconnect()
            sys.exit()

class Instructions(object):                                              
    def __init__(self, comando=None):
        self.comando=comando

    def inicial(self):                                                     
        print("para su uso favor ingresar a una de las siguientes ramas")
        print("\t1. Enviar texto \n\t\ta.Enviar mensaje directo\n\t\tb.Enviar a una sala")
        print("\t2. Enviar nota de voz")
        print("\t3. Desconectarme")
        print("\t4. Mostrar opciones")

    def direct(self):                                                      
        Destinatario=input("Destinatario:")
        texto_enviar=input("Que le quieres decir a "+Destinatario+": ")     
        return Destinatario, texto_enviar

    def grupo(self):
        Destinatario=input("Sala elegida:")
        texto_enviar=input("Que le quieres decir a la sala "+Destinatario+": ")     
        return Destinatario, texto_enviar

    def audiorec(self):
        #duracion=input("Cuantos segundos desea grabar:")
        #if int(duracion)>0 and int(duracion)<=30:
        #    logging.info("Comenzando grabacion...")
        #    consola="arecord -d"+str(duracion)+"-f U8 -r 8000 notadevoz.wav"
        #    os.system(consola)
        #    peso=os.stat("noradevoz.wav").st_size
        #    grabado=True
        #else: 
        #    logging.warning("Tiempo no valido")
        #    grabado=False
        #    peso=0
        #return grabado,peso
        pass

    def goodbye(self):
        pass


ExamenProyectos980=MyMQTTClass()
ExamenProyectos980.initMQTTClient()
