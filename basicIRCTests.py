# -*- coding: utf-8 -*-
import logging, ircparser, ircTests
from ircTests import IRCTest, TipoTest
from corrector import Corrector

class BasicTest(IRCTest):
    
    tipoTest = TipoTest.BASICO
    
    # Hay que restar uno porque la prueba de empaquetado no puntúa
    def getScore(self):                
        return self.basicTestsScore/float(len(ircTests.basicTestsList) - 1)         

"""
    Los tests, en general, señalizan su fallo lanzando una excepción AssertionError. Si todo va bien,
    devuelven su puntuación. Hay pruebas esenciales, como TestConnectionRegistration, cuyo fallo 
    implica que los tests no pueden continuar. Para ello, un test debe lanzar una excepción diferente
    a AssertionError. 
"""
class TestConexionRegistro(BasicTest):
    
    def execute(self):        
                                
        # Conexión al servidor
        self.ircServer.connect(self.testNick)                                                             
        
        # Todo ha ido bien
        return self.getScore()
    
    def getDescription(self):
        return type(self).__name__ + " - Comprueba la conexión y registro al servidor IRC" 
        
    def getInfo(self):
        return """Este test comprueba la conexión y registro de un usuario contra el servidor IRC.
Para ello, envia los comandos USER y NICK, y parsea las respuestas."""            


"""
    Test que comprueba el comando JOIN. Necesita que LIST funcione correctamente para
    comprobar que el usuario se ha unido correctamente al canal.
    
    DEPENDENCIAS: LIST 
"""
class TestComandoJoin(BasicTest):
    
    def execute(self):                        
                
        # Conexión al servidor
        self.ircServer.connect(self.testNick)        
        
        # Se envían los comandos de registro
        canalTemp = self.ircServer.generateRandomString()       
        self.ircServer.joinChannel(self.testNick, canalTemp)                                           

        # Obtenemos la lista de canales del servidor
        listaCanales = self.ircServer.getChannelList(self.testNick)                                    
        
        # Todo ha ido bien
        assert "#" + canalTemp in listaCanales, "Canal creado [%s] no aparece en la lista del servidor" % canalTemp
    
        return self.getScore()
    
    def getDescription(self):
        return type(self).__name__ + " - Prueba del comando JOIN" 
        
    def getInfo(self):
        return """Test que comprueba el comando JOIN. Genera un nick y nombre de canal aleatorios, y 
añade el usuario a dicho canal. Luego pide la lista de canales al servidor y comprueba que el usuario
está en dicha lista, por lo que necesita que el comando LIST funcione correctamente."""            


"""
    INFO: Este test comprueba el comando LIST. Para ello crea 5 canales de nombre aleatorio, 
    a través del comando JOIN, y comprueba que se devuelven sus nombres correctamente
    DEPENDENCIAS: JOIN
"""
class TestComandoList(BasicTest):
    
    def execute(self):        
                
        # Conexión al servidor        
        self.ircServer.connect(self.testNick)                
        
        listaCanales = []
        numCanales = 5
        
        # Se realizan 5 JOINS a canales con nombres aleatorios
        for x in range(numCanales):
            nombreCanal = self.ircServer.generateRandomString()
            self.ircServer.joinChannel(self.testNick, nombreCanal)
            listaCanales.append('#' + nombreCanal)            
        
        logging.debug("Canales creados: %s" % listaCanales)
        
        # Algunas comprobaciones    
        assert len(listaCanales) == numCanales, "Número de canales creados incorrecto"
        
        # Solicitamos la lista de canales
        listaReal = self.ircServer.getChannelList(self.testNick)                                
        logging.debug("Lista de canales: %s" % listaReal)
        
        # Comprobamos que están todos los canales creados
        for nombre in listaCanales:
            assert nombre in listaReal, "Canal %s no encontrado en lista de canales" % nombre                                     
        
        # Todo ha ido bien
        return self.getScore()
        
    def getDescription(self):
        return type(self).__name__ + " - Prueba del comando LIST" 
        
    def getInfo(self):
        return """Este test comprueba el comando LIST. Para ello crea 5 canales de nombre aleatorio, 
    se une a ellos a través del comando JOIN, y comprueba que se devuelven sus nombres correctamente."""            
    

