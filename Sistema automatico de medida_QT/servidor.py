from flask import Flask, render_template, request, redirect, url_for, send_file    #render_template nos sirve para enviar archivos html en cada pagina
from visa import barrido, buscar_recursos, abrir_recursos, cerrar
import threading
from bokeh.plotting import figure
from bokeh.io import export_png
import pandas as pd
import queue
import sys
from datetime import datetime



#Esta variable app la vamos  usar para crear nuestras rutas del servidor para crear nuestras url
app = Flask(__name__)
app.USE_X_SENDFILE = True

lista = []
lista_idn = []
Nombre = None
tipo_error = None
lista_voltaje = []
lista_generado = []
estado = 0
q = queue.Queue()
q2 = queue.Queue()


#Definimos los hilos
def run_escritura(volt_init, volt_final, paso, q, q2):

    global tipo_error

    error, tipo_error = barrido(volt_init, volt_final, paso, q, q2)

    if error ==True:
        q.put('Error')
    


def comenzar_procal(volt_init, volt_final, paso):
        
        t_escritura = threading.Thread(target = run_escritura, args = (volt_init, volt_final, paso, q, q2))
        t_escritura.start()
        




#Crear nuestras ruta. Route() nos da una pagina con el nombre que le metamos
#le decimos que esta es nuetra pagina principal


#PAGINA INICIAL
@app.route('/',  methods= ['POST', 'GET']) #los nombres que "sale arriba" navegando en una web
#Nos dice qué vamos a ver en nuestra página principal
def buscar_instrumento():
    if request.method == 'GET':
        
        return render_template('buscar_instrumentos.html')
    
    elif request.method == 'POST':

        global lista
        global lista_visa

        lista, lista_visa = buscar_recursos()
        
        return redirect(url_for('seleccion'))
    else:
       
        return 'Metodo no aceptado'


#PAGINA DONDE SE SELECCIONA QUÉ INTRUMENTOS USAR
@app.route('/seleccion', methods= ['POST', 'GET'])

def seleccion():
    if request.method == 'GET':
        global lista
        global lista_visa
        global data
        return render_template('seleccionar_intrumento.html', lista_instr = lista)
    
    elif request.method == 'POST':
        
        if request.form['submit_button'] == 'Comenzar':
            lista
            data = request.form.to_dict() 
            
            
            error = abrir_recursos(lista_visa, data.get('osciloscopio'), data.get('generador'))
            if error == False:
                return redirect(url_for('form'))
            else:
                return redirect(url_for('error'))

        elif request.form['submit_button'] == 'Volver a buscar':
            
            

            lista, lista_visa = buscar_recursos()
            
            return redirect(url_for('seleccion'))

    else:
       
        return 'Metodo no aceptado'
    

#PAGINA CON EL FORMULARIO PARA COMENZAR EL BARRIDO
@app.route('/barrido', methods= ['POST', 'GET'])
def form():
    if request.method == 'GET':
        
        return render_template('form.html')
    elif request.method == 'POST':
        
        global Nombre
       
        data = request.form.to_dict()   #Pedimos todos los datos del formulario y lo guardamos en data

        #Llamamos a la funcion que hace el barrido de frecuencia. Como argumentos vamos sacando los valores del formulario uno a uno y haciendo el casting para
        #que los pase como un entero y no como un string.
       
        error_formato = False

        try:
            volt_init = float(data.get('v_inicial'))
            volt_final = float(data.get('v_final'))
            paso = float(data.get('paso'))

            if (paso == 0):
                error_formato = True

            elif (paso < 0 and volt_init < volt_final):  

                error_formato = True

            print('exito')

        except:
            error_formato = True
            print('fallo')

        if( error_formato == False):

            Nombre = data.get('nombre') + 'csv'

            comenzar_procal(float(data.get('v_inicial')), float(data.get('v_final')), float(data.get('paso')))

            return redirect(url_for('cargando'))

        else:
            return redirect(url_for('error_valores'))

        
    else:
       
        return 'Metodo no aceptado'

