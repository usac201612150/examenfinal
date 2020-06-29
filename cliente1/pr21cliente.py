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
from Crypto.Cipher import AES
import hashlib

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
        #self.logging=logging                                                #DRRP   No estoy seguro si es necesario declararlo así
        self.dead=dead                                                      #       contador para el ALIVE
        self.EstoyMuriendo=EstoyMuriendo                                    #       bandera para el ALIVE
        self.ItLives=ItLives                                                #       Definiciones de tiempo en el ALIVE
        self.AmIDead=AmIDead
        self.instru=Instructions()                                          #DRRP   Instancia de la clase Instruccions
        self.pwd=True                                               
 
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
        self.TCP_HOST=TCP_HOST
        self.TCP_PORT=TCP_PORT
        self.BUFFER_SIZE=BUFFER_SIZE
        self.setupMQTTClient(Host,Puerto,nombre,contra)
        self.subscribeMe()
        self.keepAliveThread=threading.Thread(target=self.mqttAlive,name="Alive",daemon=True)
        self.keepAliveThread.start()                                        #Notese la forma en la que se crea el hilo del ALIVE
        self.interfaz()                     #Aqui ya empieza el bucle del programa

    def publishData(self, topic,data):                                      #DRRP   Metodo que publicara en los topics correspondientes
        self.mqttc.publish(topic=topic,payload=data,qos=0)
    
    def IwantToBreakFree(self,destin,filesize,qos=0,retain=False):
        topic=COMANDOS+"/"+str(grupo)+"/"+self.userid
        mensaje=b'\x03'+b'$'+bytes(destin,"utf-8")+b'$'+bytearray(filesize,"utf-8")
        self.mqttc.publish(topic,mensaje,qos,retain)

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
                logging.info("cool im alive")
            elif self.EstoyMuriendo==True and self.dead <=200:              #       del alive sea menor. En caso se restablezca la conexion
                time.sleep(self.AmIDead)                                    #       la bandera y el contador seran reseteados.
            elif dead<=3:                                                   #       Notese que se cumplen con los tiempos estipulados pues
                time.sleep(self.ItLives)                                    #       en 20s habran aprox 200 dead.
            else:
                logging.critical("¡Vaya! Te has desconectado del servidor. \nPara continuar reinicia el programa.")
                sys.exit()
                break
    
    def RecepAudio(self,lista):
        logging.info("Se ha recibido un audio de: "+str(lista[1])+" de tamaño: "+str(lista[2]))
        logging.info("Se reproducira en unos momentos.....")
        sock=socket.socket()
        sock.connect((self.TCP_HOST,self.TCP_PORT))
        try:
            buf=sock.recv(self.BUFFER_SIZE)
            archivo=open("notaentrante.wav","wb")
            while buf:
                archivo.write(buf)
                buf=sock.recv(self.BUFFER_SIZE)
            archivo.close()
            sock.close()
            if self.pwd:
                self.TopSecret.decifaudio("notaentrante.wav")
            os.system("aplay notaentrante.wav")
        except InterruptedError:
            logging.warning("Ha ocurrido un error en la transmision")
        finally:
            sock.close()
        

    def mensajeria(self,data):                                              #DRRP   metodo que manejara los topics y redirigira en caso 
        data=(str(data[0]),data[1])                                         #       sea necesario.
        registro=[]
        
        if data[0][:8]==COMANDOS:
            trama=data[1].decode("utf-8")
            registro=trama.split("$")       #DRRP   Se aprovecha la ventaja del split para trabajar mas rapido
            if registro[-1]==self.userid:
                if registro[0]=="\x05":
                    self.EstoyMuriendo=False    #DRRP   Apaga bandera que acelera el tiempo
                    self.dead=0                 #       Tambien coloca en 0 el contador del ALIVE
                elif registro[0]=="\x06":
                    self.BanderaAudio=True      #DRRP   servidor acepta el intercambio de audio
                    self.BanderaHoldOn=False    #       apaga la espera del servidor
                elif registro[0]=="\x07":
                    self.BanderaAudio=False     #DRRP   servidor deniega el intercambio de audio
                    self.BanderaHoldOn=False    #       apaga la espera del servidor
                elif registro[0]=="\x02":
                    self.Audiothread=threading.Thread(name="Recepcion audio",target=RecepAudio,args=registro,daemon=False)
                    self.Audiothread.start()
        elif data[0][:5]==SALAS:
            logging.info("Se ha recibido un mensaje de la sala "+data[0][9:14])
            if self.pwd:
                trama=self.TopSecret.deciftxt(data[1])
            else:
                trama=data[1].decode("utf-8")
            logging.info(trama)
        elif data[0][:8]==USUARIOS:
            logging.info("Se recibió un mensaje para usted")
            if self.pwd:
                trama=self.TopSecret.deciftxt(data[1])
            else:
                trama=data[1].decode("utf-8")
            logging.info(trama)

