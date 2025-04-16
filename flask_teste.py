from flask import Flask, request, jsonify
from flask_mysqldb import MySQL

app = Flask(__name__)

# configurações MYSQL
app.config['MYSQL_HOST'] = '--------' #Coloque seu hostname
app.config['MYSQL_USER'] = 'root'  #coloque seu username
app.config['MYSQL_PASSWORD'] = '1234567'  #coloque sua senha
app.config['MYSQL_DB'] = 'estudante_db' #coloque seu banco de dados que será usado

mysql = MySQL(app)

#MétodoPOST
@app.route('/registro', methods=['POST'])
def register_student():
    data = request.get_json()
    nome = data.get('nome')
    email = data.get('email')
    matrícula = data.get('matrícula')
    senha = data.get('senha')

    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO estudante (nome, email, matrícula, senha) VALUES (%s, %s, %s, %s)", 
                   (nome, email, matrícula, senha))
    mysql.connection.commit()
    cursor.close()

    return jsonify({'mensagem': 'estudante registrado com sucesso!'}), 201

#MétodoGET
@app.route('/estudante', methods=['GET'])
def list_students():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM estudante_db.estudante")
    results = cursor.fetchall()
    cursor.close()

    students = []
    for row in results:
        students.append({
            'id': row[0],
            'nome': row[1],
            'email': row[2],
            'matrícula': row[3],
            'senha': row[4]
        })

    return jsonify(students), 200

if __name__ == '__main__':
    app.run(debug=True)