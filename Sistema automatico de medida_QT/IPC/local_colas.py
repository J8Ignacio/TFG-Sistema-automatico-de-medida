import threading
import queue
import visa_colas
from bokeh.plotting import figure, output_file, show
from bokeh.io import export_png

   

        
q = queue.Queue()

medida_hilo = threading.Thread(target= visa_colas.barrido_frecuencia, args=(100,1000,100, q,))


medida_hilo.start()

lista_voltaje = []
lista_frecuencia = []
        
while True:
        
        item = q.get()
        
        if item is None:
            break

        lista_voltaje.append(item[0])
        lista_frecuencia.append(item[1])

        print(f"Recibido: voltaje {lista_voltaje[-1]} y frecuencia {lista_frecuencia[-1]}") #En python las posiciones negativas son las ultimas, -1 es el último, -2 el penultimo etc etc

  #Añadimpos la grafica
p = figure(
    title = 'Simple Example',
    x_axis_label='X Axis',
    y_axis_label='Y_Axis',
)

#export_png(p, filename="plot.png")

#Render glyph
p.line(lista_frecuencia, lista_voltaje)

show(p)