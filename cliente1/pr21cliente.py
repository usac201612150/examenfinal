"""                                                                        #DRRP
Este codigo debe ser copiado a una carpeta en la que existan los siguientes archivos:
    -usuario (Dentro de el, ingresar 201603188 o 201612150)
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
CLIENTE="cliente1"            #Prioritario cambiarlo para distintos clientes
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
####################        METODOS#               #######################
##########################################################################
class Instructions(object):                                                #DRRP Clase para el manejo de las instruciones
    def __init__(self, comando):
        self.comando=comando

    def inicial(self):                                                     #DRRP Despliega el menu grafico
        print("para su uso favor ingresar a una de las siguientes ramas")
        print("\t1. Enviar texto \n\t\ta.Enviar mensaje directo\n\t\tb.Enviar a una sala")
        print("\t2. Enviar nota de voz")
        print("\t3. Desconectarme")
        print("\t4. Mostrar opciones")

    def direct(self):                                                       #DRRP Instruccion para enviar mensajes directos
        Destinatario=input("Destinatario:")
        texto_enviar=input("Que le quieres decir a "+Destinatario+": ")     
        return Destinatario, texto_enviar

    def grupo(self):
        Destinatario=input("Sala elegida:")
        texto_enviar=input("Que le quieres decir a la sala "+Destinatario+": ")     
        return Destinatario, texto_enviar

    def audiorec(self):
        duracion=input("Cuantos segundos desea grabar:")
        if int(duracion)>0 and int(duracion)<=30:
            logging.info("Comenzando grabacion...")
            consola="arecord -d"+str(duracion)+"-f U8 -r 8000 notadevoz.wav"
            os.system(consola)
            peso=os.stat("noradevoz.wav").st_size
            grabado=True
        else: 
            logging.warning("Tiempo no valido")
            grabado=False
            peso=0
        return grabado,peso

    def goodbye(self):
        pass

def Whatsmyname():                                                          #DRRP Identifica quien soy  
    global YoSoy
    file=open(CLIENTE+"/usuario","r")#ojo este cambia para clientes
    for i in file:
        YoSoy=str(i)
        YoSoy=YoSoy.replace("\n","")
    return YoSoy    

def on_connect(cliente,userdata,flags,rc):                                  #DRRP metodo de MQTT para la conexion con el Broken
    logging.debug("Conexion establecida")

def on_message(client,userdata,msg):                                        #DRRP metodo de MQTT para la recepcion
    if str(msg.topic)==COMANDOS+"/"+str(grupo)+"/"+YoSoy:                   #     redirige la informacion para el mejor procesamiento
        ComandConfirm(msg.payload)
    else:
        logging.info("\nMensaje de: "+str(msg.topic))
        logging.info("\t>>"+str(msg.payload)+"\n")
        logCommand = 'echo "(' + str(msg.topic) + ') -> ' + str(msg.payload) + '" >> ' + LOG_FILENAME
        os.system(logCommand)

def on_publish(client, userdata, mid):                                      #DRRP metodo de MQTT para la publicacion
    publishText = "Publicacion satisfactoria"
    logging.debug(publishText)

def confRecepcion():                                                        #DRRP Hice dos metodos distintos para la publicacion y recepcion
    global client_receptor                                                  #     porque no estoy seguro de si entrarian en conflicto
    client_receptor=mqtt.Client(clean_session=True)
    client_receptor.on_connect=on_connect
    client_receptor.on_message=on_message
    client_receptor.username_pw_set(MQTT_USER, MQTT_PASS) 
    client_receptor.connect(host=MQTT_HOST, port = MQTT_PORT) 
    
def confEmisor():
    global client_emisor
    client_emisor = mqtt.Client(clean_session=True) 
    client_emisor.on_connect = on_connect 
    client_emisor.on_publish = on_publish 
    client_emisor.username_pw_set(MQTT_USER, MQTT_PASS)
    client_emisor.connect(host=MQTT_HOST, port = MQTT_PORT) 

def room_subs():                                                            #DRRP el metodo room_subs y user_subs establecen la suscripcion a todo
    file=open(CLIENTE+"/salas","r")#ojo cambiar para los clientes           #     los topics que el usuario tiene que estar suscrito
    finallist=[]
    for i in file:
        newlist=[]
        text=SALAS+"/"+str(grupo)+"/"+str(i)
        text=text.replace("\n","")
        newlist.append(text)
        newlist.append(qos)
        finallist.append(tuple(newlist))
    file.close()
    client_receptor.subscribe(finallist)

def user_subs():
    userid=Whatsmyname()
    text=USUARIOS+"/"+userid
    client_receptor.subscribe((text,qos))
    text2=COMANDOS+"/"+str(grupo)+"/"+userid
    client_receptor.subscribe((text2,qos))

def recepcion_data():                                                       #DRRP este metodo lo cree para que pueda trabajar en un hilo demonio
    client_receptor.loop_start()

def publishData(topicRoot,topicName,value,qos=0,retain=False):              #DRRP metodo encargado del envio de texto y comandos
    topic=topicRoot+"/"+topicName
    client_emisor.publish(topic,value,qos,retain)

def clientevivo(qos=0,retain=False):                                        #DRRP metodo especial para el comando ALIVE
    topic=COMANDOS+"/"+str(grupo)+"/"+YoSoy
    usuario=bytes(YoSoy,"utf-8")
    mensaje=COMMAND_ALIVE+b'$'+usuario
    client_emisor.publish(topic,mensaje,qos,retain)

def Check():                                                                #DRRP metodo que sera ejecutado por el hilo demonio
        global dead                                                         #     encargado del ALIVE, en el se tiene los retardos
        global EstoyMuriendo                                                #     segun lo estipulado y tambien mata el programa en
        while True:                                                         #     caso exista una desconeccion
            clientevivo()
            dead+=1
            if dead==3:
                EstoyMuriendo=True
                time.sleep(ItLives)
            elif EstoyMuriendo==True and dead<=200:
                time.sleep(AmIDead)
            elif dead<=3:
                time.sleep(ItLives)
            else:
                logging.critical("Algo salio mal, favor resetear el programa")
                sys.exit()

def TransmisionAudio():
    sock=socket.socket()
    sock.connect((TCP_HOST,TCP_PORT))
    try:
        with open("notadevoz.wav","rb") as transmision:
            sock.sendall(transmision)
            transmision.close()
        logging.info("Transmision exitosa")
    finally:
        sock.close()

def ComandConfirm(Ack):                                                        #DRRP  con este metodo se recibe la respuesta del servidor
    global dead                                                                #       es por eso que es importante que dead y EstoyMuriendo sean globales
    global EstoyMuriendo
    if str(Ack)==b'\x05':
        if EstoyMuriendo==True and dead>=3:
            dead=0
            EstoyMuriendo==False
        else:
            dead-=1
    elif str(Ack)==b'\x02':
        TransmisionAudio()
    



##########################################################################
####################        Principal              #######################
##########################################################################
logging.basicConfig(                                                        #DRRP configuracion del logging
    level = logging.INFO, 
    format = '[%(levelname)s] (%(threadName)-10s) %(message)s'
    )

confEmisor()       #DRRP inicializacion de metodos necesarios
confRecepcion()
room_subs()
user_subs()

t1=threading.Thread(name="Recepcion",target=recepcion_data,args=(),daemon=True) #DRRP creacion del hilo que recibira mensajes
t2=threading.Thread(name="SigoVivo",target=Check,args=(),daemon=True) #DRRP creacion del hilo que idicara "ALIVE"
t1.start()
t2.start()

print("\n\nBienvenido al chat de proyectos980")
try:
    while True:                                                             #DRRP manejo de las instruciones iniciales dentro de un ciclo principal
        instruccion=input("Presiona enter para ver opciones o ingresa un comando: ")
        if instruccion=="\n":
            Instructions.inicial(instruccion)
        elif instruccion=="1a": #Mensaje Directo
            destin, mensaje=Instructions.direct(instruccion)
            publishData(USUARIOS,destin,mensaje)
        elif instruccion=="1b": #Mensaje a grupo
            destin, mensaje=Instructions.grupo(instruccion)
            publishData(SALAS,destin,mensaje)

        elif instruccion=="2": #Audio
            Destinatario=input("Destinatario:")
            subtopic=Whatsmyname()
            subtopic=str(grupo)+"/"+subtopic
            grabado, peso=Instructions.audiorec(instruccion)
            if grabado:
                trama=COMMAND_FTR+b'$'+bytes(Destinatario,"utf-8")+bytes(str(peso),"utf-8")
                publishData(COMANDOS,subtopic,trama)

        elif instruccion=="3":  #Desconectarme
            Instructions.goodbye(instruccion)
        elif instruccion=="4":  #Menu
            Instructions.inicial(instruccion)
        else:
            print("Ingrese un comando válido, Ej: \'1a\'")
            Instructions.inicial(instruccion)

except KeyboardInterrupt:
    logging.info("\nTerminando conexion")
    if t1.is_alive():
        t1._stop()
    if t2.is_alive():
        t2._stop()
finally:
    
    client_emisor.disconnect()
    client_receptor.disconnect()
    sys.exit()