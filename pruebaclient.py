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
##########################################################################
####################           Clases              #######################
##########################################################################
class MyMQTTClass(object):                                                  #DRRP   Clase que maneja el proceso principal
    def __init__(self):                                                     #       Configuracion de las instancias
        logging.basicConfig(                                                #       Indica como trabajara el logging
            level=logging.INFO,
            format='[%(levelname)s] (%(threadName)-10s) %(message)s'
        )
        self.logging=logging                                                #DRRP   No estoy seguro si es necesario declararlo así
        self.dead=dead                                                      #       contador para el ALIVE
        self.EstoyMuriendo=EstoyMuriendo                                    #       bandera para el ALIVE
        self.ItLives=ItLives                                                #       Definiciones de tiempo en el ALIVE
        self.AmIDead=AmIDead
        self.instru=Instructions()                                          #DRRP   Instancia de la clase Instruccions
        #self.initMQTTClient()                                               
 
    def Whatsmyname(self):                                                  #DRRP   Define el user id
        file=open(USUARIOS,"r")
        for line in file:
            Yosoy=line
            Yosoy=Yosoy.replace("\n","")
        file.close()
        return Yosoy

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
        file=open(SALAS,"r")
        finallist=[]
        for i in file:
            newlist=[]
            text=SALAS+"/"+str(grupo)+"/"+str(i)
            text=text.replace("\n","")
            newlist.append(text)            #Dado que la forma en la que suscribe el metodo
            newlist.append(qos)             #recibe una tupla dentro de una lista, ej: finallist=[(text,qos),(text,qos),(text,qos)]
            finallist.append(tuple(newlist))
        file.close()
        self.mqttc.subscribe(finallist)                                     #Aprovecho este metodo para suscribir tanto para salas
        userTopic=USUARIOS+"/"+str(grupo)+"/"+self.userid                   #como para el usuario y sus comandos
        self.mqttc.subscribe(userTopic)
        commandTopic=COMANDOS+"/"+str(grupo)+"/"+self.userid
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
        #self.keepAliveThread=threading.Thread(target=self.mqttAlive,name="Alive",daemon=True) 
        #self.keepAliveThread.start()                                        #Notese la forma en la que se crea el hilo del ALIVE
        self.interfaz()                     #Aqui ya empieza el bucle del programa

    def publishData(self, topic,data):                                      #DRRP   Metodo que publicara en los topics correspondientes
        self.mqttc.publish(topic=topic,payload=data,qos=0)
    
    def clientevivo(self,qos=0,retain=False):                               #DRRP   Se publica el ALIVE (\x04)
        topic=COMANDOS+"/"+str(grupo)+"/"+self.userid                      
        mensaje=b'\x04'+b'$'+bytes(self.userid,"utf-8")
        self.mqttc.publish(topic,mensaje,qos,retain)

    def mqttAlive(self):
        while True:
            self.clientevivo()
            self.dead+=1
            if self.dead>200:               #DRRP   Aqui hubo un pequeño bug que no supe solucionar de otra forma
                logging.critical("¡Vaya! Te has desconectado del servidor. \nPara continuar reinicia el programa.")
                sys.exit()
            elif self.dead==3:                                              #DRRP   La logica de esto es que cada ALIVE genera un dead
                self.EstoyMuriendo=True                                     #       que si llega un ACK lo cancela, si el dead llega a 3
                time.sleep(self.ItLives)                                    #       se levanta la bandera EstoyMuriendo para que el tiempo
            elif self.EstoyMuriendo==True and self.dead <=200:              #       del alive sea menor. En caso se restablezca la conexion
                time.sleep(self.AmIDead)                                    #       la bandera y el contador seran reseteados.
            elif dead<=3:                                                   #       Notese que se cumplen con los tiempos estipulados pues
                time.sleep(self.ItLives)                                    #       en 20s habran aprox 200 dead.
            else:
                logging.critical("¡Vaya! Te has desconectado del servidor. \nPara continuar reinicia el programa.")
                sys.exit()
            
    def mensajeria(self,data):                                              #DRRP   metodo que manejara los topics y redirigira en caso 
        data=(str(data[0]),data[1])                                         #       sea necesario.
        registro=[]
        if data[0][:8]==COMANDOS:
            trama=data[1].decode()
            registro=trama.split("$")       #DRRP   Se aprovecha la ventaja del split para trabajar mas rapido
            if registro[0]=="\x05":
                self.EstoyMuriendo=False    #DRRP   Apaga bandera que acelera el tiempo
                self.dead=0                 #       Tambien coloca en 0 el contador del ALIVE
            elif registro[0]=="\x06":
                self.BanderaAudio=True      #DRRP   servidor acepta el intercambio de audio
                self.BanderaHoldOn=False    #       apaga la espera del servidor
                #Agregar metodo para la grabación del audio
            elif registro[0]=="\x07":
                self.BanderaAudio=False     #DRRP   servidor deniega el intercambio de audio
                self.BanderaHoldOn=False    #       apaga la espera del servidor
                
