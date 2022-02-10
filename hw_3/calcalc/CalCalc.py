
import argparse
import numexpr
import urllib
import requests

def calculate(in_str, return_float=False):
    if return_float:
        url_str = urllib.parse.quote_plus(in_str)
        url_wolfram = 'https://api.wolframalpha.com/v1/result?i=' + url_str + '&appid=DEMO'
        url_wolfram = 'https://api.wolframalpha.com/v1/result?i=How+many+ounces+are+in+a+gallon%3F&appid=DEMO'
        
        answer_str = requests.get(url_wolfram).text
        answer = float(answer_str)
    
    else:
        answer = numexpr.evaluate(in_str)
        print(answer)
        
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
    
    print(results.question_python)
    print(results.question_wolfram)
    
    if (results.question_python != None) & (results.question_wolfram != None):
        raise Exception('Make up your mind! You can only set one flag.')

    if results.question_wolfram is None:
        return_float=False
        question = results.question_python
    else:
        return_float=True     
        question = results.question_wolfram
        
    calculate(question, return_float=return_float)