#PAGINA EERROR VALORES
@app.route('/error_valores', methods= ['POST', 'GET'])
def error_valores():
    if request.method == 'GET':

        return render_template('error_valores.html')

    elif request.method == 'POST':
            
            if request.form['submit_button'] == 'Otra medida':
                return redirect(url_for('form'))
            
            elif request.form['submit_button'] == 'Cerrar y salir':
                cerrar()
                sys.exit()

            elif request.form['submit_button'] == 'Cambiar de instrumentos':
                cerrar()
                return redirect(url_for('buscar_instrumento'))
    else:
    
        return 'Metodo no aceptado'
        
           

#PAGINA EN CARGANDO
@app.route('/cargando', methods= ['POST', 'GET'])
def cargando():
    if request.method == 'GET':


        global lista_voltaje 
        global lista_generado
        
        while True: #Cambiar para que pare cuando llegue el evento de los hilos

            mensaje = q.get()

    

            if mensaje == 'Error':

                return redirect(url_for('error') )

            elif mensaje != None :
                


                lista_voltaje.append(mensaje[0])
                lista_generado.append(mensaje[1])
                
                
                q2.put('Continua')
                
            else:

                return redirect(url_for('resultado'))
        
       
    else:
       
        return 'Metodo invalido'
        
        
          

        
    

#PAGINA CON EL RESULTADO Y ELIGES SI SALIR O HACER OTRA MEDIDA
@app.route('/resultado', methods= ['POST', 'GET'])
def resultado():
    if request.method == 'GET':

        global lista_generado
        global lista_voltaje

        hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #creamos csv poner en funcion a parte
        dato = {'Fecha y hora': hora, 'Voltaje generado_[V]' : lista_generado, 'Voltaje medido_[V]': lista_voltaje }


        df = pd.DataFrame(dato, columns= ['Fecha y hora', 'Voltaje generado_[V]', 'Voltaje medido_[V]'])


        df.to_csv(Nombre, mode='a', index=False, header=True,sep=';',decimal=',')

        #creamos la grafica Poner en funcion a parte
        p = figure(
            title = 'Simple Example',
            x_axis_label='Voltaje medido [Hz]',
            y_axis_label='Voltaje generado [V]',
        )


        #Render glyph  
        p.line(lista_generado,  lista_voltaje)

        export_png(p, filename="static/plot.png")

        lista_voltaje.clear()
        lista_generado.clear()

        return render_template('resultado.html')
    
    elif request.method == 'POST':
        
        if request.form['submit_button'] == 'Otra medida':
            return redirect(url_for('form'))
        
        elif request.form['submit_button'] == 'Descargar CSV':
            return send_file(path_or_file=Nombre, as_attachment=True )
                        
        elif request.form['submit_button'] == 'Descargar Gráfica':
            return send_file(path_or_file='static\plot.png', as_attachment=True, )
                    
        elif request.form['submit_button'] == 'Cambiar de instrumentos':
            cerrar()
            return redirect(url_for('buscar_instrumento'))
        else:
                 return 'Error'
    else:
       
        return 'Metodo no aceptado'
    
#PAGINA EN CASO DE ERRROR
@app.route('/error', methods= ['POST', 'GET'])
def error():
    if request.method == 'GET':
        
        return render_template('error.html', Error = tipo_error)
    
    elif request.method == 'POST':
        
        if request.form['submit_button'] == 'Otra medida':
            return redirect(url_for('form'))
        
        elif request.form['submit_button'] == 'Cerrar y salir':
            cerrar()
            sys.exit()

        elif request.form['submit_button'] == 'Cambiar de instrumentos':
            cerrar()
            return redirect(url_for('buscar_instrumento'))
    else:
       
        return 'Metodo no aceptado'

#Hacemos una comprobación para ver si esta ejecutando este archivo como si fuera un archivo de ejecucion y no un modulo
#Le decimos que este archivo es el que va a rrancar mi aplicaicon
if __name__ == '__main__':
    app.run(debug = True, host='0.0.0.0')     #Poniendo dbug a true nos ahorra tener que estar matando el programa y volviendolo a ajecutar cada vez que cambiamos algo. 
                      

#Para encontrar la pagina en google tambien podemos usar localhost:5000