########################
########################

    def on_message(self, mqttc,obj,msg):    #DRRP   metodo exlusivo de MQTT (redirige la informacion)
        self.mensajeria((msg.topic,msg.payload))

    def on_connect(self,mqttc,obj,flags,rc):#DRRP   metodo exlusivo de MQTT, indica la coneccion
        logging.info("Conectado correctamente")
    
    def on_publish(self,mqttc,obj,mid):     #DRRP   metodo exlusivo de MQTT, indica si la publicacion fue satisfactoria
        logging.info("Publicacion exitosa")
    
    def interfaz(self):                                                     #DRRP   Metodo que trabaja toda la interfaz
        print("\n\nBienvenido al chat de proyectos980")                     #       es el encargado del loop principal
        try:                                                                #       y negociaciones con otras clases
            while True:
                instruccion=input("Presiona enter para ver opciones o ingresa un comando: ")
                if instruccion=="\n":   
                    self.instru.inicial()
                elif instruccion=="1a":     #Mensaje Directo
                    destin,mensaje=self.instru.direct()
                    Destinatario=USUARIOS+"/"+str(grupo)+"/"+destin
                    self.publishData(Destinatario,mensaje)
                elif instruccion=="1b":     #Mensaje a grupo
                    destin, mensaje=Instructions.grupo(instruccion)
                    Destinatario=SALAS+"/"+str(grupo)+"/"+destin
                    self.publishData(Destinatario,mensaje)
                #elif instruccion=="2":      #Audio
                #    pass
                #elif instruccion=="3":      #Desconectarme
                #    Instructions.goodbye(instruccion)
                elif instruccion=="4":      #Menu
                    Instructions.inicial(instruccion)
                else:
                    print("\nIngrese un comando válido, Ej: \'1a\'")
        except KeyboardInterrupt:           #En caso que se detenga el programa               
            if self.mqttThread.is_alive():  #se finalizan todos los procesos
                self.mqttThread._stop()
                logging.warning("Se esta saliendo del chat")
        finally:
            logging.info("¡Vaya! algo pasó.\nPara continuar reiniciar el programa.")
            self.mqttc.disconnect()
            sys.exit()

class Instructions(object):                                                 #DRRP   Clase que trabaja actividades secundarias                                           
    def __init__(self, comando=None):
        self.comando=comando

    def inicial(self):                                                      #DRRP   Despliegue de menu                                            
        print("para su uso favor ingresar a una de las siguientes ramas")
        print("\t1. Enviar texto \n\t\ta.Enviar mensaje directo\n\t\tb.Enviar a una sala")
        print("\t2. Enviar nota de voz")
        print("\t3. Desconectarme")
        print("\t4. Mostrar opciones")

    def direct(self):                                                       #DRRP   Establecimiento de mensaje directo
        Destinatario=input("Destinatario:")
        texto_enviar=input("Que le quieres decir a "+Destinatario+": ")     
        return Destinatario, texto_enviar

    def grupo(self):                                                        #DRRP   Establecimiento de mensaje en grupo
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
