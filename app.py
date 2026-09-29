import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from flask import Flask, render_template, redirect, url_for, request, flash, session

app = Flask(__name__)
app.secret_key = 'ecomarket_secret_key_2026'

DATA_FILE = 'datos.csv'

USERS = {
    "admin": "1234"
}

def obtener_datos():
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError("El archivo datos.csv no existe. Ejecuta generar_proyecto.py nuevamente.")
    
    df = pd.read_csv(DATA_FILE)
    # Si la columna 'edad' no existe previamente en datos.csv, la inicializamos por defecto
    if 'edad' not in df.columns:
        df['edad'] = 25
    return df

def guardar_datos(df):
    df.to_csv(DATA_FILE, index=False)

def generar_graficas():
    df = obtener_datos()
    os.makedirs('static/images', exist_ok=True)

    if df.empty:
        return

    # 1. Ventas por Ciudad
    ventas_por_ciudad = df.groupby('ciudad')['ventas'].sum().reset_index()
    plt.figure(figsize=(6, 4))
    plt.bar(ventas_por_ciudad['ciudad'], ventas_por_ciudad['ventas'], color='#2ecc71')
    plt.title('Ventas Totales por Ciudad')
    plt.xlabel('Ciudad')
    plt.ylabel('Ventas Totales ($)')
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig('static/images/ventas_ciudad.png')
    plt.close()

    # 2. Promedio de Ventas por Ciudad
    promedio_por_ciudad = df.groupby('ciudad')['ventas'].mean().reset_index()
    promedio_general = np.mean(df['ventas'])
    plt.figure(figsize=(6, 4))
    plt.axhline(y=promedio_general, color='#e74c3c', linestyle='--', label=f'Promedio General: ${promedio_general:.2f}')
    plt.bar(promedio_por_ciudad['ciudad'], promedio_por_ciudad['ventas'], color='#3498db', alpha=0.7)
    plt.title('Promedio de Ventas por Ciudad')
    plt.xlabel('Ciudad')
    plt.ylabel('Promedio ($)')
    plt.legend()
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig('static/images/promedio_ciudad.png')
    plt.close()

    # 3. Distribución del Monto de Ventas
    plt.figure(figsize=(6, 4))
    plt.hist(df['ventas'], bins=10, color='#9b59b6', edgecolor='black', alpha=0.8)
    plt.title('Distribución del Monto de Ventas')
    plt.xlabel('Monto ($)')
    plt.ylabel('Frecuencia')
    plt.tight_layout()
    plt.savefig('static/images/distribucion_ventas.png')
    plt.close()

    # 4. Ventas vs. Satisfacción
    plt.figure(figsize=(6, 4))
    plt.scatter(df['ventas'], df['satisfaccion'], color='#e67e22', alpha=0.7, edgecolors='k')
    plt.title('Relación Ventas vs. Satisfacción')
    plt.xlabel('Ventas ($)')
    plt.ylabel('Satisfacción (1 - 5)')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig('static/images/ventas_vs_satisfaccion.png')
    plt.close()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in USERS and USERS[username] == password:
            session['user'] = username
            return redirect(url_for('dashboard'))
        flash('Usuario o contraseña incorrectos')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in USERS:
            flash('El usuario ya existe')
        else:
            USERS[username] = password
            flash('Usuario registrado exitosamente. Inicia sesión.')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    generar_graficas()
    df = obtener_datos()
    
    registros = len(df)
    ventas_totales = np.sum(df['ventas']) if not df.empty else 0
    promedio_ventas = np.mean(df['ventas']) if not df.empty else 0
    promedio_edad = np.mean(df['edad']) if not df.empty else 0
    promedio_satisfaccion = np.mean(df['satisfaccion']) if not df.empty else 0
    
    metricas = {
        'registros': registros,
        'ventas_totales': f"${ventas_totales:,.2f}",
        'promedio_ventas': f"${promedio_ventas:,.2f}",
        'promedio_edad': f"{promedio_edad:.2f}",
        'satisfaccion': f"${promedio_satisfaccion:.2f}"
    }

    return render_template('dashboard.html', metricas=metricas)

@app.route('/productos')
def productos():
    if 'user' not in session:
        return redirect(url_for('login'))
    df = obtener_datos()
    lista_productos = df.to_dict(orient='records')
    return render_template('productos.html', productos=lista_productos)

@app.route('/producto/nuevo', methods=['GET', 'POST'])
def crear_producto():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        df = obtener_datos()
        nuevo_id = int(df['id'].max() + 1) if not df.empty else 1
        nuevo_registro = {
            'id': nuevo_id,
            'producto': request.form['producto'],
            'edad': int(request.form.get('edad', 25)),
            'ciudad': request.form['ciudad'],
            'ventas': float(request.form['ventas']),
            'satisfaccion': float(request.form['satisfaccion'])
        }
        df = pd.concat([df, pd.DataFrame([nuevo_registro])], ignore_index=True)
        guardar_datos(df)
        return redirect(url_for('dashboard'))
    return render_template('crear_producto.html')

@app.route('/producto/editar/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    df = obtener_datos()
    if request.method == 'POST':
        df.loc[df['id'] == id, 'producto'] = request.form['producto']
        if 'edad' in request.form:
            df.loc[df['id'] == id, 'edad'] = int(request.form['edad'])
        df.loc[df['id'] == id, 'ciudad'] = request.form['ciudad']
        df.loc[df['id'] == id, 'ventas'] = float(request.form['ventas'])
        df.loc[df['id'] == id, 'satisfaccion'] = float(request.form['satisfaccion'])
        guardar_datos(df)
        return redirect(url_for('productos'))
    
    prod = df[df['id'] == id].to_dict(orient='records')
    if not prod:
        return redirect(url_for('productos'))
    return render_template('editar_producto.html', producto=prod[0])

@app.route('/producto/eliminar/<int:id>')
def eliminar_producto(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    df = obtener_datos()
    df = df[df['id'] != id]
    guardar_datos(df)
    return redirect(url_for('productos'))

if __name__ == '__main__':
    app.run(debug=True)
