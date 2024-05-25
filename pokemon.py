import sqlite3
import json
import logging
import os

from datetime import timedelta
from flask import Flask, jsonify, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask("pokemon")
app.secret_key = 'supersecretkey'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=7)

#Criar tabelas
def create_database():
    conn = sqlite3.connect('pokemon.db')
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tipo (
                        Nome varchar(50) PRIMARY KEY
                    );
                  """)
    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS pokemon (
                        Id INTEGER PRIMARY KEY,
                        Nome varchar(50) NOT NULL,
                        Tipo1 varchar(50) NOT NULL,
                        Tipo2 varchar(50),
                        Vida INTEGER,
                        Ataque INTEGER,
                        Defesa INTEGER,
                        AtaqueEspecial INTEGER,
                        DefesaEspecial INTEGER,
                        Velocidade INTEGER,
                        FOREIGN KEY (Tipo1) REFERENCES tipo (Nome),
                        FOREIGN KEY (Tipo2) REFERENCES tipo (Nome)
                        );
                  """)
    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        username TEXT PRIMARY KEY,
                        password TEXT NOT NULL,
                        role TEXT NOT NULL
                    );
                  """)
    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS team (
                        username TEXT,
                        pokemon_id INTEGER,
                        apelido TEXT,
                        FOREIGN KEY (username) REFERENCES users(username),
                        FOREIGN KEY (pokemon_id) REFERENCES pokemon(Id),
                        PRIMARY KEY (username, pokemon_id)
                    );
                  """)             
    conn.commit()
    conn.close()

#Popular tabela Tipo
def populate_tipo_table():
    conn = sqlite3.connect('pokemon.db')
    cursor = conn.cursor()
    tipos = [
        "Normal", "Lutador", "Voador", "Venenoso", "Terra", "Rocha", "Inseto", "Fantasma",
        "Metálico", "Fogo", "Água", "Grama", "Elétrico", "Psíquico", "Gelo", "Dragão", "Noturno", "Fada"
    ]
    for tipo in tipos:
        cursor.execute("INSERT OR IGNORE INTO tipo (Nome) VALUES (?)", (tipo,))
    conn.commit()
    conn.close()

