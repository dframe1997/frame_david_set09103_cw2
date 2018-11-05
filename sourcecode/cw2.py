from flask import Flask, render_template, url_for, request, redirect, abort, json, flash
import os
app = Flask(__name__)
app.secret_key = 'sandwich'
roomList=[]

class Room:
    def __init__(self, roomCode):
        self.roomCode = roomCode
        self.users = []

@app.route('/', methods=['POST','GET'])
def enterQuiz():
    if request.method == 'POST':
        print request.form
        roomCode = request.form['roomCode']
        username = request.form['username']
        if any(room for room in roomList if room.roomCode == roomCode):
            #https://stackoverflow.com/questions/17057191/redirect-while-passing-arguments
            return redirect(url_for('.quizInput', roomCode=roomCode, username=username))
        else:
            flash('Room does not exist, please try again')
            return redirect(url_for('.enterQuiz'))
    return render_template('enter.html')

@app.route('/admin', methods=['POST','GET'])
#Dashboard for the admin that runs the quiz
def admin():
    if request.method =='POST':
        print request.form
        roomCode = request.form['roomCode']
        return redirect(url_for('.lobby', roomCode=roomCode))
    return render_template('adminDash.html')

@app.route('/lobby')
def lobby():
    roomCode = request.args['roomCode']
    roomList.append(Room(roomCode))
    return render_template('lobby.html', room=next((room for room in roomList if room.roomCode == roomCode), None), update='true')

@app.route('/quiz-input')
#This is the mobile view of the questions
def quizInput():
    roomCode = request.args['roomCode']
    username = request.args['username']
    roomIndex = next((room for room in roomList if room.roomCode == roomCode), None)
    if roomIndex != None:
        roomIndex = roomList.index(roomIndex)
        if username not in roomList[roomIndex].users:
            roomList[roomIndex].users.append(username)
    return render_template("quiz.html", room=roomCode, view='mobile')

@app.route('/quiz-display')
#This is the desktop view of the questions
def quizDisplay():
    roomCode = request.args['roomCode']
    return render_template("quiz.html", room=roomCode, view='desktop')

@app.route('/clearusers')
def clearUsers():
    roomCode = request.args['roomCode']
    roomIndex = next((room for room in roomList if room.roomCode == roomCode), None)
    if roomIndex != None:
        roomIndex = roomList.index(roomIndex)
        roomList[roomIndex].users = []
    return redirect(url_for('.lobby', roomCode=roomCode))

@app.route('/removeroom')
def removeRoom():
    roomCode = request.args['roomCode']
    roomIndex = next((room for room in roomList if room.roomCode == roomCode), None)
    if roomIndex != None:
        roomIndex = roomList.index(roomIndex)
        del roomList[roomIndex]
    return redirect(url_for('.admin'))
    
