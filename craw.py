import threading
import time

import requests
import traceback
import ast
from hexicapi import save
from typing import *

judge_url: str = "https://judge.softuni.org/"
login_url: str = "https://judge.softuni.org/Account/Login"
list_of_content_groups = {
    "Programming Basics": {
        "C# Basics": "245/CSharp-Basics",
        "Java Basics": "246/Java-Basics",
        "JS Basics": "247/JS-Basics",
        "Python Basics": "248/Python-Basics",
        "PB - More Exercises": "193/PB-More-Exercises",
        "PB - Exams": "38/PB-Exams",
        "C++ Basics": "100/CPlusPlus-Basics",
        "Go Basics": "338/Go-Basics",
    },
    "Fundamentals": {
        "C# Fundamentals": "149/CSharp-Fundamentals",
        "Java Fundamentals": "145/Java-Fundamentals",
        "JS Fundamentals": "147/JS-Fundamentals",
        "Python Fundamentals": "191/Python-Fundamentals",
        "PHP Fundamentals": "148/PHP-Fundamentals",
        "Fundamentals - Common": "154/Fundamentals-Common", # It's one lab LMAO
        "Fundamentals - Exams": "153/Fundamentals-Exams",
    },
    "Advanced": {
    	"C# Advanced": "182/CSharp-Advanced-Exercises",
    	"Java Advanced": "175/Java-Advanced-Exercises",
    	"Javascript Advanced": "306/JS-Advanced-Exercises",
    	"Python Advanced": "209/Python-Advanced-Exercises"
    },
    "OOP": {
    	"C# OOP": "184/CSharp-OOP-Exercises",
    	"Java OOP": "187/Java-OOP-Exercises",
    	"Javascript Applications": "308/JS-Applications-Exercises",
    	"Python OOP": "210/Python-OOP-Exercises"
    },
    "DB Fundamentals": {
    	"MS-SQL": "62/CSharp-Databases-Basics-Exercises",
    	"MySQL": "66/Java-Databases-Basics-Exercises",
    	"Entity Framework Core": "68/CSharp-Databases-Advanced-Exercises",
    	"Spring Data": "71/Java-Databases-Advanced-Exercises"
    },
    "Web Exams": {
    	"C# Web Exams": "90/CSharp-Web-Development-Basics-Exams",
    	"Java Web Exams": "91/Java-Web-Development-Basics-Exams",
    	"ExpressJS Exams": "119/ExpressJS-Exams",
    	"ReactJS Exams": "120/ReactJS-Exams",
        "Python Web Exams": "290/Python-Web-Basics-Exams"
    },
    "Front-End": {
    	"JS Front-End": "380/JS-Front-End-Exercise",
        "HTML & CSS": "134/HTML-and-CSS-Exercises"
    },
     "Open Courses": {
    	"MongoDB Exams": "243/MongoDB",
        "HTML & CSS": "134/HTML-and-CSS-Exercises",
        "C# Algorithms Fundamentals": "280/Algorithms-Fundamentals-Exercises",
        "C# Algorithms Advanced": "282/Algorithms-Advanced-Exercises",
        "Java Algorithms Fundamentals": "255/Algorithms-Fundamentals-Exercises",
        "Java Algorithms Advanced": "257/Algorithms-Advanced-Exercises",
        "Python Algorithms Fundamentals": "351/Algorithms-Fundamentals-Exercises",
        "C# Data Structures Fundamentals": "261/Data-Structures-Fundamentals-Exercises",
        "C# Data Structures Advanced": "265/Data-Structures-Advanced-Exercises",
        "Java Data Structures Fundamentals": "215/Data-Structures-Fundamentals-Exercises",
        "Java Data Structures Advanced": "217/Data-Structures-Advanced-Exercises"
    },
    "Pick my own using <number>/<name> format from url": {}
}
contests_category_url: str = None
try:
    contests_category_url = save.load('url_backup.sav')[0]
    contests_category_url_was_loaded = True
    print('Loaded url_backup.sav url data.')
except TypeError: contests_category_url_was_loaded = False
finally: i = 2 if contests_category_url_was_loaded else 'g'

try:
    complete_exercises = save.load('completed_exercises.sav')[0]
except: complete_exercises = []

while type(i) != int:
    print(*[f"[{i}] {key}" for i, key in enumerate(list_of_content_groups.keys())], sep="\n")
    i = input("Pick: ")
    try:
        i = int(i)
    except ValueError:
        print('\n\nTry again')

group = list_of_content_groups[list(list_of_content_groups.keys())[i]]
if len(group.keys()) > 0:
    i = 'g'
    while type(i) != int:
        print(*[f"[{i}] {key}" for i, key in enumerate(group.keys())], sep="\n")
        i = input("Pick: ")
        try:
            i = int(i)
        except ValueError:
            print('\n\nTry again')
    contests_category_url = group[list(group.keys())[i]]

if not contests_category_url:
    contests_category_url: str = input("url: ")
