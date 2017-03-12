# -*- coding: utf-8 -*-
import logging, re, ircTests, time
from ircTests import IRCTest, TipoTest        
from codes import codes

class AdvancedTest(IRCTest):
    
    tipoTest = TipoTest.AVANZADO
    
    def getScore(self):                
        return self.advancedTestsScore/float(len(ircTests.advancedTestsList)) 

"""
    Tests que comprueba el funcionamiento del comando AWAY
    
    DEPENDENCIAS: - 
"""
class TestComandoAway(AdvancedTest):
    
    def _parseRPL_AWAYCommand(self, mensajes, awayMessage):
        
        # Comprobamos que hemos recibido el RPL_AWAY y que éste tiene
        # el formato correcto
        assert mensajes.has_key("RPL_AWAY"), "La respuesta del servidor no contiene el comando 301"
        
        expectedResponse = r":\S+ %s %s %s :%s" % (codes['RPL_AWAY'], self.testNick, self.testNick, awayMessage)         
        assert re.match(expectedResponse, mensajes['RPL_AWAY']), \
            "El formato del comando 301 no es correcta. \n Esperado [%s] \n Recibido [%s]" % (expectedResponse, mensajes['RPL_AWAY'])
            
    def execute(self):                       
         
        # Conexión al servidor        
        self.ircServer.connect(self.testNick)
        
        # Solicitamos que el servidor nos marque como AWAY
        awayMessage = "Adios, Luke, hasta siempre!"
        self.ircServer.send(self.testNick, "AWAY :%s" % awayMessage)
        self.ircServer.expect(self.testNick, r":\S+ %s %s :\S+" % \
                              (codes['RPL_NOWAWAY'], self.testNick))                

        # Pedimos ahora un WHOIS al servidor, que deberá responder con un RPL_AWAY        
        self.ircServer.send(self.testNick, "WHOIS %s" % self.testNick)
        mensajes = self.ircServer.readAllLinesTill(self.testNick, "RPL_ENDOFWHOIS")        
        # Parseamos la respuesta        
        self._parseRPL_AWAYCommand(mensajes, awayMessage)
                         
        # Ahora enviamos un mensaje privado al usuario
        self.ircServer.send(self.testNick, "PRIVMSG %s :%s" % (self.testNick, "Hola, Luke, ¿cómo estás?"))
        
        # Leemos toda la respuesta hasta que salte el timeout                
        mensajes = self.ircServer.readAllLinesTill(self.testNick)
        # Parseamos la respuesta        
        self._parseRPL_AWAYCommand(mensajes, awayMessage)  
                
        # Finalmente pedidos que nos desmarque como AWAY
        self.ircServer.send(self.testNick, "AWAY")
        self.ircServer.expect(self.testNick, r":\S+ %s %s :\S+" % \
                              (codes['RPL_UNAWAY'], self.testNick))
        
        # Todo OK
        return self.getScore()
    
    def getDescription(self):
        return type(self).__name__ + " - Comprueba el funcionamiento del comando AWAY" 
        
    def getInfo(self):
        return """Esta prueba comprueba que el servidor reacciona correctamente al envio del comando AWAY.
Una vez que un usuario envie un /AWAY <mensaje>, el servidor debería marcar dicho usuario como en estado
"away". A partir de se momento, si se realiza un comando WHOIS, o se envia un mensaje privado al usuario, 
el servidor deberá incluir un código RPL_AWAY (301), incluyendo <mensaje>, en su salida."""


