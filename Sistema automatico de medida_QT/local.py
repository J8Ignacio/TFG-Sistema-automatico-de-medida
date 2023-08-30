
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import  QThread, pyqtSignal
import visa
import pandas as pd
import queue
import sys
from datetime import datetime


#Definimos los hilos

#Hilo que accede a procal y realiza el barrido
class Hilo_Escritura(QThread):
    
    def __init__(self, cola, cola2):
        super().__init__()
        self.cola = cola
        self.cola2 = cola2
        self.volt_init = 0
        self.volt_final = 0
        self.volt_paso = 0
        self.error = False 
        self.tipo_error = None 
        self.mensaje = None

    def run(self):

        self.error, self.tipo_error = visa.barrido(self.volt_init, self.volt_final, self.volt_paso,  self.cola, self.cola2)
        
        if self.error == True:
            self.mensaje = ['Error', self.tipo_error]
            self.cola.put(self.mensaje)
  

    def param(self, volt_init, volt_fin, paso):
        self.volt_init = volt_init
        self.volt_final = volt_fin
        self.volt_paso = paso

#Hilo que se queda y va leyendo la cola
class Hilo_Lectura(QThread):

    mensaje_recibido = pyqtSignal(str)  #Señal que manda cuando recibe una señal, es de tipo str y será el mensaje recibido
   
    def __init__(self, cola, cola2):
        super().__init__()
        
        self.mensaje = None
        self.cola = cola
        self.cola2 = cola2
        self.parar = False
     
        
    def run(self):

        self.parar = False

        while True: #Cambiar para que pare cuando llegue el evento de los hilos
            
            self.mensaje = self.cola.get()

            if self.mensaje[0] == 'Error':
                

                self.mensaje_recibido.emit('Error')

            elif self.mensaje != None :
    
                self.mensaje_recibido.emit('Continua')
                
                if self.parar == False:
                    self.cola2.put('Continua')
                else:
                    self.cola2.put('Termina')
            else:
 
                self.mensaje_recibido.emit('Terminado')
    
    def obtener_mensaje(self):
        return self.mensaje
    
    def para(self):
        self.parar = True
    
    def devolver_error(self):
        return self.mensaje[1]



#variables globales
osciloscopio = None
generador = None
lista_voltaje = []
lista_generado = []
q = queue.Queue()
q2 = queue.Queue()
error = False
parado = False


def parar():
    global parado
    parado = True
    hilo_lectura.para()

def salir():
    visa.cerrar()
    sys.exit()

def abrir_instrumentos( osciloscopio, generador):
    global lista_visa
    global error    
    error = visa.abrir_recursos(lista_visa, osciloscopio, generador)

def cambiar_instrumento():

    #Se cierra los instrumentos abiertos

    visa.cerrar()
    global lista
    global lista_visa

    lista.clear()
    
    lista, lista_visa = visa.buscar_recursos()

    #Cargamos los elementos visa en la interfaz
    seleccion_instrumento.osciloscopio.clear()
    seleccion_instrumento.comboBox.clear()

    seleccion_instrumento.osciloscopio.addItems(lista)
    seleccion_instrumento.comboBox.addItems(lista)


    resultado.hide()
    seleccion_instrumento.show()

def mensaje_rec(mensaje):
    global lista_voltaje 
    global lista_generado
    global parado

  
    
    if mensaje == 'Continua':



        if parado == False:

            item = hilo_lectura.obtener_mensaje()
            lista_voltaje.append(item[0])
            lista_generado.append(item[1])
            cargando_ui.label_2.setText(f"Recibido: voltaje medido {lista_voltaje[-1]} y voltaje generado {lista_generado[-1]}")

        else:
            parado = True

    elif mensaje == 'Error':
        error = hilo_lectura.obtener_mensaje()

        cargando_ui.hide()
        error_iu.label_2.setText(error[1])
        error_iu.show()

    else:     
        mostrar_resultado()  