if not contests_category_url_was_loaded:
    if input('save url? [y/N] ').lower() == 'y':
        save.save('url_backup.sav', contests_category_url)
        print('Saved.\n')
    else:
        print('Skipped.\n')

exercise_result_page_size = 10

S = requests.session()
craw_time = 0

def get_verification_token() -> str:
    resp = S.get(login_url)
    html = resp.content.decode('utf-8')
    element = html.split('<input name="__RequestVerificationToken" ')[1].split('>')[0]
    value = element.split('value=')[1].split('"')[1]
    return value


def get_login_data(username: str, password: str) -> bool:
    token = get_verification_token()
    resp = S.post(login_url, {
        '__RequestVerificationToken': token,
        'UserName': username,
        'Password': password,
        'RememberMe': False,
    }, allow_redirects=False)
    return resp.status_code == 302


def yes_or_no(msg: str) -> bool:
    return input(f'{msg} [Y/n]').lower() != 'n' or False


def get_contests(category_url: str) -> Tuple[list[dict], int]:
    global craw_time
    contests: list[dict] = []
    for i in range(1,21): # This is the amount of pages to try and scrape!
        resp = S.get(judge_url+f'Contests/List/ByCategory/{category_url}?page={i}')
        if 'The selected category is empty.' in resp.text: break
        lines = resp.text.splitlines(False)
        for i, line in enumerate(lines):
            start = time.time()
            if line.startswith('<a href="    /Contests/'):
                identifier, url_name = line.split('Contests/')[1].split('/')
                name = lines[i+1].split('>')[1].rstrip('</a')
                contests.append({
                    'identifier': int(identifier),
                    'name': name,
                    'url_name': url_name,
                    'type': 'compete' if lines[i+4] != '</td>' else 'practice'
                })
                threading.Thread(target=get_exercises, args=(contests[-1],), daemon=True).start()
            craw_time += time.time()-start
    return contests, i-1


def get_exercise_information(exercise_url: str, clickable_url: str):
    exercise = {
        'url': exercise_url,
        'clickable_url': clickable_url
    }

    resp = S.get(judge_url+exercise_url.lstrip('/'))
    exercise['full_name'] = resp.text.split('\n<h2>\n')[1].split('\n')[0]
    number, name = exercise['full_name'].split(maxsplit=1)
    exercise['number'] = int(''.join([n for n in number if n.isdecimal()]))
    exercise['name'] = name
    resp = S.post(judge_url + exercise_url.lstrip('/').replace('Problem','ReadSubmissionResults'), {
        'sort': "SubmissionDate-desc",
        'page': 1,
        'pageSize': exercise_result_page_size,
        'group': '',
        'filter': ''
    })
    dict_text: str = resp.text
    dict_text = dict_text.replace('null','None')
    dict_text = dict_text.replace('true','True')
    dict_text = dict_text.replace('false','False')
    try:
        exercise['submission_data'] = ast.literal_eval(dict_text)
    except:
        print(f"Can't text to dict the following: \n{dict_text}\n")


    return exercise


def get_exercises(contest: dict):
    global craw_time
    resp = S.get(judge_url+f'Contests/{contest["type"].capitalize()}/Index/{contest["identifier"]}#0')
    exercises: list[dict] = []
    #print(resp.text)
    exercise_urls: list[str] = resp.text.split('"contentUrls":[')[1].split(']')[0].split(',')
    for i, exercise_url in enumerate(exercise_urls):

        exercise_url = exercise_url.strip('"')
        # Get the completed urls, continue if it's in them
        if exercise_url in [exercise['url'] for exercise in complete_exercises]: continue
        exercises.append(get_exercise_information(exercise_url,
                        judge_url+f'Contests/{contest["type"].capitalize()}/Index/{contest["identifier"]}#{i}'))
    contest['exercises'] = exercises


def login_to_judge() -> None:
    try:
        username, password = save.load('login.sav')
        used_saved = True
    except:
        username, password = input("username: "), input("password: ")
        used_saved = False

    login = get_login_data(username, password)
    while not login:
        print("Wrong login!")
        username, password = input("username: "), input("password: ")
        used_saved = False
        login = get_login_data(username, password)

    if (not used_saved) and yes_or_no('Save?'):
        save.save('login.sav', username, password)


login_to_judge()
contests_list, number_of_pages = get_contests(contests_category_url)

print(f"Got {len(contests_list)} contests!")
exercise_list: list[dict] = []
exercise_list.extend(complete_exercises) # extend with the completed exercises
for contest_dict in contests_list:
    start = time.time()
    while 'exercises' not in contest_dict.keys(): pass
    exercise_list.extend(contest_dict['exercises'])
    print(f"Scanned contest \"{contest_dict['name']}\"")
    craw_time += time.time() - start

print(f"Got {len(exercise_list)} exercises!")

contests_list = [contest for contest in contests_list if contest['type'] != 'unknown']

save.save('exercises.sav', contests_list, exercise_list)

print(f"Total time for crawing: {time.strftime('%M:%S', time.gmtime(craw_time))}")

# print("Please use the evaluate.py to get your evaluation")

import evaluate

input("Press enter to exit ")