"""
    Prueba que comprueba el modo de protección de topic de un canal
    
    DEPENDENCIAS: - 
"""
class TestModoProteccionTopic(AdvancedTest):
                
    def execute(self):                       
         
        # Conexión al servidor        
        self.ircServer.connect(self.testNick)

        #        
        # 1. Probamos la protección del topic de un canal
        #
        # Creamos un canal de nombre aleatorio
        nuevoCanal = self.ircServer.generateRandomString()
        self.ircServer.joinChannel(self.testNick, nuevoCanal)
                
        # Generamos un topic aleatorio y lo establecemos
        topic = self.ircServer.generateRandomString()
        self.ircServer.setChannelTopic(self.testNick, nuevoCanal, topic)                 

        # Enviamos el comando de protección
        self.ircServer.send(self.testNick, "MODE #%s +t" % nuevoCanal)
        self.ircServer.expect(self.testNick, r":\S+ MODE #%s \+t" % nuevoCanal)                                      
                
        # El intento de cambio de topic por otro usuario debería dar ahora un error
        self.ircServer.connect(self.testNick2)
        self.ircServer.joinChannel(self.testNick2, nuevoCanal)
        self.ircServer.send(self.testNick2, "TOPIC #%s :%s" % (nuevoCanal, topic))
        self.ircServer.expect(self.testNick2, r":\S+ 482 %s #%s :\S+" % (self.testNick2, nuevoCanal))                
        
        # Cerramos todas las conexiones
        #self.ircServer.tearDown()        
        
        # Todo OK
        return self.getScore()
    
    def getDescription(self):
        return type(self).__name__ + " - Comprueba el modo de protección de topic de un canal" 
        
    def getInfo(self):
        return """Esta prueba genera un canal y topic aleatorios, y establece la protección
del mismo con el comando MODE. Luego un segundo usuario intenta cambiar dicho topic, a lo que
el servidor debería responder con un código 482 (ERR_CHANOPRIVSNEEDED)."""        

"""
    Prueba que comprueba el establecimiento de un canal secreto
    
    DEPENDENCIAS: - 
"""
class TestModoCanalSecreto(AdvancedTest):
                
    def execute(self):                       
         
        # Conexión al servidor        
        self.ircServer.connect(self.testNick)

        #        
        # 2. Probamos la generación de un canal secreto
        #
        # Creamos un canal de nombre aleatorio
        nuevoCanal = self.ircServer.generateRandomString()
        self.ircServer.joinChannel(self.testNick, nuevoCanal)
                
        # Lo hacemos secreto
        self.ircServer.send(self.testNick, "MODE #%s +s" % nuevoCanal)
        self.ircServer.expect(self.testNick, r":\S+ MODE #%s \+s" % nuevoCanal)                 

        # El canal no debe aparecer ahora en el listado de otro usuario
        self.ircServer.connect(self.testNick2)        
        #self.ircServer.joinChannel(self.testNick2, nuevoCanal)
        listaCanales = self.ircServer.getChannelList(self.testNick2)
        assert "#"+nuevoCanal not in listaCanales, "El canal secreto #%s no debería aparecer en la lista de canales." % nuevoCanal                                
        
        # Cerramos todas las conexiones
        #self.ircServer.tearDown()
        
        # Todo OK
        return self.getScore()
    
    def getDescription(self):
        return type(self).__name__ + " - Comprueba el modo de protección de topic de un canal" 
        
    def getInfo(self):
        return """Esta prueba genera un canal y topic aleatorios, y establece la protección
del mismo con el comando MODE. Luego un segundo usuario intenta cambiar dicho topic, a lo que
el servidor debería responder con un código 482 (ERR_CHANOPRIVSNEEDED)."""        

"""
    Prueba que comprueba el modo de protección con clave de un canal
    
    DEPENDENCIAS: - 
"""
class TestModoCanalProtegidoClave(AdvancedTest):
                
    def execute(self):                       
         
        # Conexión al servidor        
        self.ircServer.connect(self.testNick)

        #        
        # 1. Establecemos una clave para un canal
        #
        # Creamos un canal de nombre aleatorio
        nuevoCanal = self.ircServer.generateRandomString()
        self.ircServer.joinChannel(self.testNick, nuevoCanal)
        
        # Y una clave también aleatoria
        claveCanal = self.ircServer.generateRandomString()        
        # Enviamos el comando de protección
        self.ircServer.send(self.testNick, "MODE #%s \+k %s" % (nuevoCanal, claveCanal))
        
        # 2. Ahora comprobamos que otro usuario, sin la clave
        # correcta, no puede entrar en el canal
        self.ircServer.connect(self.testNick2)
        self.ircServer.send(self.testNick2, "JOIN #%s"  % nuevoCanal)
        self.ircServer.expect(self.testNick2, r":\S+ 475 %s #%s :\S+" % (self.testNick2, nuevoCanal))                
        
        # 3. Pero la puerta se abre con la clave correcta...                
        self.ircServer.joinChannel(self.testNick2, nuevoCanal, claveCanal)
                                            
        # Todo OK
        return self.getScore()
    
    def getDescription(self):
        return type(self).__name__ + " - Comprueba la protección de un canal con clave" 
        
    def getInfo(self):
        return """Esta prueba comprueba que el servidor gestiona correctamente la protección de 
un canal con clave. Un usuario crea un canal aleatorio, y establece una clave para él. Luego se
comprueba que otro usuario no puede unirse a él con una clave incorrecta, pero sí cuando ésta 
es la adecuada."""
        
