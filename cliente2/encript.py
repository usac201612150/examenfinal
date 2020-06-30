
from Crypto.Cipher import AES
import hashlib

class TopSecret(object):
    def __init__(self,password):
        self.key=hashlib.sha256(password).digest()
        self.mode=AES.MODE_CBC
        self.IV='Stringde16Roche!'

    def pad_message(self,mensaje):
        while len(mensaje)%16!=0:
            mensaje=mensaje+" "
        return mensaje

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