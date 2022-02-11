
import argparse
import numexpr
import urllib
import requests
import pdb
import re

number_dict = {'one' : '*1.',
               'ten' : '*10.',
               'hundred' : '*100.',
               'thousand' : '*1000.',
               'million' : '*10.**6',
               'billion' : '*10.**9',
               'trillion' : '*10.**12',
               'quadrillion' : '*10.**15',
               'quintillion' : '*10.**18',
               'sextillion' : '*10.**21',
               'septillion' : '*10.**24'}

def calculate(in_str, return_float=False):
    # Evaluate remotely using wolfram.
    if return_float:
        # Convert question to URL and sent to wolfram
        url_str = urllib.parse.quote_plus(in_str)
        app_id = 'Q9RQK4-QK54QKTJ72'
        url_wolfram = 'https://api.wolframalpha.com/v2/query?input=' + url_str + '&appid=' + app_id + '&output=json&scanner=Data'
        
        try:
            # FIXME: raise error if No short answer available
            answer = requests.get(url_wolfram)
            answer_text = answer.json()['queryresult']['pods'][0]['subpods'][0]['img']['title']
            print('Answer (direct from Wolfram): ', answer_text)

            # Simplify answers that are convoluted
            answer_text = answer_text.split('\n', 1)[0] # skip parenthetical clarifications, units.
            answer_text = answer_text.split(' (', 1)[0] # skip blah blah details. THE SPACE IS IMPORTANT
            answer_text = answer_text.split('to', 1)[0] # give lower range

            # Convert math symbols to be python.
            answer_text = answer_text.replace('×', '*')
            answer_text = answer_text.replace('^', '**')
            #answer_text = answer_text.replace(' to the ', '**')
            #answer_text = answer_text.replace(' times ', '*')
            
            # Convert numbers spelled out in words to numbers
            if any([x in answer_text for x in number_dict.keys()]):
                for key in number_dict.keys():
                    if key in answer_text:
                        answer_text = answer_text.replace(key, number_dict[key])
            
            # Fix potential overflow due to integers only.
            if '**' in answer_text:
                if '.' not in answer_text:
                    answer_text += '.'
            
            # Clean up anything that is not a number or relevant math symbol
            answer_text = re.sub('[^1234567890*.]', '', answer_text)
            answer = float(numexpr.evaluate(answer_text))
            print('Answer (float): ', answer)
            return answer
        
        except:
            print('This question\'s answer isn\'t convertable to a string. \n' + 
                  'Try rephrasing your question (e.g. specify units of the result).')

    # Evaluate locally using python.
    else:
        try:
            # Fix potential overflow due to integers only.
            if '**' in in_str:
                if '.' not in in_str:
                    in_str += '.'
            answer = float(numexpr.evaluate(in_str))
            print(answer)
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

    results = parser.parse_args()
    
    
    if (results.question_python != None) & (results.question_wolfram != None):
        raise Exception('Make up your mind! You can only set one flag.')

    if results.question_wolfram is None:
        return_float=False
        question = results.question_python
    else:
        return_float=True     
        question = results.question_wolfram
        
    calculate(question, return_float=return_float)