"""
    INFO: Comprueba el funcionamiento del comando WHOIS. Para ello envia el comando y parsea la respuesta
    DEPENDENCIAS: JOIN
"""
class TestComandoWhois(BasicTest):
    
    def execute(self):                

        # Puntuación por los mensajes extra (+ 20%)
        extraScore = self.getScore() * 0.2
        localScore = 0
        receivedMessages = []        
        
        # Conexión y envio del comnado        
        self.ircServer.connect(self.testNick)
        
        # Conectamos el usuario a un canal aleatorio
        tempCanal = self.ircServer.generateRandomString()
        self.ircServer.joinChannel(self.testNick, tempCanal)
        
        # Ahora enviamos el comando            
        self.ircServer.send(self.testNick, "WHOIS %s" % self.testNick)
                      
        # Recepción y parseo de la respuesta                      
        message = ircparser.translate(self.ircServer._readLine(self.testNick))                                       
        
        # TODO: Este bucle puede no terminar nunca, mejorar                 
        # Hacer una función que devuelva una lista de 'message', con un límite máxmo
        # de líneas leidas antes de dar ERROR
        while (message['command'] is not "RPL_ENDOFWHOIS"):
            # Cada mensaje que se muestre en la respuesta suma puntuación                
            if message['command'] == 'RPL_WHOISUSER':
                localScore += extraScore                   
            if message['command'] == 'RPL_WHOISSERVER':
                localScore += extraScore                                    
            # Obtenemos los canales en los que está este usuario
            if (message['command'] == 'RPL_WHOISCHANNELS'):
                # Comprobamos que está el canal recién creado
                assert "@#" + tempCanal in message['params'][2].split(' '),\
                    "Comando WHOIS no devuelve correctamente los canales en los que está el usuario"                
                receivedMessages.append('RPL_WHOISCHANNELS')
                
            # Recepción y parseo de la respuesta                      
            message = ircparser.translate(self.ircServer._readLine(self.testNick))            
            assert message is not None, "Se ha recibido una respuesta vacía del servidor"
            
        # Comprobación de que se han recibido los mensajes correctos
        # Detección de duplicados
        assert len(set(receivedMessages)) == len(receivedMessages) and \
            'RPL_WHOISCHANNELS' in receivedMessages, "No se ha recibido el código RPL_WHOISCHANNELS del servidor"            
                    
        # Todo ha ido bien
        # return self.getScore() + localScore
        return self.getScore()
            
    def getDescription(self):
        return type(self).__name__ + " - Prueba del comando WHOIS" 
        
    def getInfo(self):
        return """Esta prueba verifica el funcionamiento del comando WHOIS de la siguientes forma: 
  1. Crea un canal de nombre aleatorio. 
  2. Une al usuario de pruebas al canal, y envía el comando WHOIS apropiado. 
  3. Verifica la respuesta y espera encontrar los RPL_WHOISCHANNELS y RPL_ENDWHOIS. Opcionalmente \
también los comandos RPL_WHOISUSER y RPL_WHOISSERVER (no son imprescindibles, pero suman puntuación)."""            

"""
    INFO: Comprueba el funcionamiento del comando NAMES
    DEPENDENCIAS: -
"""
class TestComandoNames(BasicTest):
    
    def execute(self):                

        # Conexión al servidor        
        self.ircServer.connect(self.testNick)
        
        # Nos unimos a un canal de nombre aleatorio
        nuevoCanal = self.ircServer.generateRandomString()
        self.ircServer.joinChannel(self.testNick, nuevoCanal)                
        
        # Pedimos la lista de usuarios del canal
        listaUsuarios = self.ircServer.getChannelUsers(self.testNick, nuevoCanal)
                        
        # ¿Está el usuario en la lista?
        assert self.testNick in listaUsuarios, "No está %s en la lista de usuarios del canal %s" % (self.testNick, nuevoCanal)
        
        # Todo ha ido bien
        return self.getScore()                    
    
    def getDescription(self):
        return type(self).__name__ + " - Prueba del comando NAMES"
        
    def getInfo(self):
        return """ - Comprueba el comando NAMES, usado para listar los usuarios de un canal. Para ello \
crea un canal de nombre aleatorio, envía el comando NAMES y comprueba que el nick del usuario se encuentra en la lista \
devuelta."""         
        