def comenzar_procal(volt_init, volt_final, paso):

        

        #Comienza el hilo que hace la lectura y el hilo que hace la escritura
        error_formato = False

        try:
            volt_init = float(volt_init)
            volt_final = float(volt_final)
            paso = float(paso)

            if (paso == 0):

                error_formato = True

            elif (paso < 0 and volt_init < volt_final):

                error_formato = True



        except:
            error_formato = True


        if( error_formato == False):
            hilo_lectura.start()
    
            hilo_escritura.param(float(volt_init), float(volt_final), float(paso))
        
            hilo_escritura.start()

            procal.hide()
            cargando_ui.label_2.setText("Esperando mensaje...")
            cargando_ui.show()

        else:
            procal.hide()
            erro_valores.show()

        


def abrir_instrumento():
    global osciloscopio
    global generador
    osciloscopio = seleccion_instrumento.osciloscopio.currentIndex()  #Guardamos el indice del instrumento seleccionado ya que va a ser el mismo indice que en la lista
    generador = seleccion_instrumento.comboBox.currentIndex()

    abrir_instrumentos(osciloscopio, generador)

    if(error == False):
        seleccion_instrumento.hide()
        error_iu.hide()
        procal.show()
    else:
        seleccion_instrumento.hide()
        error_iu.show()



def repetir_procal():
    cargando_ui.hide()
    resultado.hide()
    error_iu.hide()
    procal.show()

def mostrar_resultado():
    hilo_lectura.quit()
    hilo_escritura.quit()

    hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    #creamos csv poner en funcion a parte
    dato = {'Fecha y hora': hora, 'Voltaje generado_[V]' : lista_generado, 'Voltaje medido_[V]': lista_voltaje }


    df = pd.DataFrame(dato, columns= ['Fecha y hora', 'Voltaje generado_[V]', 'Voltaje medido_[V]'])


    df.to_csv((procal.lineEdit_4.text() + '.csv'), mode='a', index=False, header=True,sep=';',decimal=',')
    #creamos la grafica Poner en funcion a parte


    resultado.graphicsView.clear()

    resultado.graphicsView.plot(lista_voltaje, lista_generado) #x y


    #vaciamos las listas
    lista_voltaje.clear()
    lista_generado.clear()
    
    seleccion_instrumento.hide()
    error_iu.hide()   
    cargando_ui.hide()        
    resultado.show()

        

#***************************************Programa principal***************************************#

#Buscamos los elementos visa
lista, lista_visa = visa.buscar_recursos()


#Inicio de aplicacion
app = QtWidgets.QApplication([])

#creamos los hilos
hilo_lectura = Hilo_Lectura(q, q2)

hilo_escritura = Hilo_Escritura(q, q2)




hilo_lectura.mensaje_recibido.connect(mensaje_rec)


#carga archivos .ui
seleccion_instrumento = uic.loadUi('IU/seleccion_intrumento.ui')
procal = uic.loadUi('IU/procal.ui')
resultado = uic.loadUi('IU/resultado.ui')
error_iu = uic.loadUi('IU/error.ui')
cargando_ui = uic.loadUi('IU/cargando.ui')
erro_valores = uic.loadUi('IU/error_valores.ui')

#Cargamos 
seleccion_instrumento.osciloscopio.addItems(lista)
seleccion_instrumento.comboBox.addItems(lista)



#botones
seleccion_instrumento.pushButton.clicked.connect(abrir_instrumento)
seleccion_instrumento.pushButton_2.clicked.connect(cambiar_instrumento)
procal.comenzar_barrido.clicked.connect(lambda: comenzar_procal(procal.Volt_init.text(), procal.Volt_fin.text(),  procal.Paso.text()))
procal.Salir.clicked.connect(salir)
cargando_ui.pushButton.clicked.connect(parar)
resultado.otra_medida.clicked.connect(repetir_procal)
resultado.pushButton_3.clicked.connect(cambiar_instrumento)
resultado.salir.clicked.connect(salir)
error_iu.salir.clicked.connect(salir)
error_iu.otra_medida.clicked.connect(repetir_procal)
error_iu.pushButton_3.clicked.connect(cambiar_instrumento)
erro_valores.salir.clicked.connect(salir)
erro_valores.otra_medida.clicked.connect(repetir_procal)
erro_valores.pushButton_3.clicked.connect(cambiar_instrumento)


# Ejecutable
seleccion_instrumento.show()

app.exec()

