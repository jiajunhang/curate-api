

revisions = {'0': [{'index': 1, 'difficulty': -0.019091637692472574, 'action': 'SELECT_WRONG', 'selected': 3}, {'index': 1, 'difficulty': -0.019091637692472574, 'action': 'MODIFY_CORRECT', 'selected': 1}], '1': [{'index': 2, 'difficulty': -0.4443763450232776, 'action': 'SELECT_WRONG', 'selected': 3}, {'index': 2, 'difficulty': -0.4443763450232776, 'action': 'SELECT_CORRECT', 'selected': 1}], '2': [{'index': 3, 'difficulty': 0.6634606055268444, 'action': 'SELECT_CORRECT', 'selected': 2}, {'index': 3, 'difficulty': 0.6634606055268444, 'action': 'SELECT_WRONG', 'selected': 3}, {'index': 3, 'difficulty': 0.6634606055268444, 'action': 'MODIFY_CORRECT', 'selected': 2}], '3': [{'index': 4, 'difficulty': 0.3492572640078251, 'action': 'SELECT_WRONG', 'selected': 3}, {'index': 4, 'difficulty': 0.3492572640078251, 'action': 'MODIFY_CORRECT', 'selected': 4}], '4': [{'index': 5, 'difficulty': 0.6634606055268444, 'action': 'SELECT_WRONG', 'selected': 1}, {'index': 5, 'difficulty': 0.6634606055268444, 'action': 'SELECT_CORRECT', 'selected': 2}]}

def process_revisions(revisions):

    total_questions = len(revisions)

    indiv_qn_assessments = []

    for idx in revisions:
        currentSequence = revisions[idx]
        difficulty = currentSequence[0]['difficulty']

        modified = did_modify(currentSequence)
        lastSelectionEntry = find_last_selection(currentSequence)
        lastSelection = lastSelectionEntry['action']
        print(lastSelectionEntry)
        print(type(lastSelectionEntry))
        if modified:
            lastModificationEntry = currentSequence[len(currentSequence)-1]
            print(lastModificationEntry)
            print(type(lastModificationEntry))
            lastModification = lastModificationEntry['action']
        else:
            lastModification = "NA"

        assessment = {
            "index": int(idx)+1,
            "difficulty": difficulty,
            "selection": lastSelection,
            "last_revision":  lastModification,
            "n2_score": 1 if modified else 0,
            "nc2_score":  1 if lastModification == "MODIFY_CORRECT" else 0,
            "weighted_nc2": weighted_nc2(difficulty) if lastModification == "MODIFY_CORRECT" else 0
        }

        print(assessment)
        indiv_qn_assessments.append(assessment)
    
    metric = {
        "indiv_qns": indiv_qn_assessments,
        "total_n2": sum(list(map(lambda x: x['n2_score'], indiv_qn_assessments) )) / total_questions,
        "total_nc2": sum(list(map(lambda x: x['nc2_score'], indiv_qn_assessments) )) / total_questions,
        "total_weighted_nc2": sum(list(map(lambda x: x['weighted_nc2'], indiv_qn_assessments) ))
    }

    print(metric)

    return metric

def getValue(element, key):
    return element[key]

def weighted_nc2(difficulty):

    difficulty = abs(difficulty - 3)
    normalized = (difficulty - 0) / 6

    return normalized

def did_modify(seq):
    lastEntry = seq[len(seq)-1]
    lastAction = lastEntry['action']

    if lastAction == "MODIFY_CORRECT" or lastAction == "MODIFY_WRONG":
        return True

    return False

def find_last_selection(seq):
    lastSelection = seq[0]

    for entry in seq:
        if entry['action'] == "SELECT_WRONG" or entry['action'] == "SELECT_CORRECT":
            lastSelection = entry
        else:
            return lastSelection
    
    return lastSelection

#process_revisions(revisions)