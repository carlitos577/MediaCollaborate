import os
from flask import Flask, request, send_from_directory, render_template, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, join_room, emit

#--------------------------------------------------
#--------------------------------------------------

#--------------------------------------------------
#--------------------------------------------------

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './Archivos_multimedia'

socketio = SocketIO(app)

ruta = './Archivos_multimedia'  # Cambia esto a la ruta de tu carpeta

def listar_archivos(ruta):
    return os.listdir(ruta)

archivos = listar_archivos(ruta)

for archivo in archivos:
    print(archivo)
#--------------------------------------------------
#--------------------------------------------------
# Diccionario para almacenar archivos por sala
rooms_files = {}
#--------------------------------------------------
#--------------------------------------------------
@app.route('/listar_archivos', methods=['GET'])
def listar_archivos():
    archivos = os.listdir(app.config['UPLOAD_FOLDER'])
    return {'archivos': archivos}
#--------------------------------------------------
#--------------------------------------------------
# Función para verificar si el usuario está autorizado
def is_user_authorized(username, password):
    with open('usuarios_autorizados.txt', 'r') as f:
        authorized_users = [line.strip().split(':') for line in f]
    return any(user[0] == username and user[1] == password for user in authorized_users)
#--------------------------------------------------
#--------------------------------------------------
@app.route('/emisor', methods=['GET'])
def emisor():
    username = request.args.get('username')
    password = request.args.get('password')
    
    if is_user_authorized(username, password):
        return render_template('emisor.html')
    else:
        return redirect(url_for('receptor'))

#--------------------------------------------------
#--------------------------------------------------

#--------------------------------------------------
#--------------------------------------------------
@app.route('/')
def receptor():
    return render_template('receptor.html') # Cargar receptor.html por defecto
#--------------------------------------------------
#--------------------------------------------------

#--------------------------------------------------
#--------------------------------------------------
@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST' and request.files['archivo']:
        f = request.files['archivo']
        filename = secure_filename(f.filename)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename
    else:
        return 'Se ha producido un error!', 400
#--------------------------------------------------
#--------------------------------------------------

#--------------------------------------------------
#--------------------------------------------------
@app.route('/media/<filename>')
def media(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
#--------------------------------------------------
#--------------------------------------------------

#--------------------------------------------------
#--------------------------------------------------
@socketio.on('join')
def join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    emit('message', {'text': f'Bienvenido {username} a la sala {room}'}, room=room)

    print('estoy en el inicio del join')
    print(rooms_files)
    # Cuando un receptor se une a la sala, le enviamos el archivo más reciente (si existe)
    if room in rooms_files:
        latest_file = rooms_files[room]
        print('aqui es el join')
        print(latest_file)
        emit('media', {'filename': [latest_file]}, room=request.sid)
        if latest_file:
            emit('media', {'filename': [latest_file]}, room=request.sid)
    print(rooms_files)
#--------------------------------------------------
#--------------------------------------------------

#--------------------------------------------------
#--------------------------------------------------
@socketio.on('upload')
def upload(data):
    filename = data['filename']
    room = data['room']
    
    rooms_files[room] = []
    # Almacenar el archivo en el historial de la sala
    if room not in rooms_files:
        rooms_files[room] = [filename]
    else:
        # Si ya existe un archivo en la sala, sobrescribe el nombre del archivo
        rooms_files[room].append(filename)

    # Actualizar el archivo más reciente
    latest_file = filename

    print('estoy en donde se envia')
    print(rooms_files)
    # Emitir el archivo a todos los receptores en la sala
    emit('media', {'filename': [latest_file]}, room=room)
#--------------------------------------------------
#--------------------------------------------------

#--------------------------------------------------
#--------------------------------------------------
@app.route('/eliminar_archivo/<filename>', methods=['DELETE'])
def eliminar_archivo(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.remove(file_path)
        return 'Archivo eliminado correctamente', 200
    except Exception as e:
        return f'Error al eliminar el archivo: {str(e)}', 500

#--------------------------------------------------
#--------------------------------------------------

#--------------------------------------------------
#--------------------------------------------------
@app.route('/cambiar_archivo/<filename>', methods=['POST'])
def cambiar_archivo(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.remove(file_path)
        
        new_file = request.files['archivo']
        new_filename = secure_filename(new_file.filename)
        new_file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))

        return 'Archivo cambiado correctamente', 200
    except Exception as e:
        return f'Error al cambiar el archivo: {str(e)}', 500

#--------------------------------------------------
#--------------------------------------------------
@app.route('/guardar_archivos_seleccionados', methods=['POST'])
def guardar_archivos_seleccionados():
    try:
        data = request.json
        archivos_seleccionados = data.get('archivos', [])

        # Actualiza la variable rooms_files para la sala 'Media'
        room = 'Media'
        rooms_files[room] = []
        if room not in rooms_files:
            rooms_files[room] = archivos_seleccionados
        else:
            # Asegúrate de que rooms_files[room] sea una lista antes de extenderla
            if not isinstance(rooms_files[room], list):
                rooms_files[room] = []

            rooms_files[room].extend(archivos_seleccionados)
        print(rooms_files)
        return jsonify({'success': True, 'message': 'Archivos guardados correctamente'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
#--------------------------------------------------
#--------------------------------------------------

if __name__ == '__main__':
    socketio.run(app, debug=True)
