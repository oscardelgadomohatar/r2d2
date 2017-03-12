# -*- coding: utf-8 -*-
import os, re, shutil, signal, socket, logging, time
import random, string
import ircparser

"""
    Clase abstracta que define un test genérico
"""
class IRCServer(object):
    
    REGEXP_PING = r'PING (\S+)'
    
    def __init__(self, sDroid):
        self.sd = sDroid
        
    def connect(self, nick, ssl = False):
        
        # Si ya está establecida la conexión, nada que hacer
        if self.sd.connections.has_key(nick):
            # Limpiamos los posibles mensajes anteriores
            self.discardAll(nick)            
            return        
        
        s = socket.socket()
        s.settimeout(5)
        try:
            # Intento de conexión            
            s.connect((self.sd.serverIP, self.sd.serverPort))
            if ssl: s = socket.ssl(s)

            # Es necesario volver a establecer el socket como bloqueante
            # para la llamada a makefile
            s.settimeout(None)        
        
            # Todo ha ido bien
            self.sd.connections[nick] = s.makefile(mode="rw")      
            self.sd.sockets[nick] = s
            
            # Se envían los comandos de registro       
            self.send(nick, "NICK %s" % nick)
            self.send(nick, "USER %s * * :%s" % (nick, nick))
                             
            # Comenzamos a parsear y comprobar las respuestas. Se descarta toda 
            # entrada hasta el primer código 001                       
            self.discardTill(nick, r":\S* 001 %s :.*" % nick)
            self.discardAll(nick)   

            # Indicamos que todo ha ido bien
            return True

        except Exception as e:            
            raise e
        
    def shutDown(self):
        os.kill(self.child_pid, signal.SIGTERM)
        os.waitpid(self.child_pid, 0)
        if self.state_dir:
            try:
                shutil.rmtree(self.state_dir)
            except IOError:
                pass

    def tearDown(self):
        try:        
            for x in self.sd.sockets.values():                
                x.shutdown(socket.SHUT_WR)
                x.close()            
        except Exception:
            pass
        finally:
            for x in self.sd.connections.values():
                x.close()
            self.sd.connections.clear()

        # Damos tiempo a que la otra parte cierre sus conexiones
        time.sleep(1)
        
    def send(self, nick, message):
        logging.debug(">> SERVER: %s" % message)
        self.sd.connections[nick].write(message + "\r\n")        
        self.sd.connections[nick].flush()    
            
    def _readLine(self, nick, regexp = "", timeout = 5):
        # Sorprendemente, Python 2.x no tiene soporte no bloqueante
        # para la función readline(), así que hay que utilizar este "truco"
        def timeout_handler(signum, frame):
            raise AssertionError("Ha saltado el timeout esperando la expresión %r" % regexp)
        signal.signal(signal.SIGALRM, timeout_handler)
        
        while True:
            # Establecemos el timeout y leemos una línea
            signal.alarm(timeout)  
            line = self.sd.connections[nick].readline().rstrip()        
            signal.alarm(0)                
        
            # Si se trata de un PING enviado por el servidor, respondemos aquí
            # PING 1079550066
            # Reply: PONG 1079550066                              
                
            # Comprobamos que el nombre del directorio tiene el formato requerido, G-CCCC-NN-PX
            m = re.match(self.REGEXP_PING, line)
        
            if m is not None:
                # Hemos recibido un PING, respondemos
                params = m.group(1)                                          
            
                logging.debug("<< SERVER: %s" % line)            
                self.send(nick, "PONG %s" % params)
            else:
                # Si no se trata de un PING, salimos y devolvemos la línea leida
                logging.debug("<< SERVER: %s" % line)
                break
            
        return line
    
    """
        ENTRADA: Ninguna
        SALIDA: Ninguna
        FUNCIÓN: Descarta todos los mensajes enviado por el servidor hasta
             que salta el timeout (significa que no hay más mensajes)
    """
    def discardAll (self, nick):
                
        while True:
            try:
                line = self._readLine(nick, timeout=1)                
                
                assert len(line) != 0
                
            except AssertionError:
                break            
    """
        FUNCIÓN: Descarta toda la salida devuelta por el servidor hasta que se 
        encuentra un patrón específico
    """
    def discardTill (self, nick, regexp):
        # Leemos la siguiente linea
        line = self._readLine(nick, regexp)
        m = re.match(regexp, line)
        
        # No, no hay bucles do-while en Python... :/
        while not m:
            logging.debug("Discarded message [%s]: %s" % (len(line), line)) 
            line = self._readLine(nick, regexp)            
            m = re.match(regexp, line)
    
    """
        ENTRADA: timeout, regexp
        SALIDA: Lista de comandos IRC
        FUNCIÓN: Devuelve toda la salida producida por el servidor en forma de lista
        con cada línea de salida, hasta encontrar un patrón específico
    """