#Popular tabela Pokemons
def populate_database():
    conn = sqlite3.connect('pokemon.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM pokemon")
    count = cursor.fetchone()[0]

    if count == 0:
        with open('pokemons.json', 'r', encoding='utf-8') as file:
            pokemon_data = json.load(file)
            for pokemon in pokemon_data:
                tipos = pokemon['Tipo']
                tipo1 = tipos[0]
                tipo2 = tipos[1] if len(tipos) > 1 else None 

                cursor.execute("""
                                INSERT INTO pokemon (Nome, Tipo1, Tipo2, Vida, Ataque, Defesa, AtaqueEspecial, DefesaEspecial, Velocidade)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                                """, (
                                    pokemon['Nome'],
                                    tipo1,
                                    tipo2,
                                    pokemon['base']['Vida'],
                                    pokemon['base']['Ataque'],
                                    pokemon['base']['Defesa'],
                                    pokemon['base']['AtaqueEspecial'],
                                    pokemon['base']['DefesaEspecial'],
                                    pokemon['base']['Velocidade']
                                ))
            conn.commit()
    conn.close()

#Popular tabela users
def populate_users_table():
    conn = sqlite3.connect('pokemon.db')
    cursor = conn.cursor()
    users = [
        ('admin', generate_password_hash('admin'), 'administrador'),
        ('comum', generate_password_hash('comum'), 'comum')
    ]
    for user in users:
        cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", user)
    conn.commit()
    conn.close()

#Método de conexão
def get_connection():
    conn = sqlite3.connect('pokemon.db')
    return conn

# Verificação de login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

#Endpoints de rota
@app.route('/')
def index():
    return redirect('/static/login.html')

#Endpoint de Login
@app.route('/login', methods=['POST'])
def login():
    try:
        username = request.json['username']
        password = request.json['password']

        conn = sqlite3.connect('pokemon.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user[1], password):
            role = user[2]
            session['username'] = username
            session['role'] = role
            return jsonify({'role': role}), 200
        else:
            return jsonify({'error': 'Nome de usuário ou senha inválidos'}), 401
    except Exception as e:
        return jsonify({'error': 'Erro ao fazer login'}), 500
        
# Endpoint para logout
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('index'))

# Checar Sessão
@app.route('/check-session', methods=['GET'])
def check_session():
    if 'username' not in session:
        return '', 401
    return '', 200

# Métodos dos endpoints da API    
class PokemonDB:
    def __init__(self, conn):
        self.conn = conn

    def get_connection(self):
        return self.conn

    def insert_pokemon(self, pokemon_data):
        insert_pokemon_sql = """
                            INSERT INTO pokemon (Nome, Tipo1, Tipo2, Vida, Ataque, Defesa, AtaqueEspecial, DefesaEspecial, Velocidade)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                            """
        cursor = self.conn.cursor()
        for pokemon in pokemon_data:
            tipo1 = pokemon.get('Tipo1')
            tipo2 = pokemon.get('Tipo2')

            if tipo2 == "":
                tipo2 = None

            cursor.execute(insert_pokemon_sql, (
                pokemon['Nome'],
                tipo1,
                tipo2,
                pokemon['base']['Vida'],
                pokemon['base']['Ataque'],
                pokemon['base']['Defesa'],
                pokemon['base']['AtaqueEspecial'],
                pokemon['base']['DefesaEspecial'],
                pokemon['base']['Velocidade']
            ))
        self.conn.commit()
        self.conn.close()
        pokemon_id = cursor.lastrowid
        return pokemon_id

    def get_pokemon_by_id(self, pokemon_id):
        select_pokemon_sql = "SELECT * FROM pokemon WHERE id = ?"
        cursor = self.conn.cursor()
        cursor.execute(select_pokemon_sql, (pokemon_id,))
        pokemon = cursor.fetchone()
        self.conn.close()
        return pokemon

    def update_pokemon(self, pokemon_id, pokemon_data):
        try:
            update_pokemon_sql = """
                                UPDATE pokemon
                                SET Vida=?, Ataque=?, Defesa=?,
                                AtaqueEspecial=?, DefesaEspecial=?, Velocidade=?
                                WHERE Id=?;
                                """
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM pokemon WHERE Id = ?", (pokemon_id,))
            pokemon = cursor.fetchone()
            if not pokemon:
                return False
            
            base_data = pokemon_data.get('base', {})
            
            vida = base_data.get('Vida', pokemon[4]) if base_data.get('Vida') != "" else pokemon[4]
            ataque = base_data.get('Ataque', pokemon[5]) if base_data.get('Ataque') != "" else pokemon[5]
            defesa = base_data.get('Defesa', pokemon[6]) if base_data.get('Defesa') != "" else pokemon[6]
            ataque_especial = base_data.get('AtaqueEspecial', pokemon[7]) if base_data.get('AtaqueEspecial') != "" else pokemon[7]
            defesa_especial = base_data.get('DefesaEspecial', pokemon[8]) if base_data.get('DefesaEspecial') != "" else pokemon[8]
            velocidade = base_data.get('Velocidade', pokemon[9]) if base_data.get('Velocidade') != "" else pokemon[9]
            
            update_values = [
                vida,
                ataque,
                defesa,
                ataque_especial,
                defesa_especial,
                velocidade,
                pokemon_id
            ]

            cursor.execute(update_pokemon_sql, update_values)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logging.error(f"Error: {e}")
            return False


    def delete_pokemon(self, pokemon_id):
        try:
            delete_pokemon_sql = "DELETE FROM pokemon WHERE id =?"
            cursor = self.conn.cursor()
            cursor.execute(delete_pokemon_sql, (pokemon_id,))
            rows_affected = cursor.rowcount
            is_any_rows_affected = rows_affected > 0
            self.conn.commit()
            return is_any_rows_affected
        except sqlite3.Error as e:
            logging.error(f"Error deleting Pokemon: {e}")
            self.conn.rollback()
            return False
        finally:
            cursor.close()

# Métodos do endpoint de imagens
class PokemonImage:
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

    @staticmethod
    @app.route('/pokemon-image', methods=['POST'])
    def upload_pokemon_image():
        try:
            image_file = request.files['imagem']
            pokemon_id = request.form.get('pokemon_id')

            if not (image_file and pokemon_id):
                return jsonify({'error': 'Missing image file or pokemon_id'}), 400

            upload_folder = os.path.join(app.root_path, 'static', 'img')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            filename = f"{pokemon_id}.png"
            image_path = os.path.join(upload_folder, filename)
            image_file.save(image_path)

            return jsonify({'success': True}), 201
        except Exception as e:
            logging.error(f"Error uploading image: {e}")
            return jsonify({'error': 'Internal Server Error'}), 500

# Endpoint para registro de novos usuários
@app.route('/registrar', methods=['POST'])
def register():
    try:
        username = request.json['username']
        password = request.json['password']

        conn = sqlite3.connect('pokemon.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            return jsonify({'message': 'Usuário já existe'}), 400

        hashed_password = generate_password_hash(password)

        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_password, 'comum'))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Usuário criado com sucesso'}), 201
    except Exception as e:
        return jsonify({'Erro': str(e)}), 500

