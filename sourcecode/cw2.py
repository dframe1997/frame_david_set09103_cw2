from flask import Flask, render_template, url_for, request, redirect, abort, json, flash
import os, time, pickle
app = Flask(__name__)
app.secret_key = 'sandwich'
roomList=[]
timer = 30;

class Question:
    def __init__(self, questionText, answers, correctAnswer, responders):
        self.questionText = questionText
        self.answers = answers
        self.correctAnswer = correctAnswer
        self.responders = responders

class User:
    def __init__(self, name, score):
        self.name = name
        self.score = score

class Room():  
    def __init__(self, roomCode, users, questions, currentQuestion, status, results):
        self.roomCode = roomCode
        self.users = users
        self.questions = questions
        self.currentQuestion = currentQuestion
        self.status = status
        self.results = results

with open('roomData.pkl', 'wb') as data:
    pickle.dump(roomList, data)


with open('roomData.pkl', 'rb') as data:
    roomList = pickle.load(data)

print(roomList)

questionComplete = 'false'

@app.route('/')
def root():
    return redirect(url_for('.enterQuiz'))

@app.route('/enter', methods=['POST','GET'])
def enterQuiz():
    #Entry point into the quiz
    if request.method == 'POST':
        print request.form
        roomCode = request.form['roomCode']
        username = request.form['username']
        if any(room for room in roomList if room.roomCode == roomCode):
            return redirect(url_for('.waiting', roomCode=roomCode, username=username, waitingLocation="lobby"))
        else:
            flash('Room does not exist, please try again')
            return redirect(url_for('.enterQuiz'))
    return render_template('enter.html')

@app.route('/waiting')
def waiting():
    #Waiting area
    roomCode = request.args['roomCode']
    username = request.args['username']
    waitingLocation = request.args['waitingLocation']
    

 
    roomIndex = next((room for room in roomList if room.roomCode == roomCode), None)
    roomIndex = roomList.index(roomIndex)
   
    if waitingLocation == "lobby":
       if username != "admin" and not any(u.name == username for u in roomList[roomIndex].users):
           roomList[roomIndex].users.append(User(username, 0))
       
       if roomList[roomIndex].status == 'running':
          return redirect(url_for('.quiz', roomCode=roomCode, user=username))
       else:
          return render_template('waiting.html', roomCode=roomCode, username=username, waitingLocation="lobby")
    elif waitingLocation == "question":
        initialIndex = request.args['initialIndex']   
        canMoveOn = 'false'
        print(initialIndex)
	print(roomList[roomIndex].currentQuestion)
        if int(initialIndex) < int(roomList[roomIndex].currentQuestion):
            canMoveOn = 'true'
        elif roomList[roomIndex].status == 'results':
            return redirect(url_for('.results', roomCode=roomCode))
        if canMoveOn == 'true':        
            return redirect(url_for('.quiz', roomCode=roomCode, user=username))
        else:
            return render_template('waiting.html', roomCode=roomCode, username=username, waitingLocation="question", initialIndex=initialIndex)

@app.route('/admin', methods=['POST','GET'])
#Dashboard for the admin that runs the quiz
def admin():
    if request.method =='POST':
        print request.form
        roomCode = request.form['roomCode']
        if not any(room for room in roomList if room.roomCode == roomCode):
            roomList.append(Room(roomCode, [], [], 0, "offline", []))       
        roomIndex = roomList.index(next((room for room in roomList if room.roomCode == roomCode), None))
        return redirect(url_for('.questionEdit', roomIndex=roomIndex, roomCode=roomCode))
    return render_template('adminDash.html')

@app.route('/questionedit', methods=['POST', 'GET'])
def questionEdit():
    #Edit the questions
    if request.method == 'POST':
        print request.form
        roomIndex = int(request.args['roomIndex'])
        roomCode = request.args['roomCode']
        requestType = request.form['requestType']
        
        if requestType == "addAnswer":
            questionID = int(request.form['questionID'])
            answer = request.form['answer']
            roomList[roomIndex].questions[questionID].answers.append(answer)
        elif requestType == "deleteAnswer":
            questionID = int(request.form['questionID'])
            answerID = int(request.form['answerID'])
            correctAnswer = int(roomList[roomIndex].questions[questionID].correctAnswer)
            if answerID < correctAnswer:
               roomList[roomIndex].questions[questionID].correctAnswer = correctAnswer - 1
            del roomList[roomIndex].questions[questionID].answers[answerID]
        elif requestType == "setCorrectAnswer":
            questionID = int(request.form['questionID'])
            answerID = int(request.form['answerID'])
            roomList[roomIndex].questions[questionID].correctAnswer = answerID
        elif requestType == "deleteQuestion":
            questionID = int(request.form['questionID'])
            del roomList[roomIndex].questions[questionID]   
        elif requestType == "addQuestion":
            questionText = request.form['questionText']
            answersString = str(request.form['answers'])
            correctAnswer = int(request.form['correctAnswer'])
            answers = answersString.split(";")
            if correctAnswer > len(answers)-1 or correctAnswer < 0:
                correctAnswer = 0
             
            roomList[roomIndex].questions.append(Question(questionText, answers, correctAnswer, []));
        else:
            abort(404)
        saveRoomList()
        return redirect(url_for('.questionEdit', roomIndex=roomIndex, roomCode=roomCode))
    roomIndex = int(request.args['roomIndex'])
    return render_template('questionedit.html', room=roomList[roomIndex])

