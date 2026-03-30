from flask import Flask, render_template, url_for, redirect, request, session
from flask_socketio import SocketIO, emit, join_room

import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = "very secret key"

def get():
    return sqlite3.connect('data.db')

def init_db():
    db = get()
    cursor = db.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    ''')
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chats(
        user_id INTEGER,
        name TEXT,
        room TEXT,
        post TEXT
    )
    """)
    
    db.commit()
    db.close()

socketio = SocketIO(app,async_mode='threading')

@app.route("/",methods=["GET","POST"])
def login():
  init_db()
  db = get()
  cur = db.cursor()
  if request.method == "POST":
    username = request.form.get("username")
    password = request.form.get("password")
    room = request.form.get("room")
    cur.execute("SELECT *  FROM users WHERE username=? AND password=?",(username,password))
    user = cur.fetchall()
    db.close()
    if user == []:
      return f'<h1>invalid credentials</h1><a href="{url_for("login")}">try again</a>'
    session.clear()
    single_user = user[0]
    session["user_id"] = single_user[0]
    session["room"] = room
    return redirect(url_for("chat",room=room))
  else:
    return render_template("login.html")

@app.route("/add_account",methods=["GET","POST"])
def add_account():
  db = get()
  cur = db.cursor()
  if request.method == "POST":
    username = request.form.get("username")
    password = request.form.get("password")
    cur.execute("INSERT INTO users(username,password) VALUES(?,?)",(username,password))
    db.commit()
    db.close()
    return redirect(url_for("login"))
  else:
    return render_template("add_account.html")
    
        
@app.route("/chat/<room>")
def chat(room):
    user_id = session.get("user_id")
    db = get()
    cur = db.cursor()
    cur.execute("SELECT * FROM chats WHERE room=?",(room,))
    chats = cur.fetchall()
    return render_template("chat.html",room=room,user_id=user_id,chats=chats)
@socketio.on("join_room")
def handle_join_room(data):
    room = data["room"]
    join_room(room)
    print("joined room:"+room)
    
@socketio.on("send_message")
def sendMessage(data):
    db = get()
    cur = db.cursor()
    
    user_id = data["user_id"]
    msg = data["message"]
    room = data["room"]
    
    cur.execute("SELECT username FROM users WHERE user_id=?",(user_id,))
    
    name = cur.fetchone()[0]
    
    cur.execute("INSERT INTO chats(user_id,name,room,post) VALUES(?,?,?,?)",(user_id,name,room,msg))
    
    emit("receive_message",{
        "user_id": user_id,
        "name": name,
        "message": msg
    },room=room)
    
    db.commit()
    db.close()
    
if __name__ == "__main__":
    socketio.run(app)