########################
########################

    def on_message(self, mqttc,obj,msg):    #DRRP   metodo exlusivo de MQTT (redirige la informacion)
        self.mensajeria((msg.topic,msg.payload))
        
    def on_connect(self,mqttc,obj,flags,rc):#DRRP   metodo exlusivo de MQTT, indica la coneccion
        logging.info("Conectado correctamente")
    
    def on_publish(self,mqttc,obj,mid):     #DRRP   metodo exlusivo de MQTT, indica si la publicacion fue satisfactoria
        logging.debug("Publicacion exitosa")
    
    def interfaz(self):                                                     #DRRP   Metodo que trabaja toda la interfaz
        print("\n\nBienvenido al chat de proyectos980")                     #       es el encargado del loop principal
        print("Cifrado de punto a punto")                                   #       y negociaciones con otras clases
        kygen=input("Ingrese la llave: ")
        kygen.encode()
        self.TopSecret=TopSecret(kygen)                                                                   
        try:                                                                
            while True:
                instruccion=input("Presiona enter para ver opciones o ingresa un comando: ")
                if instruccion=="\n":   
                    self.instru.inicial()
                elif instruccion=="1a":     #Mensaje Directo
                    destin,mensaje=self.instru.direct()
                    Destinatario=USUARIOS+"/"+str(grupo)+"/"+destin
                    if self.pwd:
                        mensaje=self.TopSecret.ciftxt(mensaje)
                    self.publishData(Destinatario,mensaje)
                elif instruccion=="1b":     #Mensaje a grupo
                    destin, mensaje=self.instru.grupo()
                    Destinatario=SALAS+"/"+str(grupo)+"/"+destin
                    if self.pwd:
                        mensaje=self.TopSecret.ciftxt(mensaje)
                    self.publishData(Destinatario,mensaje)
                elif instruccion=="2":      #Audio
                    destin, peso, recordflag=self.instru.audiorec()
                    if recordflag:
                        logging.info("Espere la validacion del servidor. . . . .")
                        self.IwantToBreakFree(destin,peso)
                        time.sleep(5)
                        if self.pwd:
                            self.TopSecret.cifaudio("notadevoz.wav")
                        if self.BanderaAudio:
                            logging.info("Se transmitira el audio, por favor espere.")
                            sock=socket.socket()
                            sock.connect((self.TCP_HOST,self.TCP_PORT))
                            try:
                                with open("notadevoz.wav","rb") as audio:
                                    sock.sendall(audio)
                                audio.close()
                                sock.close()
                            except InterruptedError:
                                logging.warning("Ha ocurrido un error en la transmision")
                            finally:
                                sock.close()
                    else:
                        logging.warning("Su transmisión ha sido rechazada, intentelo más tarde")

                elif instruccion=="3":  #Cifrado
                    if self.pwd:
                        encender=input("El cifrado está encendido, desea apagarlo: S/N")
                        if encender=="S":
                            self.pwd==False
                            print("Apagado")
                        else:
                            pass
                    else:
                        encender=input("El cifrado está apagado, desea encenderlo: S/N")
                        if encender=="S":
                            self.pwd==True
                            print("Encendido")
                    
                elif instruccion=="4":      #Desconectarme
                    self.instru.goodbye()
                    self.mqttc.disconnect()
                    sys.exit()
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

    def direct(self):                                                       #DRRP   Establecimiento de mensaje directo
        Destinatario=input("Destinatario:")
        texto_enviar=input("Que le quieres decir a "+Destinatario+": ")     
        return Destinatario, texto_enviar

    def grupo(self):                                                        #DRRP   Establecimiento de mensaje en grupo
        Destinatario=input("Sala elegida:")
        texto_enviar=input("Que le quieres decir a la sala "+Destinatario+": ")     
        return Destinatario, texto_enviar

    def audiorec(self):
        Destinatario=input("A quien desea enviarle este audio: ")
        duracion=input("Cuantos segundos desea grabar:")
        if int(duracion)>0 and int(duracion)<=30:
            logging.info("Comenzando grabacion...")
            consola="arecord -d "+str(duracion)+" -f U8 -r 8000 notadevoz.wav"
            os.system(consola)
            peso='os.stat("noradevoz.wav").st_size'
            grabado=True
        else: 
            logging.warning("Tiempo no valido")
            grabado=False
            peso=0
        return Destinatario,peso,grabado
        

    def goodbye(self):
        print("Vaya una pena que te vayas, vuelve pronto")

#Referencia https://www.youtube.com/watch?v=SoeeCg04-FA
class TopSecret(object):
    def __init__(self,password):
        self.key=hashlib.sha256(password).digest()
        self.mode=AES.MODE_CBC
        self.IV='Stringde16Roche!'

    def pad_message(self,mensaje):
        while len(message)%16!=0:
            message=message+" "
        return message

    def ciftxt(self,mensaje):
        cipher=AES.new(self.key,self.mode,self.IV)
        rightlen=self.pad_message(mensaje)
        encriptado=cipher.encrypt(rightlen)
        return encriptado

    def deciftxt(self,mensaje):
        cipher=AES.new(self.key,self.mode,self.IV)
        decrypted_text=cipher.decrypt(mensaje)
        decrypted_text.rstrip().decode()
        return decrypted_text
    
    def pad_audio(self,file):
        while len(file)%16 !=0:
            file = file +b'0'
        return file

    def cifaudio(self,audio):
        cipher=AES.new(self.key,self.mode,self.IV)
        with open(audio,"rb") as f:
            data=f.read()
        rightlen=self.pad_audio(data)
        f.close()
        encriptado=cipher.encrypt(rightlen)
        with open(audio,"wb") as f:
            f.write(encriptado)
        f.close()
    
    def decifaudio(self,audio):
        cipher=AES.new(self.key,self.mode,self.IV)
        with open(audio,"rb") as f:
            data=f.read()
        decrypted_file = cipher.decrypt(data)
        f.close()
        with open(audio,"wb") as f:
            f.write(decrypted_file.rstrip(b'0'))



ExamenProyectos980=MyMQTTClass()
ExamenProyectos980.initMQTTClient()