@app.route('/lobby')
def lobby():
    #Lobby to hold players until the quiz starts
    roomCode = request.args['roomCode'] 
    roomIndex = next((room for room in roomList if room.roomCode == roomCode), None)
    roomIndex = roomList.index(roomIndex)
    roomList[roomIndex].status = 'offline';    
    roomList[roomIndex].currentQuestion = 0;
    for question in roomList[roomIndex].questions:
        question.responders = []

    return render_template('lobby.html', room=next((room for room in roomList if room.roomCode == roomCode), None), update='true')

@app.route('/quiz')
#This is the quiz itself
def quiz():
    roomCode = request.args['roomCode']
    user = request.args['user']
   
    roomIndex = next((room for room in roomList if room.roomCode == roomCode), None)
    if roomIndex != None:
        roomIndex = roomList.index(roomIndex)
        if user == "admin":
            #Admin has started the quiz
            roomList[roomIndex].status = 'running'
    return render_template("quiz.html", room=next((room for room in roomList if room.roomCode == roomCode), None), user=user)

@app.route('/clearusers')
def clearUsers():
    #Removes all users from the room
    roomCode = request.args['roomCode']
    roomIndex = next((room for room in roomList if room.roomCode == roomCode), None)

    if roomIndex != None:
        roomIndex = roomList.index(roomIndex)
        roomList[roomIndex].users = []
    return redirect(url_for('.lobby', roomCode=roomCode))

@app.route('/removeroom')
def removeRoom():
    #Deletes the room
    roomCode = request.args['roomCode']
    roomIndex = next((room for room in roomList if room.roomCode == roomCode), None)
    if roomIndex != None:
        roomIndex = roomList.index(roomIndex)
        del roomList[roomIndex]
    return redirect(url_for('.admin'))
    
@app.route('/debug')
def debug():
    #Shows roomList details for debug purposes
    output = "";
    for room in roomList: 
        output += "(" + room.roomCode + ";" + room.status + ")"
        for user in room.users:
            output += user.name + ";"
        output += "O"
        for question in room.questions:
            output += question.questionText + "R:"
            for responder in question.responders:
                output += responder + ";"
            output += "(ENDOFQUESTION)"
    return "<label>" + output + "</label>"

@app.route('/nextquestion')
def nextquestion():
    #Advance to the next question
    roomCode = request.args['roomCode']
    user = request.args["user"]
    
    roomIndex = next((room for room in roomList if room.roomCode == roomCode), None)
    if roomIndex != None:
       roomIndex = roomList.index(roomIndex)
       if user != "admin":
         answer = request.args['answer']
         userIndex = roomList[roomIndex].users.index(next((u for u in roomList[roomIndex].users if u.name == user), None))
         #Increment user score if they answered the question correctly
         if answer == roomList[roomIndex].questions[roomList[roomIndex].currentQuestion].correctAnswer:
             roomList[roomIndex].users[userIndex].score = roomList[roomIndex].users[userIndex].score + 1
         
         roomList[roomIndex].questions[roomList[roomIndex].currentQuestion].responders.append(user)
     

       print(roomList[roomIndex].users)
       print(roomList[roomIndex].questions[roomList[roomIndex].currentQuestion].responders)
       canMoveOn = 'true'
       for u in roomList[roomIndex].users:
           if u.name not in roomList[roomIndex].questions[roomList[roomIndex].currentQuestion].responders:
               canMoveOn = 'false'
       
       print(canMoveOn)
       if canMoveOn == 'true':
           if roomList[roomIndex].currentQuestion+1 < len(roomList[roomIndex].questions):
               roomList[roomIndex].currentQuestion = roomList[roomIndex].currentQuestion + 1
               return redirect(url_for('.quiz', roomCode=roomCode, user=user)) 
           else:
              roomList[roomIndex].status = 'results'
              roomList[roomIndex].results = calculateResults(roomList[roomIndex].users)
              return redirect(url_for('.results', roomCode=roomCode))
       else:
           return redirect(url_for('.waiting', roomCode=roomCode, username=user, waitingLocation="question", initialIndex=roomList[roomIndex].currentQuestion))


@app.route('/refreshDisplay')
def refreshDisplay():
    #Refresh the host's display to see if the next question should be shown
    roomCode = request.args['roomCode']
    user = request.args['user']
    room = next((room for room in roomList if room.roomCode == roomCode), None)
    if room.status == "results":
        return redirect(url_for('.results', roomCode=roomCode))
    return redirect(url_for('.quiz', roomCode=roomCode, user=user))
   
@app.route('/results')
def results():
    #Show the results screen
    roomCode = request.args['roomCode']
    room = next((room for room in roomList if room.roomCode == roomCode), None)
    return render_template("results.html", room=room)

def saveRoomList():
    #Save the roomList in a pickle file
    with open('roomData.pkl', 'wb') as data:
        pickle.dump(roomList, data)

def calculateResults(users):
    #Calculate the results
    listOfResults = []
    users.sort(key=lambda x: x.score)
    for user in users:
        listOfResults.append(user.name)
        print(user.name)
    return listOfResults
