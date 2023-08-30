
import queue
import pyvisa
import time



def barrido_frecuencia(frec_init, frec_final, paso, q):
    
    rm = pyvisa.ResourceManager()
    lista = rm.list_resources()

    osciloscopio = rm.open_resource('USB0::0x0699::0x0362::C060465::INSTR')
    print("Se va a trabajar con el osciloscopio: ")
    print(osciloscopio.query('*IDN?') + '\n')  

    generador = rm.open_resource('ASRL3::INSTR')
    print("Se va a trabajar con el generador: ")
    print(generador.query('*IDN?') + '\n')  


    print("Configurando osciloscopio.\n")
    osciloscopio.write('*RST')
    #tenemos que poner un wait o si no no le da tiempo a cambiar de escala
    osciloscopio.write('CH1:SCALE 5')
    time.sleep(5)


    print("Configuramos el generador.\n")
    generador.write('SOURce:OUTPut ON')
    generador.write('SOURce:FUNCtion SINusoid')
    generador.write('SOURce:AMPLitude 1')

    

    for int in range (frec_init, frec_final, paso):  #Valor de inicio, valor final, el paso
        comando = "SOURce1:FREQUENCY " + str(int)
        generador.write(comando)

        osciloscopio.write('MEASUrement:IMMed:TYPe PK2pk')

        #Me fallaba el auto set, la grafica se salia por encima de la escala
        osciloscopio.write('CH1:SCAle 5')

        print("Frecuencia:  " + str(int) + "[Hz] -  Amplitud: ")
        medida = float(osciloscopio.query('MEASUrement:IMMed:VALue?' ))/10

        print(str(medida) + "[V]  " + str(medida*2) + "  [Vpp]\n")

        mensaje = [medida, int] #Se manda un mensaje con dos elementos, el primero es la medida y el segundo la frecuencia

        q.put(mensaje)

        print(f"Eviado: voltaje {medida} y frecuencia {int}" )

    q.put(None)

    
   
  
  

    generador.close()
    osciloscopio.close()
        