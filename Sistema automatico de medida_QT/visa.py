import pyvisa
import time




#Iniciamos las variable globales a None
osciloscopio = None
generador = None
rm = None


def range_with_floats(start, stop, step):
   if step > 0:
        while stop > start:
            yield start
            start += step
   else:
       while stop < start:
            yield start
            start += step

def buscar_recursos():
    global rm
    rm = pyvisa.ResourceManager()
    lista_idn =[]
    lista_visa = []
    for contador in range (len(rm.list_resources())):
        lista_visa = rm.list_resources()
        instrumento = rm.open_resource( lista_visa[contador])
        lista_idn.append(instrumento.query('*IDN?')[:-1])
        instrumento.close()
    
    return lista_idn,  lista_visa


def abrir_recursos(lista, oscilador_index, generador_index):
    try:
        global osciloscopio
        osciloscopio = rm.open_resource(lista[int(oscilador_index)])
        print("Se va a trabajar con el osciloscopio: ")
        print(osciloscopio.query('*IDN?') + '\n')
    except:
        return  True
        print("Error abriendo osciloscopio")  


    try:
        global generador
        generador = rm.open_resource(lista[int(generador_index)])
        print("Se va a trabajar con el generador: ")
        print(generador.query('*IDN?') + '\n')  
    except:
        return  True
        print("Error abriendo generador")

    return False

def cerrar():
    print('Cerrando generador')
    try:
        generador.close()
    except:
        print('Generador se desconectó inesperadamente')

    print('Cerrando osciloscopio')
    
    try:
        osciloscopio.close()
    except:
        print('Osciloscopio se desconectó inesperadamente')

    
    


def barrido(volt_init, volt_final, paso, q, q2):

    error = None

    print("Configurando osciloscopio.\n")
    print(osciloscopio)

    try:
        osciloscopio.write('*RST')
        osciloscopio.write('CH1:SCAle 5')
        time.sleep(3)
    except:
        
        error = 'Error configurando el osciloscopio'
        return  True


    print("Configuramos el generador.\n")
    try:
        generador.write('SOURce:OUTPut ON')
        generador.write('SOURce:FUNCtion SINusoid')
        generador.write('SOURce:AMPLitude 1')
        
    except:
        print('error')
        error = 'Error configurando el generador.'
        return True, error
    
    
    for int in range_with_floats(volt_init, volt_final, paso):  #Valor de inicio, valor final, el paso

        time.sleep(1)

        

        try:
            
            comando = "SOURce1:AMPLitude " + str(int)
            generador.write(comando)
        except:
            print('error')
            error = 'Error añadiendo el valor al generador'
            return True, error

        try:
            osciloscopio.write('CH1:SCAle 20')
            time.sleep(1)
            osciloscopio.write('MEASUrement:IMMed:TYPe PK2pk')

            medida = float(osciloscopio.query('MEASUrement:IMMed:VALue?' ))/20
        except:
            print('error')
            error = 'Error tomando la medida'
            return True, error

       
           

        mensaje = [medida, int] #Se manda un mensaje con dos elementos, el primero es la medida y el segundo la frecuencia



        q.put(mensaje)



        estado = q2.get()

        if estado == 'Termina':
            print('Termina en visa')
            break
    
    time.sleep(2) #Si no al hilo principal no le da tiempo a procesar los valores
    
    q.put(None)

  

   


    return False, None
  

 
        