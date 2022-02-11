
import argparse
import numexpr
import urllib
import requests
import pdb
import re

def calculate(in_str, return_float=False):
    # Evaluate remotely using wolfram.
    if return_float:
        url_str = urllib.parse.quote_plus(in_str)
        app_id = 'Q9RQK4-QK54QKTJ72'
        url_wolfram = 'https://api.wolframalpha.com/v2/query?input=' + url_str + '&appid=' + app_id + '&output=json&scanner=Data'
        # url_wolfram = 'https://api.wolframalpha.com/v2/query?input=' + url_str + '&appid=' + app_id
        #url_wolfram = 'https://api.wolframalpha.com/v1/result?i=How+many+ounces+are+in+a+gallon%3F&appid=DEMO'
        
        try:
            # Need some condition for "about"
            # No short answer available
            # hundred, ten, thousand, etc...
            answer = requests.get(url_wolfram)
            answer_text = answer.json()['queryresult']['pods'][0]['subpods'][0]['img']['title']
            print('Answer (direct from Wolfram): ', answer_text)
            #answer_text.rstrip().split('(') 
            #answer_text.rstrip().split('\n') 
            answer_text = answer_text.split('\n', 1)[0] # skip parenthetical clarifications, units.
            answer_text = answer_text.split(' (', 1)[0] # skip blah blah details.
            answer_text = answer_text.split('to', 1)[0] # give lower range
            #print(answer_text)
            #answer_text = requests.get(url_wolfram).text
            #print(answer_text)
            answer_text = answer_text.replace('×', '*')
            answer_text = answer_text.replace('^', '**')
            #answer_text = answer_text.replace(' to the ', '**')
            #answer_text = answer_text.replace(' times ', '*')
            answer_text = re.sub('[^1234567890*.]', '', answer_text)
            print('Answer (cleaned up): ', answer_text)
            answer = float(numexpr.evaluate(answer_text))
            print('Answer (float): ', answer)
            return answer
        
        except:
            print('This question\'s answer isn\'t convertable to a string. \n' + 
                  'Try rephrasing your question (e.g. specify units of the result).')

    # Evaluate locally using python.
    else:
        try:
            print('input: ', in_str)
            print('numexpr: ', numexpr.evaluate(in_str))
            answer = float(numexpr.evaluate(in_str))
            print('floated: ', answer)
            return answer
        except:
            print('This expression can\'t be evaluated numerically. \n' + 
                  'Did you mean to evaluate with wolfram? \n' +
                  'If not, check your question for typos.')
        
def test1():
    assert abs(4. - calculate('2**2')) < 0.001
    
def test2():
    assert abs(4. - calculate('2**2')) < 0.001
    
def test3():
    assert abs(4. - calculate('2**2')) < 0.001
    
def test4():
    assert abs(4. - calculate('2**2')) < 0.001
    
def test5():
    assert abs(4. - calculate('2**2')) < 0.001
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Write something useful here.')
    parser.add_argument('-s', action='store', dest='question_python', 
                        help='Numbers', default=None)
    parser.add_argument('-w', action='store', dest='question_wolfram',
                        help='Words', default=None)
    # Maybe edit this, so that instead it will return as string.

    results = parser.parse_args()
    
#    print(results.question_python)
#    print(results.question_wolfram)
    
    if (results.question_python != None) & (results.question_wolfram != None):
        raise Exception('Make up your mind! You can only set one flag.')

    if results.question_wolfram is None:
        return_float=False
        question = results.question_python
    else:
        return_float=True     
        question = results.question_wolfram
        
    calculate(question, return_float=return_float)
