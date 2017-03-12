#! /usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess, psutil, os.path, re, tarfile, logging, csv
from subprocess import PIPE
from termcolor import colored

BANNER = "R2D2 - Redes 2 Droid 2.0 - Universidad Autónoma de Madrid"
REGEXP_PRACTICA = r'G-(\d{4})-(\d{2})-P(\d)'
REGEXP_FICH_PRACTICA = REGEXP_PRACTICA + ".tar.gz"
NOMBRE_FICH_NOTAS = 'notas.csv'

LINEA_FICHERO_AUTORES = r'(\d{6})#(.+)'

class Corrector(object):
    def __init__(self, serverDroid):
        self.sd = serverDroid
    
    def _parseIdentificador(self, regexp, idAlumno):
        
        # Comprobamos que el nombre del directorio tiene el formato requerido, G-CCCC-NN-PX
        m = re.match(regexp, os.path.basename(idAlumno))
        assert m is not None, "El formato del directorio de entrada no es el requerido, G-CCCC-NN-PX"
        numGrupo = m.group(1)            
        logging.debug("Número de clase: %s" % numGrupo) 
        numPareja = m.group(2)
        logging.debug("Número de grupo: %s" % numPareja)
        numPractica = m.group(3)
        logging.debug("Número de práctica: %s" % numPractica)
        
        return numGrupo, numPareja, numPractica
    
    def extractFicheroPractica (self, ruta):
        # Abrimos el fichero en modo lectura
        try:
            fp = open (ruta, "r")
        except IOError:
            raise AssertionError("No se encuentra el fichero %r" % ruta)                        
        
        # Leemos la prímera línea, que debe ser del formato G-CCCC-NN-PX
        idGrupo = str(fp.readline())
        
        return idGrupo, fp
    
    """
        FUNCIÓN: Función que parsea el fichero de autores y comprueba su validez
        RECIBE: Ruta al fichero
        DEVUELVE: True si el formato es correcto, False en caso contrario
    """
    def checkFicheroAutores (self, ruta):
                
        listaAutores = []        
        
        # Leemos el nombre del fichero de la práctica
        idGrupo, fp = self.extractFicheroPractica(ruta)
               
        # Comprobamos que el nombre del directorio tiene el formato requerido, G-CCCC-NN-PX
        numGrupo, numPareja, numPractica = self._parseIdentificador(REGEXP_PRACTICA, idGrupo)   
        
        # Leemos el contenido
        autores = fp.readlines()            
        
        for autor in autores:
            # El formato de cada línea debe ser:
            #NIA#Apellidos, Nombre
            m = re.match(LINEA_FICHERO_AUTORES, autor)
            assert m is not None, "Error de sintaxis, linea incorrecta: %s" % autor

            NIA = m.group(1)            
            logging.debug("NIA: %s" % NIA) 
            apellidos = m.group(2)
            logging.debug("Apellidos, Nombre: %s" % apellidos)                                                    
        
            # Generamos el diccionario de autores
            dictAutor = {}
            dictAutor['Grupo'] = numGrupo
            dictAutor['Pareja'] = numPareja
            dictAutor['NIA'] = NIA
            dictAutor['Apellidos'] = apellidos            
            listaAutores.append(dictAutor)
            
        fp.close()
        
        return True, listaAutores
                
    """
        FUNCIÓN: Función que comprueba el empaquetado de una práctica
        RECIBE: Ruta al fichero .tar.gz 
        DEVUELVE: -
    """
    def checkEmpaquetado(self, nombreFichero):        
        
        # Lista con la estructura de ficheros requeridos en el empaquetado
        listaFichs = ['src','doc','srclib','includes','lib', 'obj', 'man']   
        
        logging.debug("Comprobando empaquetado [%s]..." %  nombreFichero)
        
        # 1. Comprobaciones sobre el fichero .tar.gz
        assert os.path.exists(nombreFichero), "No se encuentra el fichero %s" % nombreFichero
        assert tarfile.is_tarfile(nombreFichero), "El paquete no es un fichero TAR válido"
        
        # Comprobamos que el nombre del directorio tiene el formato requerido, G-CCCC-NN-PX
        numGrupo, numPareja, numPractica = self._parseIdentificador(REGEXP_FICH_PRACTICA, \
                                                                    os.path.basename(nombreFichero))        

        # Debemos aplicar la función dos veces porque .tar.gz son dos extensiones                        
        rutaBase = os.path.splitext(os.path.splitext(nombreFichero)[0])[0]
        
        assert not os.path.exists(rutaBase), "Ya existe la ruta base %s, probablemente de una ejecución previa. Debe borrarla para que sea válido el test de empaquetado" % rutaBase

        # 2. Descomprimiendo fichero...                
        logging.debug("Descomprimiendo archivo [%s]..." % nombreFichero)
        out = tarfile.open(nombreFichero)
        try:                
            out.extractall()
        except Exception:
            print colored("ERROR: ", 'red') + \
                colored("Extrayendo archivo [%s]" % nombreFichero, 'yellow')
            assert False, "Al extraer el tar.gz debe crearse automáticamente una carpeta, no extraerse en el mismo directorio"
        finally:                    
            out.close()                                
        
        # Comprobamos que existen los ficheros necesarios
        assert os.path.exists(rutaBase), "No se encuentra la ruta base %s, el tar.gz debe auto-descomprimirse creando este directorio" % rutaBase
        rutaMakefile = os.path.join(rutaBase, "Makefile")
        assert os.path.exists(rutaMakefile), "No se encuentra el fichero Makefile en %s" % rutaMakefile
        rutaEjecutableServidor = os.path.join(rutaBase, "irc_server")
        assert os.path.exists(rutaMakefile), "No se encuentra el ejecutable del servidor en %s" % rutaEjecutableServidor
        rutaFicheroAutores = os.path.join(rutaBase, "autores.txt")        
        assert os.path.exists(rutaFicheroAutores), "No se encuentra el fichero de autores en %s" % rutaFicheroAutores
        rutaFichMemoria = os.path.join(rutaBase, "doc", "G-%s-%s-P%s-doc.pdf" % (numGrupo, numPareja, numPractica))
        assert os.path.exists(rutaFichMemoria), "No se encuentra el fichero de la memoria en %s" % rutaFichMemoria 
        
                    
        # Comprobamos la estructura del directorio                        
        for directorio in listaFichs:
            assert os.path.exists(os.path.join(rutaBase, directorio)), "Se requiere el directorio [%s]" % directorio

        # 3. Parseamos el fichero de autores                
        logging.debug("Parseando ficheros de autores [%s]..." % rutaFicheroAutores)        
        assert self.checkFicheroAutores(rutaFicheroAutores), "Formato del fichero de autores incorrecto"                                                                                                                                                        
    
    def _mataServidor (self, nombreServidor):   
             
        for proc in psutil.process_iter():
        # check whether the process name matches
            if proc.name() == nombreServidor:
                proc.kill()
                proc.wait(timeout=3)                                

                # Nos aseguramos que el proceso ha muerto
                assert proc.pid not in psutil.pids()         
                
    """
        FUNCIÓN: Función que corrige de forma masiva prácticas
        RECIBE: Ruta al directorio que contiene los ficheros .tgz 
        DEVUELVE: -
    """
    def corrigePracticas(self, dirEntrada):        
        
        try:
            print "Corrigiendo prácticas en [%s]..." %  dirEntrada
            
            # 1. Listamos los archivos del directorio
            listaPracticas = os.listdir(dirEntrada)
            numFicheros = len(listaPracticas)
            
            # 2. Filtramos los ficheros adecuados            
            listaPracticas = [os.path.join(dirEntrada, practica) \
                               for practica in listaPracticas if \
                                os.path.isfile(os.path.join(dirEntrada, practica)) and \
                                # 3. Comprobamos que el nombre del directorio tiene el formato requerido, G-CCCC-NN-PX
                                re.match(REGEXP_FICH_PRACTICA, practica) is not None ]
            print "Encontrados %s/%s ficheros de prácticas válidas" % \
                                    (len(listaPracticas), numFicheros)                                                    
    
            # Fichero de notas
            rutaFicheroNotas = os.path.join(dirEntrada, NOMBRE_FICH_NOTAS)
            fichNotas = open(rutaFicheroNotas, 'w')
            fieldnames = ['Grupo', 'Pareja', 'NIA', 'Apellidos', 'Nota']
            writer = csv.DictWriter(fichNotas, fieldnames=fieldnames)
    
            # Escribimos la cabecera
            writer.writeheader()    
            
            # 2. Comprobamos cada fichero
            for rutaCompleta in listaPracticas:                                 
                # 3.1 Nombre ficheros
                ficheroConExtension = os.path.basename(rutaCompleta)
                ficheroSinExtension = ficheroConExtension[:-7]
                rutaBase = os.path.join(os.path.dirname(rutaCompleta), ficheroSinExtension)
                
                # 3. Descomprimiendo fichero...                
                print "Descomprimiendo archivo [%s]..." % rutaCompleta
                out = tarfile.open(rutaCompleta)
                try:                
                    out.extractall(dirEntrada)
                except Exception:
                    print colored("ERROR: ", 'red') + \
                        colored("Extrayendo archivo [%s]" % rutaCompleta, 'yellow')
                finally:                    
                    out.close()                                

                # 4. Parseamos el fichero de autores
                print "Parseando ficheros de autores..."
                rtnCode, autores = self.checkFicheroAutores(os.path.join(rutaBase, 'autores.txt'))
                if rtnCode == False:                                        
                    continue                                    
                                                              
                # 5. Compilamos la práctica
                print "Compilando práctica [%s]..." % rutaBase                                
                rtnCode = subprocess.call(['make'], cwd = rutaBase)
                if rtnCode > 0:
                    print colored ("[ERROR] Error en la compilación", 'red')                    
                    continue
                
                # Comprobamos que no existe ninguna instancia de servidor corriendo anteriormente
                self._mataServidor("irc_server")
                
                # 6. Ejecutamos el servidor, comprobando que ha sido lanzado correctamente
                ficheroServidor = os.path.join(rutaBase, 'irc_server')
                print "Lanzando servidor [%s]..." % ficheroServidor,
                p = psutil.Popen(['%s' % ficheroServidor], stdout=PIPE)                                                
                if p is None:
                    print colored ("[ERROR] Error lanzando servidor", 'red')                    
                    continue
                
                serverPID = p.pid
                print "OK. PID [%s]" % serverPID                                 
            
                # 7. Ejecutamos los tests
                totalScore, numCorrectos, testEmpaquetadoErroneo = self.sd.launchAllTests()                                   
            
                # 8. Matamos el proceso del servidor
                print "Terminando servidor [%s]..." % ficheroServidor,
                self._mataServidor("irc_server") 
                print "OK. PID [%s]" % serverPID
                                
                # Guardamos las notas de ejecución                                                
                for autor in autores:
                    autor['Nota'] = totalScore                 
                    writer.writerow(autor)        
                                                                
        except Exception as e:
            raise
            print "ERROR: %s" % e
        finally:
            fichNotas.close()
