#!/usr/bin/env python3

from flask import Flask, render_template, request, make_response, redirect
from datetime import datetime
from conf import VERSION
import db
import jwt
import asyncio
import json
import ollama


app = Flask(__name__)

JWT_SECRET = "jwtSecret123123123"

ACCOUNTS = {}

EVENT_LOOP = None

TASKS = []

def init():
    global ACCOUNTS, EVENT_LOOP
    db.init()
    EVENT_LOOP = asyncio.new_event_loop()
    asyncio.set_event_loop(EVENT_LOOP)
    with open('accounts.json') as f:
        ACCOUNTS = json.load(f)


def login(username, password):
    if ACCOUNTS.get(username.strip()) is not None:
        if password.strip() == ACCOUNTS[username.strip()]['password']:
            return jwt.encode({"email": username.strip()}, JWT_SECRET, algorithm="HS256")

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        output = login(username, password)
        if output:
            resp = make_response(redirect('/mailbox', code=301))
            resp.set_cookie('ph_session', output)
            return resp
        else:
            return render_template('index.html', error="Invalid credentials provided")
    return render_template('index.html')

@app.route("/lost-password", methods=['GET', 'POST'])
def lost():
    if request.method == "GET":
        return render_template('lost.html')
    email = request.form.get('email')
    question1 = request.form.get('question1')
    question2 = request.form.get('question2')
    question3 = request.form.get('question3')
    new_password = request.form.get('new_password')
    if new_password is None:
        return render_template('lost.html', error='No new password supplied.')
    if email is None or email not in ACCOUNTS.keys():
        return render_template('lost.html', error='Invalid email address specified.')
    questions = ACCOUNTS.get(email).get('questions')
    if len(questions) != 3 or question1.lower() != questions[0].lower() \
       or question2.lower() != questions[1].lower() \
           or question3.lower() != questions[2].lower():
        print(question1, question2, question3, questions)
        return render_template('lost.html', error='Invalid security questions answers.')
    ACCOUNTS[email]['password'] = new_password
    return redirect("/", 301)

def ollama_answer(orig_email, model):
    message = {'role': 'user', 'content': f"EMAIL : <{orig_email['from']}> OBJECT : {orig_email['object']} {orig_email['contents']}"}
    response = ollama.chat(model=model, messages=[message])

    email = create_mail(orig_email['to'], orig_email['from'], 'Re: '+orig_email['object'], response['message']['content'].replace('\n', '<br/>'))
    db.add(email)
    print('ADDED NEW MAIL', email)
    return response

def callback(context):
    print("CALLBACK CALLED", context)
    return

async def async_answer(email, model):
    global TASKS
    print('BOT WILL ANSWER', email)
    task = EVENT_LOOP.run_in_executor(None, ollama_answer, email, model)
    task.add_done_callback(callback)
    TASKS.append(task)
    print(TASKS)

def create_mail(_from, _to, _object, contents):
    return {
        "from": _from,
        "to": _to,
        "object": _object,
        "contents": contents,
    }

@app.route("/read/<id>")
def read(id):
    db.read(id)
    print(id+" has been read")
    return '', 204

@app.route("/delete/<id>")
def delete(id):
    db.delete(id)
    print(id+" has been deleted")
    return '', 204

@app.route("/updates")
def updates():
    ph_session = request.cookies.get('ph_session')
    if ph_session is not None:
        try:
            user = jwt.decode(ph_session, JWT_SECRET, algorithms=['HS256'])
            emails = db.get_mailbox(_to=user['email'])
            if emails:
                return emails
        except Exception as e:
            print(e)
    return '', 204

@app.route("/mailbox", methods=[ 'GET', 'POST' ])
def mailbox():
    ph_session = request.cookies.get('ph_session')
    user = None
    if ph_session is not None:
        try:
            user = jwt.decode(ph_session, JWT_SECRET, algorithms=['HS256'])
        except Exception as e:
            print(e)
            return redirect('/', 301)
    else:
        return redirect('/', 301)
    if request.method == 'GET':
        print(db.get_mailbox(_to=user['email']))
        return render_template('mailbox.html',
                               inbox=db.get_mailbox(_to=user['email']),
                               sent=db.get_mailbox(_from=user['email']),
                               user=user,
                               version=VERSION)
    
    msg_from = request.form.get('from')
    msg_to = request.form.get('to')
    msg_object = request.form.get('object')
    msg_contents = request.form.get('contents')
    if msg_from and msg_to and msg_object and msg_contents:
        email = create_mail(msg_from, msg_to, msg_object, msg_contents)
        db.add(email)
        if msg_to not in ACCOUNTS.keys(): # If we don't know the email address
            print('mail in bouncing')
            db.add(create_mail(msg_to, user['email'], 'Undelivered Mail Returned to Sender', 'This is the mail system at photonmail. <br/>Your email could not be delivered, make sure you entered a valid recipient e-mail address! Thanks!<br/>The photonmail team'))

        else:
            print(msg_to, ACCOUNTS)
            model = ACCOUNTS[msg_to].get('model')
            if model is not None:
                asyncio.run(async_answer(email, model))
#                ollama_answer(email, model) # synchronous, for debug
    return render_template('mailbox.html',
                           inbox=db.get_mailbox(_to=user['email']),
                           sent=db.get_mailbox(_from=user['email']),
                           user=user,
                           version=VERSION)

init()
app.run(host='0.0.0.0', port=8002)