"""
    INFO: Comprueba el cambio de nick de un usuario
    DEPENDENCIAS: NAMES
"""
class TestCambioNick(BasicTest):
    
    def execute(self):                

        # Conexión al servidor        
        self.ircServer.connect(self.testNick)
        
        # Nos unimos a un canal de nombre aleatorio
        nuevoCanal = self.ircServer.generateRandomString()
        self.ircServer.joinChannel(self.testNick, nuevoCanal)
        
        # Generación del nuevo nick
        nuevoNick = self.ircServer.generateRandomString()
        logging.debug ("Cambiando nick de [%s] a [%s]..." % (self.testNick, nuevoNick))
        self.ircServer.send(self.testNick, "NICK %s" % nuevoNick)
        self.ircServer.expect(self.testNick, r":\S+ NICK :%s" % nuevoNick)                

        # Comprobamos que el viejo nick no está ya en el canal y que el nuevo sí
        listaUsuarios = self.ircServer.getChannelUsers(self.testNick, nuevoCanal)
        assert self.testNick not in listaUsuarios, "Sigue estando %s en la lista de usuarios del canal %s tras el cambio de nick" % (self.testNick, nuevoCanal)
        assert nuevoNick in listaUsuarios, "No está %s en la lista de usuarios del canal %s tras el cambio de nick" % (nuevoNick, nuevoCanal)
                
        # Dejamos el nick como estaba, para continuar con las pruebas
        self.ircServer.send(self.testNick, "NICK %s" % self.testNick)
        self.ircServer.expect(self.testNick, r":\S+ NICK :%s" % self.testNick)
    
        # Todo ha ido bien
        return self.getScore()
    
    def getDescription(self):
        return type(self).__name__ + " - Comprueba el cambio de nick de un usuario" 
        
    def getInfo(self):
        return """Esta prueba comprueba que el servidor realiza un cambio de nick correctamente.\
Para ello genera un nick y nombre de canal aleatorios, solicita el cambio de nick, añade éste \ 
nuevo usuario al canal y comprueba que el nuevo nick está en la lista de usuarios (y que no \
está el antiguo). Finalmente, vuelve a realizar un cambio de nick para volver a utilizar \
el nick de pruebas original."""
          
        
"""
    Comprueba el comando TOPIC, que cambia el topic de un canal. Para ello:
        1. Crea un canal de nombre y topic aleatorio, y comprueba que se han creado correctamente.
        2. Cambia el topic a otro valor, también aleatorio.
        3. Comprueba que el nuevo topic ha sido cambiado correctamente.
    DEPENDENCIAS:
"""
class TestCambioTopic(BasicTest):
    
    def execute(self):                

        # Conexión al servidor
        self.ircServer.connect(self.testNick)
        
        # Creamos un canal de nombre aleatorio
        nuevoCanal = self.ircServer.generateRandomString()
        self.ircServer.joinChannel(self.testNick, nuevoCanal)
                
        # Generamos un topic aleatorio y lo cambiamos
        topic = self.ircServer.generateRandomString()
        self.ircServer.setChannelTopic(self.testNick, nuevoCanal, topic)                
                                            
        # Todo ha ido bien
        return self.getScore()                                
    
    def getDescription(self):
        return type(self).__name__ + " - Comprueba el correcto cambio del TOPIC de un canal" 
        
    def getInfo(self):
        return "Comprueba el comando TOPIC, que cambia el topic de un canal. Para ello: \n" \
            "1. Crea un canal de nombre y topic aleatorio, y comprueba que se han creado correctamente.\n" \
            "2. Cambia el topic a otro valor, también aleatorio.\n" \
            "3. Comprueba que el nuevo topic ha sido cambiado correctamente.\n"         

        
    """
    Comprueba el comando KICK, que expulsa a un usuario de un canal. 
        1. El operador del canal expulsa a un usuario
        2. Un usuario intenta expulsar a un operador, lo que debería fallar informando
        de que no se poseen privilegios suficientes
    DEPENDENCIAS:
"""
class TestComandoKick(BasicTest):
    
    def execute(self):                

        # Necesitamos dos usuarios
        self.ircServer.connect(self.testNick)
        self.ircServer.connect(self.testNick2)
        
        # Creamos un canal de nombre aleatorio
        nuevoCanal = self.ircServer.generateRandomString()
        # Al ser los creadores del canal, somos también operadores del mismo
        self.ircServer.joinChannel(self.testNick, nuevoCanal)
        self.ircServer.joinChannel(self.testNick2, nuevoCanal)
        
        # Echamos al usuario 2 del canal        
        self.ircServer.send(self.testNick, "KICK #%s %s :Fuera de aqui, rata!" % (nuevoCanal, self.testNick2))
        logging.debug("Ahora se espera recibir el KICK por el socket de %s" % self.testNick2)
        self.ircServer.expect(self.testNick2, r":\S+ KICK #%s %s :Fuera de aqui, rata!" % (nuevoCanal, self.testNick2))
        
        # Volvemos a unir el usario 2 al canal...
        self.ircServer.joinChannel(self.testNick2, nuevoCanal)
        # ...e intentamos echar al operador
        self.ircServer.send(self.testNick2, "KICK #%s %s :Fuera de aqui, rata!" % (nuevoCanal, self.testNick))
        # Deberíamos recibir un comando 482
        self.ircServer.expect(self.testNick2, r":\S+ 482 %s #%s :\S+" % (self.testNick2, nuevoCanal))        
                   
        self.ircServer.discardAll(self.testNick)
        self.ircServer.discardAll(self.testNick2)
        #self.ircServer.tearDown()
                          
        # Todo ha ido bien
        return self.getScore()                                    
    
    def getDescription(self):
        return type(self).__name__ + " - Comprueba la expulsión de un usuario (KICK)" 
        
    def getInfo(self):
        return """Comprueba el comando KICK, que expulsa a un usuario de un canal. 
        1. El operador del canal expulsa a un usuario
        2. Un usuario intenta expulsar a un operador, lo que debería fallar informando
        de que no se poseen privilegios suficientes"""         
            
