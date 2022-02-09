from flask import Flask, request
from flask_cors import CORS
from pymongo import MongoClient
from bson.json_util import dumps, loads
from bson.objectid import ObjectId
from estimators import getEstimate, standard_estimator, mle_estimator, eap_estimator
from detection import process_revisions
from datetime import datetime

from dotenv import load_dotenv

import os
import girth
import pandas as pd
import numpy as np
import random

app = Flask(__name__)
CORS(app)

# Load config from a .env file:
load_dotenv()
MONGODB_URI = os.environ['MONGODB_URI']

# Connect to your MongoDB cluster:
client = MongoClient(MONGODB_URI)
db = client['curate']

pools = db['pools']
quizzes = db['quizzes']

sample_questions = db['sample_questions']
#qns = db['questions'] FOR LIVE DATA

survey = db['survey']
results = db['results']

@app.route("/")
def hello_world():
  return "Hello, World!"

@app.route("/get_calibration_questions", methods=['GET'])
def get_calibration_questions():
    calib_qn = db['python_bank'].find()
    return dumps(list(calib_qn))
    
@app.route("/sample_questions", methods=['GET'])
def get_sample_questions():
    sample = sample_questions.find().sort('difficulty')
    return dumps(list(sample))

@app.route("/pools", methods=['GET'])
def get_pools():
    pools_data = pools.find()
    return dumps(list(pools_data))

@app.route("/quizzes", methods=['GET', 'POST'])
def get_quizzes():
    if request.method == 'GET':
        quizzes_data = quizzes.find()
        return dumps(list(quizzes_data))
    elif request.method == 'POST':
        data = request.get_json()
        print(data)
        newQuiz = quizzes.insert_one(data)
        return dumps(newQuiz.inserted_id)

@app.route("/quizzes/<id>", methods=['GET'])
def get_quiz_by_id(id):

    res = quizzes.find_one(ObjectId(id))
    return dumps(res)

@app.route("/results/<quizId>", methods=['GET'])
def get_results_by_quizId(quizId):
    res = results.find( {'quizId': quizId} )

    return dumps(res)

@app.route("/result/<resultId>", methods=['GET'])
def get_result_by_resultId(resultId):
    res = results.find_one(ObjectId(resultId))
    return dumps(res)

"""
V2: Parameterized DB collection name
"""
@app.route("/get_questions/<collectionId>", methods=['POST'])
def get_questions_by_id(collectionId):
    '''
    Return test/quiz list of questions
        Parameters:
            group: callback func to calculate either using maximum likelihood or bayesian
            questions: list containing existing questions in JSON
            responses: list containing responses in int format
        Returns:
            questions: updated list of questions
    '''
    body = request.get_json()
    #print(body)

    # Extract fields from request body
    group = body['group']
    currentQuestions = body['questions']
    currentResponses = body['responses']

    print(group)
    # Selecting estimator
    if group == "STD":
        estimator = standard_estimator
    elif group == "MLE":
        estimator = mle_estimator
    else:
        estimator = eap_estimator

    # Calculate current estimate based on responses thus far
    currentEstimate = getEstimate(estimator, currentQuestions, currentResponses)
    print('currentEstimate: ' + currentEstimate)

    # Item selection based on Maximum Fisher Information
    if group == "STD":
        print("going into STD handling")
        nextQuestion = getRandomQuestionById(collectionId, parseAllIds(currentQuestions))
    else:
        print("going into ADAPTIVE handling")
        nextQuestion = getQuestionByIdEstimate(collectionId, parseAllIds(currentQuestions), currentEstimate)

    currentQuestions.append(nextQuestion)

    return dumps(currentQuestions)


