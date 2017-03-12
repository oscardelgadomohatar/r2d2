#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""R2D2 - Redes 2 Droid 2.0 - Universidad Autónoma de Madrid

Usage:
  r2d2 [--verbose] [--servidor <IP_servidor>] [--puerto <puerto_servidor>] [--tests <rango_tests>]  
  r2d2 [--lista-tests]
  r2d2 [--info-test <numero_test>]  
  r2d2 [--version]      
  r2d2 [--verbose] [--corrector <dir>]
  r2d2 [--corrector <dir>]
  r2d2 (-h | --help)

Opciones:
  -h --help                     Muestra esta pantalla de ayuda
  --version                     Muestra la versión y sale
  --verbose                     Salida detallada 
  --servidor <IP_servidor>      Dirección IP del servidor IRC
  --puerto <puerto_servidor>    Puerto del servicio IRC del servidor
  --lista-tests                 Muestra una lista completa de todas las pruebas disponibles
  --tests <rango_tests>         Selecciona los tests a realizar. Las opciones son 'basicos', 'adv', 'errores' o uno o varios rangos númericos separados por comas
  --info-test <numero_test>     Muestra información detallada sobre una prueba concreta
  --corrector <dir>
"""

import sys, docopt, logging
from termcolor import colored
from ircTests import TipoTest
import ircTests, corrector

DEFAULT_SERVER_IP = '127.0.0.1'
DEFAULT_SERVER_PORT = 6667
BANNER = "R2D2 - Redes 2 Droid 2.0 - Universidad Autónoma de Madrid"

class ServerDroid(object):
    def __init__(self):
        # Valores por defecto
        self.serverIP = DEFAULT_SERVER_IP
        self.serverPort = DEFAULT_SERVER_PORT                
        self.connections = {}
        self.sockets = {}
        self.testsList = []
        self.basicTestsList = []
        self.advancedTestsList = []
        self.errorTestsList = []
        
        self.initTests()
        
    """
    """
    def initTests(self):     
    
        # Cargamos primero los tests básicos
        for obj in ircTests.basicTestsList:
            self.basicTestsList.append(obj(self))
        for obj in ircTests.advancedTestsList:
            self.advancedTestsList.append(obj(self))
        for obj in ircTests.errorTestsList:
            self.errorTestsList.append(obj(self))
            
        # Lista completa
        self.testsList = self.basicTestsList + self.advancedTestsList + self.errorTestsList               
                            
    def showTestsList(self):
        
        # Recorremos la lista de tests completa
        if (len(self.testsList) == 0):
            print "Uhmmmm, extraño esto es, sin duda. La lista de tests vacía está..."
            print "                                                          --- Yoda"
            return 
        
        print colored(BANNER, 'red')
        print
        
        print colored("Lista completa de pruebas", 'green')
        print colored("-------------------------", 'green')
        print
        print ("Pruebas básicas")
        
        numTest = 0
        for test in self.basicTestsList:
            print colored ("[%s] - %s" % (numTest, test.getDescription()), 'yellow')
            numTest += 1
    
        print
        print ("Pruebas avanzadas")
        
        for test in self.advancedTestsList:
            print colored ("[%s] - %s" % (numTest, test.getDescription()), 'yellow')
            numTest += 1
            
        print
        print ("Pruebas de gestión de errores")
        
        for test in self.errorTestsList:
            print colored ("[%s] - %s" % (numTest, test.getDescription()), 'yellow')
            numTest += 1
            
    """
        FUNC: Muestra información extendida sobre un test concreto.
        RECIBE: Número del test en la lista completa de tests
        DEVUELVE: -
    """    
    def showInfoTest (self, testNumber):
        print colored (BANNER, 'red')
        print
        
        try:
            test = self.testsList[int(testNumber)] 
            return test.getDescription() + '\n\n' + test.getInfo()
        except IndexError:
            print "ERROR: El número de prueba es inválido (try --list-tests for obtaining a complete list)"
            sys.exit()        



    """
        FUNCIÓN: Función que lanza todos los tests disponibles
        RECIBE: -
        DEVUELVE: -
    """
    def launchAllTests(self):        
        return self.launchCustomTests(self.testsList)
        
    """
        FUNCIÓN: Función que lanza los tests solicitados
        RECIBE: Lista con los objetos tests que deben ser lanzados
        DEVUELVE: -
    """
    def launchCustomTests(self, listaTests):
        
        print colored(BANNER, 'red')
        print                
        print ("Lanzando pruebas...")                                        
        
        try: 
            totalScore = numCorrectos = numIncorrectos = score = 0
            i = 1
            testEmpaquetadoEjecutado = testEmpaquetadoErroneo = False
            numTests = len(listaTests)
                        
            # Lanzamos cada test...    
            for test in listaTests:
                try:
                    print ((" %s/%s - %s" % (i, numTests, type(test).__name__)).ljust(50, '.')),
                    # Señalizamos el inicio y fin de la prueba
                    logging.debug("========== INICIO %s =============" % type(test).__name__)
                    score = test.execute()                    
                    logging.debug("========== FIN %s =============" % type(test).__name__)
                    
                    # Si no se ha producido ninguna excepción, el test ha ido bien
                    print colored('[CORRECTA] [%.2f] [%s]' % (score, test.tipoTest), 'green') 
                        
                
                    # Actualizamos el número de tests correctos                    
                    numCorrectos += 1                    
                    
                except AssertionError as ae:                    
                    # ¿Se trata del test de empaquetado?
                    if (test.tipoTest == TipoTest.EMPAQUETADO):
                        testEmpaquetadoErroneo = True
                    
                    # El test ha fallado                    
                    print colored('[INCORRECTA]', 'red')                    
                    print colored ("ERROR: %s" % ae, 'red')
                    numIncorrectos +=1            
                                                                                                 
                finally:
                    if test.tipoTest == TipoTest.EMPAQUETADO:
                        testEmpaquetadoEjecutado = True 
                    # Actualizamos la puntuación total y el número de tests incorrectos                                        
                    totalScore += score     
                    score = 0               
                    i += 1
                    
        except Exception as ae:                        
            print colored ("\nERROR: %s" % ae, 'red')
            print "Este es un error crítico y las pruebas no pueden continuar."
        finally:            
            # Mostramos resultados
            print "\n\nResultados"            
            print "----------\n"
            
            print "Pruebas correctas: %s/%s" % (numCorrectos, len(listaTests))
            print "Puntuación total: %.3f/%s " % (totalScore, 6),
            
            if totalScore >= 3 and testEmpaquetadoEjecutado and testEmpaquetadoErroneo == False:
                print colored ("[APROBADA]\n", 'green')
            else:
                print colored ("[SUSPENSA]\n", 'red')
                
            if testEmpaquetadoEjecutado == False or testEmpaquetadoErroneo:
                print colored("""\nATENCIÓN: La práctica no ha pasado la prueba de empaquetado, por lo que