"""
    Tests que comprueba el funcionamiento del comando QUIT
    
    DEPENDENCIAS: LIST 
"""
class TestComandoQuit(AdvancedTest):
                    
    def execute(self):                       
        retCode = False

        # Conexión al servidor        
        self.ircServer.connect(self.testNick)
        
        # Solicitamos que el servidor nos marque como AWAY        
        self.ircServer.send(self.testNick, "QUIT :Que la fuerza te acompañe...")

        # Leemos salida hasta timeout porque algún servidor responde con estadísticas
        mensajes = self.ircServer.readAllLinesTill(self.testNick)                

        # Ahora sí que deberíamos leer 0 bytes        
        data, num_bytes = self.ircServer.sd.sockets[self.testNick].recvfrom(1024)        
        assert num_bytes == None, "El servidor no ha procesado correctamente el comando QUIT"        
        
        # Esperamos un poco
        time.sleep(1)
        self.ircServer.tearDown()

        # Ahora nos volvemos a conectar, para comprobar que el servidor no se ha caido
        retCode = self.ircServer.connect(self.testNick)
        
        # Cerramos todas las conexiones
        assert retCode == True, "El servidor parece haberse caido tras procesar el comando QUIT"
        
        # Todo OK
        return self.getScore()
    
    def getDescription(self):
        return type(self).__name__ + " - Comprueba el funcionamiento del comando QUIT" 
        
    def getInfo(self):
        return """Esta prueba comprueba que el servidor procesa correctamente el comando QUIT.
Una vez enviado, el servidor puede opcionalmente un último mensaje sobre estadísticas de uso, y
luego, cerrar el socket con el cliente"""
        

"""
    Tests que comprueba el funcionamiento del comando MOTD
    
    DEPENDENCIAS: - 
"""
class TestComandoMOTD(AdvancedTest):
                    
    def execute(self):                       
         
        # Conexión al servidor        
        self.ircServer.connect(self.testNick)
        
        # Solicitamos que el servidor nos marque como AWAY        
        self.ircServer.send(self.testNick, "MOTD")                        

        # Leemos la respuesta        
        mensajes = self.ircServer.readAllLinesTill(self.testNick, "RPL_ENDOFMOTD")
                
        # La respuesta debe contener los mensajes 375, 372, 376
        assert mensajes.has_key("RPL_MOTDSTART"), "La respuesta del servidor no contiene el comando RPL_MOTDSTART"
        assert mensajes.has_key("RPL_MOTD"), "La respuesta del servidor no contiene el comando RPL_MOTD"
        assert mensajes.has_key("RPL_ENDOFMOTD"), "La respuesta del servidor no contiene el comando RPL_ENDOFMOTD"
                    
        # Todo OK
        return self.getScore()
    
    def getDescription(self):
        return type(self).__name__ + " - Comprueba el funcionamiento del comando MOTD" 
        
    def getInfo(self):
        return """Esta prueba verifica que el servidor reacciona correctamente al envio del comando MOTD.
Una vez enviado, el servidor debería responder con los mensajes RPL_MOTDSTART, RPL_MOTD y RPL_ENDOFMOTD,
en ese orden"""
        