"""
V1: Simple get with hardcoded DB collection
"""
""" @app.route("/get_questions", methods=['POST'])
def get_questions():
    '''
    Return test/quiz list of questions
        Parameters:
            group: callback func to calculate either using maximum likelihood or bayesian
            questions: list containing existing questions in JSON
            responses: list containing responses in int format
        Returns:
            questions: updated list of questions
    '''
    body = request.get_json()
    #print(body)

    # Extract fields from request body
    group = body['group']
    currentQuestions = body['questions']
    currentResponses = body['responses']

    #TODO: Question selection for Group 1 (Random Selection)

    # Selecting estimator
    if group == 1:
        estimator = standard_estimator
    elif group == 2:
        estimator = mle_estimator
    else:
        estimator = eap_estimator

    # Calculate current estimate based on responses thus far
    currentEstimate = getEstimate(estimator, currentQuestions, currentResponses)
    print('currentEstimate: ' + currentEstimate)

    # Item selection based on Maximum Fisher Information
    if group == 1:
        nextQuestion = getRandomQuestion(currentQuestions)
    else:
        nextQuestion = getQuestionByEstimate(currentQuestions, currentEstimate)

    currentQuestions.append(nextQuestion)

    # Dummy Data for testing
    #data = {"correct": 4,"difficulty": -2.5492972826209277,"index": 1,"options": ["xzIjadaaaatB","6HchSbaaaaMSWeWaaaa","c0-nrdaaaaRkMGqcaaaa","RIreQcaaaa07dBHdaaa","KxO1hcaaaaOBNaMaaaa"],"question": "jaz3BdaaaaUm3iKdaaaaK30"}
    #print(type(currentQuestions))
    #print(type(data))
    #currentList.append(data)

    return dumps(currentQuestions) """
    

@app.route("/get_survey_questions", methods=['GET'])
def get_survey_questions():
    surveyQn = survey.find();
    return dumps(list(surveyQn))


@app.route("/submit_adaptive_quiz", methods=['POST'])
def submit_adaptive_quiz():
    body = request.get_json()
    print("body:")
    print(body)

    data = body['data']
    quiz_data = body['quizData']

    if 'survey' in quiz_data:
        survey_data = quiz_data['survey'] 
    else:
        survey_data = "N.A"

    group = data['quiz']['estimator']
    questions = quiz_data['questions']
    print("questions:")
    print(questions)
    responses = quiz_data['responses']
    logs = quiz_data['logs']
    print("logs:")
    print(logs)

    revisions = quiz_data['revisions']
    print("revisions:")
    print(revisions)

    if group == "STD":
        estimator = standard_estimator
        est_text = "N.A"
    elif group == "MLE":
        estimator = mle_estimator
        est_text = "MLE"
    else:
        estimator = eap_estimator
        est_text = "EAP"
    
    correct_answers = list(map(lambda x: x['correct'], questions))
    mapped_responses = list(map(lambda x, y: response_helper(x, y), correct_answers, responses))
    
    final_estimate = getEstimate(estimator, questions, responses)

    res = {
        "quizId": data['quiz']['_id']['$oid'],
        "datetime": datetime.now().strftime("%d %B %Y, %H:%M:%S"),
        "summary" : {
            "quiz_name": data['quiz']['name'],
            "name": data['name'],
            "matric": data['matric'],
            "estimator": est_text,
            "ability": final_estimate,
            "total_questions": len(questions),
            "total_correct": mapped_responses.count(1)
        },
        "detail": {
            "questions": list(map(lambda x: parseQuestions(x), questions)),
            "responses": responses
        },
        "survey": {
            "likert_score": "N.A" if survey_data == "N.A" else sum(survey_data['answers']) 
        },
        "logs": logs,
        "metrics": process_revisions(revisions)
    }

    inserted = results.insert_one(res)

    quizId = data['quiz']['_id']['$oid']
    incrementQuizAttempt(quizId)
    incrementQuestionStats(quizId, questions, mapped_responses)
    
    print(inserted.inserted_id)
    
    return str(inserted.inserted_id)

def incrementQuizAttempt(quizId):
    quizObjId = ObjectId(quizId)
    res = quizzes.update_one( {'_id': quizObjId}, { '$inc': {'attempts': 1} })
    return res

def incrementQuestionStats(quizId, questions, mapped_responses):
    selectedQuiz = quizzes.find_one( {'_id': ObjectId(quizId) } )
    collectionId = selectedQuiz['collectionId']
    
    selectedCollection = db[collectionId]

    for i in range(len(questions)):
        currentQn = questions[i]
        oid = currentQn['_id']
        response = mapped_responses[i]

        if response == 0:
            selectedCollection.update_one( {'_id': oid}, { '$inc': { 'total_attempts': 1} } )
        elif response == 1:
            selectedCollection.update_one( {'_id': oid}, { '$inc': { 'total_attempts': 1, 'total_correct': 1 } } )
        

