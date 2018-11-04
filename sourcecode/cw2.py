from flask import Flask, render_template, url_for, request, redirect, abort, json
import os
app = Flask(__name__)

roomList=[]

@app.route('/', methods=['POST','GET'])
def enterQuiz():
    if request.method == 'POST':
        print request.form
        roomCode = request.form['roomCode']
        if roomCode == '1657':
            #https://stackoverflow.com/questions/17057191/redirect-while-passing-arguments
            return redirect(url_for('.quiz', roomCode=roomCode))
    return render_template('enter.html')

@app.route('/admin', methods=['POST','GET'])
#Dashboard for the admin that runs the quiz
def host():
    if request.method =='POST':
        print request.form
        roomCode = request.form['roomCode']
        return redirect(url_for('.lobby', roomCode=roomCode))
    return render_template('adminDash.html')

@app.route('/lobby')
def lobby():
    roomCode = request.args['roomCode']
    return render_template('lobby.html', roomCode=roomCode)

@app.route('/quiz')
#This is the mobile view of the questions
def quiz():
    roomCode = request.args['roomCode']
    return render_template("quiz.html", room=roomCode)