"""
    Tests que comprueba el funcionamiento del envio de ficheros
    
    DEPENDENCIAS: - 
"""
class TestComandoDCCSend(AdvancedTest):
                    
    def execute(self):                       
         
        # Conexión al servidor        
        self.ircServer.connect(self.testNick)
        
        # Solicitamos que el servidor nos marque como AWAY        
        self.ircServer.send(self.testNick, "PRIVMSG %s :%sDCC SEND megane.pdf 3232235779 34382 1269453%s" % \
                            (self.testNick, b'\x01', b'\x01'))                                         
        #>> :oscar!~oscar@124.Red-95-122-126.staticIP.rima-tde.net PRIVMSG pepe :DCC SEND megane.pdf 1601863292 56289 1269453

        # Leemos la respuesta        
        mensajes = self.ircServer.readAllLinesTill(self.testNick)
                                    
        # Todo OK
        return self.getScore()
    
    def getDescription(self):
        return type(self).__name__ + " - Comprueba el funcionamiento del comando AWAY" 
        
    def getInfo(self):
        return """"""
        
"""
    Intento de abandonar un canal inexistente
    
    DEPENDENCIAS: LIST 
"""
class TestAbandonarCanalInexistente(AdvancedTest):
    
    def execute(self):                       
         
        # Conexión        
        self.ircServer.connect(self.testNick)
        
        # Generación de un canal temporal aleatorio...pero no hacemos JOIN
        tempCanal = self.ircServer.generateRandomString()        
        
        # Ahora enviamos el comando            
        self.ircServer.send(self.testNick, "PART #%s :Adios, mundo cruel!" % tempCanal)        
        self.ircServer.expect(self.testNick, r":\S+ %s %s #%s :\S+" % \
                              (codes['ERR_NOSUCHCHANNEL'], self.testNick, tempCanal))
                
        #Todo ha ido bien
        return self.getScore()        
    
    def getDescription(self):
        return type(self).__name__ + " - Intenta abandonar un canal inexistente" 
        
    def getInfo(self):
        return """Esta prueba comprueba que el servidor devuelve un código ERR_NOSUCHCHANNEL
cuando se intenta abandonar un canal inexistente"""
            
"""
    Tests que comprueba un comando JOIN malformado (sin argumentos)
    
    DEPENDENCIAS: LIST 
"""
class TestJoinSinArgumentos(AdvancedTest):
    
    def execute(self):                       
         
        # Conexión al servidor        
        self.ircServer.connect(self.testNick)
        
        # Envio de comando sin argumentos
        self.ircServer.send(self.testNick, "JOIN")
        self.ircServer.expect(self.testNick, r":\S+ %s %s JOIN :\S+" % \
                              (codes['ERR_NEEDMOREPARAMS'], self.testNick))
        
        return self.getScore()
    
    def getDescription(self):
        return type(self).__name__ + " - Comprueba el envio de una JOIN malformado" 
        
    def getInfo(self):
        return """Realiza el envio de un comando JOIN malformado (sin argumentos), y 
comprueba que el servidor reacciona correctamente"""            
            
class TestComandoWhoisSinNick(AdvancedTest):
    
    def execute(self):                
        
        self.ircServer.connect(self.testNick)
        
        # Envio del comando malformado (sin nick)                    
        self.ircServer.send(self.testNick, "WHOIS")
        self.ircServer.expect(self.testNick, r":\S+ %s %s :\S+" % \
                              (codes['ERR_NONICKNAMEGIVEN'], self.testNick))                
        
        return self.getScore()
                
    def getDescription(self):
        return type(self).__name__ + " - Envio de un comando WHOIS malformado" 
        
    def getInfo(self):
        return """Envio de un comando WHOIS malformado, sin especificar el usuario. La respuesta 
del servidor debería incluir el código de error ERR_NONICKNAMEGIVEN."""        
        