#===============================================================================
#     def readAllLinesTill2 (self, timeout = None, regexp = None):
#         # Leemos la siguiente linea
#         listaSalida = []
#          
# #===============================================================================
# #         Hacer una función de lectura que o bien espere que salte
# # Un timeout, que se reciba un regexp, con un máximo de 
# # Líneas leidas
# #===============================================================================
#          
#         if timeout is not None:
#             while True:
#             try:
#                 line = self._readLine(nick, timeout=1)
#                  
#                 assert len(line) != 0
#                  
#             except AssertionError:
#                 break 
#      
#         line = self._readLine(nick, regexp)
#         m = re.match(regexp, line)
#         listaSalida.insert(0, line)
#          
#         # No, no hay bucles do-while en Python... :/
#         while not m:
#             logging.debug("Received message [%s]: %s" % (len(line), line)) 
#             line = self._readLine(nick, regexp)            
#             m = re.match(regexp, line)
#             listaSalida.insert(0, line)
#          
#         return listaSalida
#===============================================================================
    
    def readAllLinesTill (self, nick, endCommand = ""):
        
        receivedMessages = {}                
        
        # Recepción y parseo de la respuesta                      
        #line = self._readLine(nick, timeout = 1)                      
        line = self._readLine(nick)
        message = ircparser.translate(line)
        receivedMessages[message['command']] = line
        
        # Si no se especifica un comando de finalización el siguiente bucle
        # es infinito hasta que salte un timeout. Si se especifica, se para
        # cuando se encuentra un comando de ese tipo
        while (endCommand == "" or \
               message['command'] is not endCommand):
            try:            
                # Recepción y parseo de la respuesta
                #line = self._readLine(nick, timeout = 1)                      
                line = self._readLine(nick)
                message = ircparser.translate(line)
                # Comprobamos que no es una línea vacia  
                assert message is not None
                
                # Guardamos el mensaje recibido en el diccionario
                receivedMessages[message['command']] = line
            except AssertionError:
                break
        
        return receivedMessages
       
    def expect(self, nick, regexp):          
        # Leemos la siguiente linea
        line = self._readLine(nick, regexp)        
        
        # Comprobamos la expresión regular
        m = re.match(regexp, line)
        assert m is not None, "Los datos recibidos %r no encajan con la expresión requerida %r" % (line, regexp)
        
        return m        
    
    def joinChannel(self, nick, channelName, clave = ""):
        
        # Conexión y envio del comnado
        if clave is not "":                
            self.send(nick, "JOIN #%s %s" % (channelName, clave))
        else:
            self.send(nick, "JOIN #%s" % channelName)
                
        self.expect(nick, r":\S+ JOIN :#%s" % channelName)
        self.discardAll(nick)
    
    def sendMessageToUser(self, nick1, nick2, mensaje):
        
        # Enviamos el mensaje 
        self.send(nick1, r"PRIVMSG %s :%s" % (nick2, mensaje))        
        self.expect(nick2, r":\S+ PRIVMSG %s :%s" % (nick2, mensaje))
        
    def sendMessageToChannel(self, nickEmisor, otrosNicks, canal, mensaje):
        
        # Enviamos el mensaje 
        self.send(nickEmisor, r"PRIVMSG #%s :%s" % (canal, mensaje))
        
        for nick in otrosNicks:              
            self.discardTill(nick, r":\S+ PRIVMSG #%s :%s" % (canal, mensaje))
    
    def setChannelTopic(self, nick, channelName, topic):
        
        # Enviamos el comando TOPIC y parseamos la respuesta        
        self.send(nick, "TOPIC #%s :%s" % (channelName, topic))
        self.expect(nick, r":\S+ TOPIC #%s :%s" % (channelName, topic))                
        
        # Ahora el comando sin parámetro debería devolver el topic
        self.send(nick, "TOPIC #%s" % channelName)
        self.expect(nick, r":\S+ 332 %s #%s :%s" % (nick, channelName, topic))
        self.discardAll(nick)                
        
    """
        DEVUELVE: Una lista de tuplas (nombreCanal, numUsuarios, topic)
    """
    def getChannelList(self, tempNick, includeTopic = False):
                
        listaCanales = []
        
        # Conexión y envio del comnado                    
        self.send(tempNick, "LIST")
                          
        # Recepción y parseo de la respuesta                      
        message = ircparser.translate(self._readLine(tempNick))                                        
        
        while (message['command'] is not "RPL_LISTEND"):
            # Cada mensaje que se muestre en la respuesta suma puntuación                
            if message['command'] == 'RPL_LIST' and message['params'][1].startswith('#'):
                listaCanales.append((message['params'][1], 
                                     message['params'][2], 
                                     message['params'][3])) if includeTopic == True else listaCanales.append(message['params'][1])
                
            # Recepción y parseo de la respuesta                      
            message = ircparser.translate(self._readLine(tempNick))
        
        return listaCanales
    
    """
        DEVUELVE: Una lista con los usuarios de un canal dado
    """      
    def getChannelUsers (self, nick, nombreCanal):
        
        listaUsuarios = []
        
        # Conexión y envio del comnado                    
        self.send(nick, "NAMES #%s" % nombreCanal)
                          
        # Recepción y parseo de la respuesta                      
        message = ircparser.translate(self._readLine(nick))                                        
        
        while (message['command'] is not "RPL_ENDOFNAMES"):
            # Cada mensaje que se muestre en la respuesta suma puntuación                
            if message['command'] == 'RPL_NAMREPLY':
                listaUsuarios.append(message['params'][0])
                
            # Recepción y parseo de la respuesta                      
            message = ircparser.translate(self._readLine(nick))
        
        return listaUsuarios
    
    def generateRandomString(self):
        return ''.join(random.sample(string.letters, 8))