"""
    Comprueba el envío y recepción de mensajes privados entre dos usuarios             
    DEPENDENCIAS: Conexión y registro
"""
class TestMensajePrivado(BasicTest):
    
    def execute(self):
        
        # Conexión de dos usuarios al servidor
        nick1 = self.ircServer.generateRandomString()
        nick2 = self.ircServer.generateRandomString()
        self.ircServer.connect(nick1)        
        self.ircServer.connect(nick2)
        
        # Enviamos el mensaje 
        self.ircServer.sendMessageToUser(nick1, nick2, "Luke, yo soy tu padre")                        

        # Todo ha ido bien
        return self.getScore()
    
    def getDescription(self):
        return type(self).__name__ + " - Comprueba el envio y recepción de mensajes privados" 
        
    def getInfo(self):
        return """Comprueba el envio y recepción de mensajes privados entre dos usuarios de nicks
aleatorios, que pueden no conectados a un canal"""         


"""
    Comprueba el envío y recepción de mensajes a un canal             
    DEPENDENCIAS: Conexión y registro
"""
class TestMensajeACanal(BasicTest):
    
    def execute(self):
        
        # Conexión de tres usuarios al servidor y un canal aleatorio
        nick1 = self.ircServer.generateRandomString()                        
        self.ircServer.connect(nick1)                       
        nick2 = self.ircServer.generateRandomString()                        
        self.ircServer.connect(nick2)
        nick3 = self.ircServer.generateRandomString()                        
        self.ircServer.connect(nick3)        
        canalTemp = self.ircServer.generateRandomString()        
        
        self.ircServer.joinChannel(nick1, canalTemp)
        self.ircServer.joinChannel(nick2, canalTemp)
        self.ircServer.joinChannel(nick3, canalTemp)
        
        # Enviamos el mensaje 
        self.ircServer.sendMessageToChannel(nick1, [nick2, nick3], canalTemp, "Hi everybody!!")                                
            
        # Todo ha ido bien
        return self.getScore()
    
    def getDescription(self):
        return type(self).__name__ + " - Comprueba el envio y recepción de mensajes a un canal" 
        
    def getInfo(self):
        return """Comprueba el envio y recepción de mensajes privados entre dos usuarios de nicks
aleatorios, que pueden no conectados a un canal"""

        
"""
    Este test comprueba que el servidor responde adecuadamente al comando PING de un cliente
    DEPENDENCIAS: Conexión
"""
class TestPingPong(BasicTest):
    
    def execute(self):       
                 
        # Conexión de dos usuarios al servidor        
        self.ircServer.connect(self.testNick)
        cadenaPing = self.ircServer.generateRandomString()
        
        # Enviamos el mensaje 
        self.ircServer.send(self.testNick, "PING LAG%s" % cadenaPing)
        self.ircServer.expect(self.testNick, r":\S+ PONG \S+ :LAG%s" % cadenaPing)
        
        #Todo ha ido bien
        return self.getScore()        
    
    def getDescription(self):
        return type(self).__name__ + " - Envia un comando PING al servidor" 
        
    def getInfo(self):
        return """Esta prueba envia un comando PING al servidor, junto con una cadena LAG aleatoria,
que debe ser respondido con un PONG y la misma cadena"""            
        
    
"""
    Comprueba que un usuario abandona correctamente un canal
    DEPENDENCIAS: Conexión, NAMES
"""
class TestAbandonarCanal(BasicTest):
    
    def execute(self):       
                 
        # Conexión        
        self.ircServer.connect(self.testNick)
        
        # Generación de un canal temporal aleatorio
        tempCanal = self.ircServer.generateRandomString()
        self.ircServer.joinChannel(self.testNick, tempCanal)
        
        # Ahora enviamos el comando            
        self.ircServer.send(self.testNick, "PART #%s :Adios, mundo cruel!" % tempCanal)
        self.ircServer.expect(self.testNick, r":\S+ PART #%s :.*" % tempCanal)
                
        # Comprobamos que el usuario efectivamente ya no se devuelve en ese canal
        listaUsuarios = self.ircServer.getChannelUsers (self.testNick, tempCanal)
        
        assert self.testNick not in listaUsuarios, "Sigue estando %s en la lista de usuarios del canal %s" % (self.testNick, tempCanal)
        
        #Todo ha ido bien
        return self.getScore()        
    
    def getDescription(self):
        return type(self).__name__ + " - Comprueba que un usuario abandona correctamente un canal (PART)" 
        
    def getInfo(self):
        return """Comprueba que un usuario abandona correctamente un canal, a través del uso del 
comando PART. Se espera que el servidor confirme la salida, y luego se verifica que, efectivamente,
el usuario ya no se encuentra en el canal con el comando NAMES"""             

"""
    Comprueba el empaquetado de la práctica
"""
class TestEmpaquetado(BasicTest):
    
    tipoTest = TipoTest.EMPAQUETADO
    
    def execute(self):        
                        
        # Conexión al servidor
        corrector = Corrector(self.sd)                                                             
        
        # Comprobamos y parseamos el fichero autores.txt
        ficheroPractica, fp = corrector.extractFicheroPractica('autores.txt')
        
        # Comprobamos el empaquetado
        corrector.checkEmpaquetado(ficheroPractica.rstrip('\r\n ') + '.tar.gz')
        
        # Todo ha ido bien
        return self.getScore()
    
    def getDescription(self):
        return type(self).__name__ + " - Comprueba el correcto empaquetado de la práctica" 
        
    def getInfo(self):
        return """Este test comprueba el correcto empaquetado de la práctica. Para ello necesita 
que existan los ficheros 'autores.txt' y 'G-CCCC-NN-PX.tar.gz' en el mismo directorio desde
donde se ejecuta el corrector. Los detalles del formato de estos ficheros pueden encontrarse
en el manual de uso"""    

    # Esta prueba es no evaluable
    def getScore(self):                
        return 0