"""
    Solicita el topic de un canal al que se no ha establecido topic anteriormente. El 
    servidor debería devolver el código 331 "No topic is set"        
    DEPENDENCIAS: Conexión y registro
"""
class TestNoTopic(AdvancedTest):
    
    def execute(self):                

        # Conexión al servidor        
        self.ircServer.connect(self.testNick)
        
        # Creamos un canal de nombre aleatorio
        nuevoCanal = self.ircServer.generateRandomString()
        self.ircServer.joinChannel(self.testNick, nuevoCanal)
        
        # Solicitamos el topic del canal, que debería devolver un código RPL_NOTOPIC        
        self.ircServer.send(self.testNick, "TOPIC #%s" % nuevoCanal)                
        self.ircServer.expect(self.testNick, r":\S+ %s %s #%s :\S+" % \
                              (codes['RPL_NOTOPIC'], self.testNick, nuevoCanal))                        
        
        # Toda ha ido bien
        return self.getScore()                    
    
    def getDescription(self):
        return type(self).__name__ + " - Solicita el cambio del topic de un canal sin topic establecido" 
        
    def getInfo(self):
        return """Solicita el topic de un canal al que se no ha establecido topic anteriormente. El 
servidor debería devolver el código 331 (No topic is set)"""   
        

class TestMensajePrivadoANadie(AdvancedTest):
    
    def execute(self):
        
        # Conexión de dos usuarios al servidor
        self.ircServer.connect(self.testNick)
        nuevoNick = self.ircServer.generateRandomString()
        
        # Enviamos el mensaje a un usuario no existente
        self.ircServer.send(self.testNick, "PRIVMSG %s :Luke, ¡yo soy tu padre!" % nuevoNick)
        self.ircServer.expect(self.testNick, r":\S+ 401 %s %s :.*" % (self.testNick, nuevoNick))        
    
        # Todo ha ido bien
        return self.getScore()
    
    def getDescription(self):
        return type(self).__name__ + " - Intenta el envio de un mensaje a un usuario inexistente" 
        
    def getInfo(self):
        return """Comprueba que el envio de un mensaje privado a un usuario inexistente falla 
" y devuelve el código de error apropiado"""         
                    
    
class TestPruebaEstres(AdvancedTest):
    
    def execute(self):                
                    
        # Conectamos dos usuarios
        self.ircServer.connect(self.testNick)
        self.ircServer.connect(self.testNick2)
        
        # Creamos un canal aleatorio
        nuevoCanal = self.ircServer.generateRandomString()        
    
        # Enviamos el mensaje a un usuario no existente
        self.ircServer.joinChannel(self.testNick, nuevoCanal)
        self.ircServer.joinChannel(self.testNick2, nuevoCanal)
        
        # Enviamos multitud de mensajes privados
        for i in range(0,100):
            nuevoMensaje = self.ircServer.generateRandomString()
            self.ircServer.sendMessageToUser(self.testNick, self.testNick2, nuevoMensaje)
            
        # Ahora en el canal
        for i in range(0,100):
            nuevoMensaje = self.ircServer.generateRandomString()
            
            self.ircServer.sendMessageToChannel(self.testNick, [self.testNick2], nuevoCanal, nuevoMensaje)                            
                                    
        # Todo ha ido bien
        return self.getScore()                                
    
    def getDescription(self):
        return type(self).__name__ + " - Realiza una prueba de estrés al servidor" 
        
    def getInfo(self):
        return """Realiza una prueba de estrés al servidor, enviando muy rápidamente multitud de
mensajes privados a un usuario, y a un canal general"""         
        

"""
    Este test genera un comando y argumentos inexistentes de forma aleatoria, los 
    envía al servidor y  espera la respuesta, que debería ser un comando 421 (ERR_UNKNOWNCOMMAND)
    DEPENDENCIAS: Conexión
"""
class TestComandoDesconocido(AdvancedTest):
    
    def execute(self):                
            
        # Conexión con el servidor
        self.ircServer.connect(self.testNick)
        
        # Generamos un comando inexistente y sus argumentos de forma aleatoria        
        command = self.ircServer.generateRandomString().upper()
        args = self.ircServer.generateRandomString()
        self.ircServer.send(self.testNick, "%s %s" % (command, args))
        self.ircServer.expect(self.testNick, r":\S+ 421 %s %s :.*" % (self.testNick, command))
        
        #Todo ha ido bien
        return self.getScore()        
    
    def getDescription(self):
        return type(self).__name__ + " - Envia un comando desconocido (no definido) al servidor" 
        
    def getInfo(self):
        return """Este test genera un comando y argumentos inexistentes de forma aleatoria, los 
    envía al servidor y  espera la respuesta, que debería ser un comando 421 (ERR_UNKNOWNCOMMAND)"""        
        