@app.route("/submit_quiz", methods=['POST'])
def submit_quiz():
    body = request.get_json()
    print("body:")
    print(body)

    data = body['data']
    quiz_data = body['quizData']
    survey_data = body['surveyData']

    group = data['group']
    questions = quiz_data['questions']
    responses = quiz_data['responses']

    if group == 1:
        estimator = standard_estimator
        est_text = "N.A"
    elif group == 2:
        estimator = mle_estimator
        est_text = "MLE"
    else:
        estimator = eap_estimator
        est_text = "EAP"
    
    correct_answers = list(map(lambda x: x['correct'], questions))
    mapped_responses = list(map(lambda x, y: response_helper(x, y), correct_answers, responses))
    
    final_estimate = getEstimate(estimator, questions, responses)

    res = {
        "summary" : {
            "name": data['name'],
            "matric": data['matric'],
            "estimator": est_text,
            "ability": final_estimate,
            "total_questions": len(questions),
            "total_correct": mapped_responses.count(1)
        },
        "detail": {
            "questions": list(map(lambda x:x['index'], questions)),
            "responses": responses,
            "accuracy": mapped_responses
        },
        "survey": {
            "group": data['group'] ,
            "likert_score": sum(survey_data['answers'])
        }
    }
    print("res:")
    print(res)

    #TODO: persist into mongoDB
    return res

def getQuestionByIdEstimate(collectionId, currentQuestions, currentEstimate):

    collection = db[collectionId]
    all_qns = list(collection.find())
    print("\n\n\n*********************** all_qns: " + str(len(all_qns)))
    print(all_qns[0:3])
    
    print("\n\n\n*********************** currentQuestions: " + str(len(currentQuestions)))
    print(currentQuestions)

    currentEstimate = float(currentEstimate)
    print("pre clone db")

    # Clone DB & remove used indices
    qn_pool = [x for x in all_qns if x not in currentQuestions]
    print("*********************** qn_pool: " + str(len(qn_pool)))
    print(qn_pool[0:3])

    print("post clone db")
    print(type(qn_pool))

    # Clone question into difficulty
    difficulty_pool = list(map(lambda x:x['difficulty'], qn_pool))
    print("post map difficulty")

    # Perform binary search
    lo = 0
    hi = len(difficulty_pool)-1
    res = -1

    while lo <= hi:
        mid = (lo+hi) // 2
        
        if difficulty_pool[mid] <= currentEstimate:
            lo = mid+1
        else:
            hi = mid-1
    
    res = mid
    nextQn = qn_pool[res]

    return nextQn

def getRandomQuestionById(collectionId, currentQuestions):
    print("getRandQnById")
    collection = db[collectionId]
    all_qns = list(collection.find())
    print(len(all_qns))
    qn_pool = [x for x in all_qns if x not in currentQuestions]

    random_index = random.randint(0,len(qn_pool)-1)

    nextQn = qn_pool[random_index]

    return nextQn



'''
TODO: 
1. Further validation, check adjacent values for a more accurate value
2. Testing with dummy data
3. Randomize across neighbors(?)
'''
""" def getQuestionByEstimate(currentQuestions, currentEstimate):
    all_qns = list(sample_questions.find()) # for LIVE, change sample_questions to qns

    currentEstimate = float(currentEstimate)
    print("pre clone db")

    # Clone DB & remove used indices
    qn_pool = [x for x in all_qns if x not in currentQuestions]
    print("post clone db")
    print(type(qn_pool))

    # Clone question into difficulty
    difficulty_pool = list(map(lambda x:x['difficulty'], qn_pool))
    print("post map difficulty")

    # Perform binary search
    lo = 0
    hi = len(difficulty_pool)-1
    res = -1

    while lo <= hi:
        mid = (lo+hi) // 2
        
        if difficulty_pool[mid] <= currentEstimate:
            lo = mid+1
        else:
            hi = mid-1
    
    res = mid
    nextQn = qn_pool[res]

    return nextQn


def getRandomQuestion(currentQuestions):
    all_qns = list(sample_questions.find()) # for LIVE, change sample_questions to qns
    qn_pool = [x for x in all_qns if x not in currentQuestions]

    random_index = random.randint(0,len(qn_pool)-1)

    nextQn = qn_pool[random_index]

    return nextQn """

def parseAllIds(qnList):
    for q in qnList:
        q = parseQuestions(q)
    return qnList

def parseQuestions(question):
    oid = question['_id']['$oid']
    question['_id'] = ObjectId(oid)

    print("parsed:")
    print(question)
    return question

def response_helper(x, y):
    if x == y:
        return 1
    else:
        return 0