ésta no puede ser entregada ni evaluada""", 'red')
                
            # Devolvemos una tupla de resultados
            return totalScore, "%s/%s" % (numCorrectos, len(listaTests)), testEmpaquetadoErroneo
    
        
if __name__ == "__main__":
    
    # Recogemos las opciones de uso del usuario
    arguments = docopt.docopt(__doc__, help = True, version='R2D2 Version 2.0 rev. 5')             
    
    # Creamos el objeto principal
    sd = ServerDroid()    
    listaTests = sd.testsList    
    
    # Se solicita el modo detallado        
    logLevel = logging.DEBUG if arguments['--verbose'] is True else logging.INFO             
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logLevel)        
    
    # Se solicita el empaquetado de una práctica
    #===========================================================================
    # if (arguments['--pack'] is not None):
    #     cPracticas = corrector.Corrector(sd)
    #     cPracticas.checkEmpaquetado(arguments['--pack'])
    #     sys.exit()
    #===========================================================================
    
    # Se solicita la corrección masiva de prácticas
    if (arguments['--corrector'] is not None):
        cPracticas = corrector.Corrector(sd)
        cPracticas.corrigePracticas(arguments['--corrector'])
        sys.exit()    
        
    # Se solicita mostrar la lista de tests
    if (arguments['--lista-tests'] is True):
        sd.showTestsList()
        sys.exit()
        
    # Parseamos las opciones y establecemos algunos valores
    if (arguments['--info-test'] is not None):
        # Muestra información sobre un test concreto
        print sd.showInfoTest(arguments['--info-test'])
        sys.exit()
    
    # IP y puerto del servidor
    if (arguments['--servidor'] is not None):
        sd.serverIP = arguments['--servidor']
    if (arguments['--puerto'] is not None):     
        sd.serverPort = int(arguments['--puerto'])
        
    if (arguments['--tests'] is not None):
        # ¿Se pide un test concreto?
        seleccion = arguments['--tests']
        
        if seleccion == 'basicos':
            listaTests = sd.basicTestsList
        elif seleccion == 'adv':
            listaTests = sd.advancedTestsList
        elif seleccion == 'errores':
            listaTests = sd.errorTestsList
        else:
            rangos = (x.split("-") for x in seleccion.split(","))
            # Generemos una lista con los números de los tests seleccionados
            listaTests = [sd.testsList[i] for r in rangos for i in range(int(r[0]), int(r[-1]) + 1)]        
    
    # Si listaTests es vacía, se ejecutarán todos los tests
    sd.launchCustomTests(listaTests)        

    
    
        
