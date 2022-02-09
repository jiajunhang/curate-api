import girth
import pandas as pd
import numpy as np
import random

def getEstimate(estimator, currentQuestions, currentResponses):
    '''
    Return estimate based on selected estimator
        Parameters:
            estimator: callback func to calculate either using maximum likelihood or bayesian
            currentQuestions: list containing existing questions in JSON
            currentQuestions: list containing responses in int format
        Returns:
            ability_estimate: decimal estimate of student ability
    '''
    if (len(currentQuestions) == 0):
        return str(0)
    
    question_difficulties = list(map(lambda x: x['difficulty'], currentQuestions))

    correct_answers = list(map(lambda x: x['correct'], currentQuestions))
    mapped_responses = list(map(lambda x, y: response_helper(x, y), correct_answers, currentResponses))

    ability_estimate = estimator(mapped_responses, question_difficulties)

    return ability_estimate

def standard_estimator(responses, difficulty):
    total = len(responses)
    score = responses.count(1)

    estimate = score / total

    return str(estimate)

def mle_estimator(responses, difficulty):
    '''
    Return MLE estimate
        Parameters:
            responses: list containing mapped responses (correct/incorrect)
            difficulty: list containing difficulty of questions in decimal format
        Returns:
            ability: decimal estimate of student ability
    '''
    np_responses = np.array([responses]).T
    np_difficulty = np.array(difficulty)

    ability = girth.ability_mle(np_responses, np_difficulty, np.ones_like(responses))

    '''
    Scaled increment/decrement if responses are all correct/wrong
    e.g. last ability is 0, correct:
            3-0=3; 3/3=1, estimate = ~1
    e.g. last ability is 1.5, correct:
            3-1.5=1.5; 1.5/3=0.5, estimate = ~2
    '''
    if np.isnan(ability[0]):
        last_difficulty = abs(np_difficulty[len(np_difficulty)-1])
        diff = (3 - last_difficulty) / 3
        is_correct = np_responses[len(np_responses)-1]

        res = last_difficulty + diff if is_correct == 1 else last_difficulty - diff
        return str(res)
    else:
        return str(ability[0])

def eap_estimator(responses, difficulty):
    '''
    Return EAP estimate
        Parameters:
            responses: list containing mapped responses (correct/incorrect)
            difficulty: list containing difficulty of questions in decimal format
        Returns:
            ability: decimal estimate of student ability
    '''
    np_responses = np.array([responses]).T
    np_difficulty = np.array(difficulty)
    ability = girth.ability_eap(np_responses, np_difficulty, np.ones_like(responses))

    return str(ability[0])


def response_helper(x, y):
    if x == y:
        return 1
    else:
        return 0