# Endpoints do usuário admin:
# Endpoint para adicionar pokemons novos
@app.route('/pokemon', methods=['POST'])
@login_required
def add_pokemon():
    try:
        novo_pokemon = request.json
        if 'Nome' not in novo_pokemon or 'Tipo1' not in novo_pokemon or 'base' not in novo_pokemon:
            return '', 400
        conn = get_connection()

        tipo1 = novo_pokemon.get('Tipo1')
        tipo2 = novo_pokemon.get('Tipo2')

        for tipo in (tipo1, tipo2):
            if tipo:
                cursor = conn.cursor()
                cursor.execute("SELECT Nome FROM tipo WHERE Nome=?", (tipo,))
                tipo_result = cursor.fetchone()
                if not tipo_result:
                    return '', 400

        pokemon_id = PokemonDB(conn).insert_pokemon([novo_pokemon])
        return jsonify({'pokemon_id': pokemon_id}), 201
    except sqlite3.Error as e:
        logging.error(f"Erro: {e}")
        return '', 500

# Endpoint para buscar pokemons
@app.route('/pokemon/<int:pokemon_id>', methods=['GET'])
@login_required
def get_pokemon_por_id(pokemon_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pokemon WHERE Id = ?", (pokemon_id,))
        pokemon_data = cursor.fetchone()
        if pokemon_data:
            pokemon = {
                'id': pokemon_data[0],
                'nome': pokemon_data[1],
                'tipo1': pokemon_data[2],
                'tipo2': pokemon_data[3],
                'base': {
                    'vida': pokemon_data[4],
                    'ataque': pokemon_data[5],
                    'defesa': pokemon_data[6],
                    'ataqueEspecial': pokemon_data[7],
                    'defesaEspecial': pokemon_data[8],
                    'velocidade': pokemon_data[9]
                }
            }
            if pokemon['tipo2'] is None:
                del pokemon['tipo2']
            return jsonify({'pokemon': pokemon})
        else:
            return jsonify({'mensagem': 'Pokémon não encontrado'}), 404
    except sqlite3.Error as e:
        logging.error(f"Error: {e}")
        return jsonify({'mensagem': 'Erro ao obter Pokémon'}), 500

# Endpoint para atualizar stats dos pokemons
@app.route('/pokemon/<int:pokemon_id>', methods=['PUT'])
@login_required
def update_pokemon_by_id(pokemon_id):
    try:
        pokemon_data = request.json
        conn = get_connection()
        pokemon_db = PokemonDB(conn)
        if pokemon_db.update_pokemon(pokemon_id, pokemon_data):
            return '', 200
        else:
            return '', 404
    except sqlite3.Error as e:
        logging.error(f"Error: {e}")
        return '', 500 

# Endpoint para deletar um pokemon do banco de dados
@app.route('/pokemon/<int:pokemon_id>', methods=['DELETE'])
@login_required
def delete_pokemon(pokemon_id):
    conn = get_connection()
    deleted_pokemon = PokemonDB(conn).delete_pokemon(pokemon_id)
    if deleted_pokemon:
        conn.commit()
        return '', 200
    else:
        return '', 404

# Endpoints do usuário comum:
# Endpoint para adicionar Pokémon ao time do usuário comum
@app.route('/team/add', methods=['POST'])
@login_required
def add_pokemon_to_team():
    try:
        username = session['username']
        pokemon_id = request.json['pokemon_id']
        apelido = request.json.get('apelido', '')

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM team WHERE username = ? AND pokemon_id = ?", (username, pokemon_id))
        if cursor.fetchone():
            return jsonify({'message': 'Pokémon já está no time'}), 400

        cursor.execute("SELECT COUNT(*) FROM team WHERE username = ?", (username,))
        if cursor.fetchone()[0] >= 6:
            return jsonify({'message': 'O time já tem 6 Pokémon'}), 400

        cursor.execute("INSERT INTO team (username, pokemon_id, apelido) VALUES (?, ?, ?)", (username, pokemon_id, apelido))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Pokémon adicionado ao time'}), 201
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({'message': 'Erro ao adicionar Pokémon ao time'}), 500

# Endpoint para remover Pokémon do time do usuário comum
@app.route('/team/remove', methods=['DELETE'])
@login_required
def remove_pokemon_from_team():
    try:
        username = session['username']
        pokemon_id = request.json['pokemon_id']

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM team WHERE username = ? AND pokemon_id = ?", (username, pokemon_id))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Pokémon removido do time'}), 200
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({'message': 'Erro ao remover Pokémon do time'}), 500

# Endpoint para atualizar apelido de um Pokémon no time do usuário comum
@app.route('/team/update', methods=['POST'])
@login_required
def update_pokemon_nickname():
    try:
        username = session['username']
        pokemon_id = request.json['pokemon_id']
        apelido = request.json['apelido']

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("UPDATE team SET apelido = ? WHERE username = ? AND pokemon_id = ?", (apelido, username, pokemon_id))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Apelido atualizado'}), 200
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({'message': 'Erro ao atualizar apelido'}), 500

# Endpoint para visualizar o time do usuário comum
@app.route('/team', methods=['GET'])
@login_required
def view_team():
    try:
        username = session['username']

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT pokemon.Id, pokemon.Nome, pokemon.Tipo1, pokemon.Tipo2, pokemon.Vida, pokemon.Ataque, 
                   pokemon.Defesa, pokemon.AtaqueEspecial, pokemon.DefesaEspecial, pokemon.Velocidade, team.apelido 
            FROM team 
            JOIN pokemon ON team.pokemon_id = pokemon.Id 
            WHERE team.username = ?
        """, (username,))

        team = cursor.fetchall()
        conn.close()

        team_data = [
            {
                'id': pokemon[0],
                'nome': pokemon[1],
                'tipo1': pokemon[2],
                'tipo2': pokemon[3],
                'base': {
                    'vida': pokemon[4],
                    'ataque': pokemon[5],
                    'defesa': pokemon[6],
                    'ataqueEspecial': pokemon[7],
                    'defesaEspecial': pokemon[8],
                    'velocidade': pokemon[9]
                },
                'apelido': pokemon[10]
            }
            for pokemon in team
        ]

        return jsonify({'team': team_data}), 200
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({'message': 'Erro ao obter time'}), 500

if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR)
    create_database()
    populate_tipo_table()
    populate_database()
    populate_users_table()
    app.run(debug=True)