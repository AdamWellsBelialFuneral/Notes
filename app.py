from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import secrets

app = Flask(__name__)

app.secret_key = secrets.getenv("SECRET_KEY", secrets.token(16))

def init_db():
    conn = sqlite3.connect('notes.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            user_id INTEGER
        );
    ''')
    conn.execute(
        '''
            CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
        '''
    )
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    init_db()

    if 'user_id' not in session:
        return redirect('/login')

    user_id = session.get('user_id')

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        with sqlite3.connect('notes.db') as conn:
            conn.execute('INSERT INTO notes (title, content, user_id) VALUES (?, ?, ?)', (title, content, user_id))
        return redirect('/')
    
    with sqlite3.connect('notes.db') as conn:
        notes = conn.execute('SELECT * FROM notes where user_id = ?', (user_id,)).fetchall()
    return render_template('index.html', notes=notes)

@app.route('/delete/<int:note_id>', methods=['POST'])
def delete(note_id):
    with sqlite3.connect('notes.db') as conn:
        conn.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    return redirect('/')

@app.route('/edit/<int:note_id>', methods=['GET', 'POST'])
def edit(note_id):
    with sqlite3.connect('notes.db') as conn:
        if request.method == 'POST':
            new_title = request.form['title']
            new_content = request.form['content']
            conn.execute('UPDATE notes SET title = ?, content = ? WHERE id = ?', (new_title, new_content, note_id))
            return redirect('/')
        else:
            note = conn.execute('SELECT * FROM notes WHERE id = ?', (note_id,)).fetchone()
            return render_template('edit.html', note=note)

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)

        conn = sqlite3.connect('notes.db')
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_pw))
            conn.commit()
        except sqlite3.IntegrityError:
            return 'User already exists!'
        finally:
            conn.close()

        return redirect('/login/')
    return render_template('register.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect('notes.db') as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect('/')
        else:
            return 'Usuário ou senha incorretos!'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
