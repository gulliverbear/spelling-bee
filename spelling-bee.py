#!/usr/bin/env python3
'''
Play the Spelling Bee game 
Usage:
To download data from nytbee.com:
    python spelling-bee.py update
To play a specific date:
    python spelling-bee.py 20200507
To play today's puzzle:
    python spelling-bee.py

Future ideas to do: 
    help options   
    1 - shows lengths of unguessed words
    2 - shows lengths + first letter of unguessed words
'''

import requests
from bs4 import BeautifulSoup
import datetime
import time
import os
import pytesseract
from PIL import Image
import random
import collections
import sys

def read_saved_words(file):
    '''
    Given the saved-words.txt file
    Reads in all lines to list and returns that list
    '''
    lines = []
    with open(file) as f:
        for line in f:
            line = line.rstrip()
            lines.append(line)
    return lines

def add_words(file, s, log_file):
    '''
    Given saved-words.txt file and s = a new line to write
    makes sure that line does not already exist in file
    Otherwise adds it to saved-words and records that in log_file
    '''
    # first make sure it is not a duplicate line
    seen_words = read_saved_words(file)
    if s in seen_words:
        with open(log_file, 'a') as f:
            f.write('already in file\n')
    else:
        with open(file,'a') as f:
            f.write(s + '\n')
        with open(log_file, 'a') as f:
            f.write('added words\n')

def check_key(date_string, words, user_agent, log_file):
    '''
    Given a list of words found for a date
    See if can determine key as the only letter present in all words
    If cannot determine - call decode_image to do image processing
    '''
    sets = [set(word) for word in words]
    u = set.intersection(*sets)
    if len(u) == 1: # just one key letter possible
        return list(u)[0]
    return decode_image(date_string, user_agent, log_file, u)

def get_words(date_string, user_agent, file, log_file):
    '''
    Given a date_string get the data for that date
    Records the data to file (saved-words.txt)
    Also log to log_file
    '''
    url = f'http://nytbee.com/Bee_{date_string}.html'
    print(f'Getting words for {date_string}...')
    try:
        page_response = requests.get(url, headers=user_agent, timeout=10)
    except:
        sys.exit('Exception occured')

    soup = BeautifulSoup(page_response.content, "html.parser")
    
    # find points for genius
    for i in soup.find_all('h3'):
        if i.text.startswith('Points Needed for Genius'):
            genius = i.text.split()[-1]
            break
    else:
        with open(log_file, 'a') as f:
            f.write('--- GENIUS NOT FOUND POSSIBLY MISSING PAGE ---\n')
        return 
        
    words = []
        
    s = soup.find(id='answer-list')
    if s:
        for li in s.findAll('li'):
            word = li.get_text().strip()
            words.append(word)
    else:
        s = soup.find("div", {'class':'answer-list'})
        if s:
            words = []
            for li in s.findAll('li'):
                word = li.get_text().strip()
                words.append(word)
        else:
            s = soup.find(id='main-answer-list')
            if s:
                words = []
                for li in s.findAll('li'):
                    word = li.get_text().strip()
                    words.append(word)
            else:
                with open(log_file, 'a') as f:
                    f.write('--- NOTHING FOUND ---\n')
                return
            
    key_letter = check_key(date_string, words, user_agent, log_file)
            
    s = f'{date_string}\t{genius}\t{key_letter}\t' + ','.join(words)
    add_words(file, s, log_file)
    return words

def decode_image(date_string, user_agent, log_file, possible_keys):
    '''
    To Do:
    Given: date_string like '20190101'
    Download the image for that date
    Try to cut out the middle part that should have the key letter
    Issue is the images changed size at certain dates
    Then use pytesseract to read that letter
    '''
    pass

def download_image(date_string, user_agent, log_file):
    '''
    Download the image containing the 7 letters (middle is the key letter)
    Taken from this so:
    https://stackoverflow.com/questions/30229231/python-save-image-from-url/30229298
    ran into same issue where I needed to supply the user_agent
    '''
    url = f'https://nytbee.com/pics/{date_string}.png'

    pic_name = os.path.join('pics',f'{date_string}-temp.png')
    with open(pic_name, 'wb') as handle:
        response = requests.get(url, stream=True, headers=user_agent)

        if not response.ok:
            with open(log_file, 'a') as f:
                f.write(response + '\n')
            return
        for block in response.iter_content(1024):
            if not block:
                break
            handle.write(block)
        return pic_name

def scroll_dates(user_agent, file, log_file, n=1000):
    '''
    Scroll through the dates starting with the last date in saved-words.txt
    Keep going one day at a time for n days
    For each day call get_words to get the data for that day
    '''
    # if saved_words.txt doesn't exist create it, and start with earliest date
    if not os.path.isfile(file):
        open(file,'a').close()
        date_string = '20180729'
    else:
        # get the last date in the file, and start on next day
        with open(file) as f:
            for line in f:
                pass
        date_string = line.split('\t')[0]
        date_dt = datetime.datetime.strptime(date_string,'%Y%m%d')
        date_dt += datetime.timedelta(days=1)
        date_string = datetime.datetime.strftime(date_dt,'%Y%m%d')
    
    for _ in range(n):
        date_dt = datetime.datetime.strptime(date_string,'%Y%m%d')

        # make sure haven't passed current day
        if date_dt > datetime.datetime.today():
            break
        with open(log_file, 'a') as f:
            f.write(date_string + '\n')
        get_words(date_string, user_agent, file, log_file)
        
        # advance to next day
        date_dt += datetime.timedelta(days=1)
        date_string = datetime.datetime.strftime(date_dt,'%Y%m%d')
        time.sleep(3) 

def print_letters(letters, key_letter, shuffle):
    '''
    Prints the 7 letters to choose from
    Will shuffle them if shuffle=True
    '''
    n = [i for i in letters if i != key_letter]
    if shuffle:
        random.shuffle(n) # shuffles in place
    print(f'   {n[0]}')
    print(f'{n[1]}     {n[2]}')
    print(f'   {key_letter.upper()}')
    print(f'{n[3]}     {n[4]}')
    print(f'   {n[5]}')
    print()

def print_words(found_words):
    '''
    Sorts the found words so that each row will start with different letter
    '''
    found_words = sorted(found_words)
    last_seen = ''
    s = ''
    for word in found_words:
        if word[0] != last_seen:
            s += '\n'
            last_seen = word[0]
        s += f'{word} '
    print(s.lstrip() + '\n')

if len(sys.argv) > 2:
    sys.exit('usage: python spelling-bee.py [date-string optional eg 20191126] ')
elif len(sys.argv) == 2:
    date_string = sys.argv[1]
else:
    today = datetime.datetime.today()
    date_string = datetime.datetime.strftime(today,'%Y%m%d')

'''
Issue at first where it was saying "Not Acceptable"
Then I found this so site that said to send a user-agent
https://stackoverflow.com/questions/34832970/http-error-406-not-acceptable-python-urllib2
'''

saved_words = os.path.join('data','saved-words.txt')
user_agent = {'User-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A'}
log_file = os.path.join('log','log-file.txt')

if date_string.lower() == 'update':
    scroll_dates(user_agent, saved_words, log_file, 10)
    sys.exit('finished updating')

daily_file = f'{date_string}.out'
found_words = set()
score = 0

with open(saved_words) as f:
    for line in f:
        ds, genius, key_letter, words_string = line.strip().split('\t')
        if ds == date_string:
            break
    else:
        raise SystemError('date string not found')

# see if we are continuing from a pre-existing file
if os.path.isfile(daily_file):
    with open(daily_file) as f:
        for line in f:
            if not line.startswith('#'):
                date_string, word, score = line.rstrip().split('\t')
                found_words.add(word)
                score = int(score)


words = words_string.split(',')
w = ''.join(words)
letters = tuple(set(list(w)))

r = ''
word_score = ''
last_message = ''
shuffle = False

with open(daily_file,'a') as f:
    
    t = datetime.datetime.strftime(datetime.datetime.now(),'%Y.%m.%d.%H.%M.%S.%f')
    f.write('\t'.join(['#'+t, 'starting\n']))

    # main loop
    while True:
        
        os.system('clear')
        print('found words:')
        print_words(found_words)
        print_letters(letters, key_letter, shuffle)
        print("type 's' to shuffle letters")
        print("type 'q' to quit")
        print(f'Genius = {genius}')
        print(f'score = {score}')
        print(f'last word: {r} ({word_score}) ({last_message})')
        last_message = ''
        word_score = ''
        shuffle = False

        r = input().lower()
        t = datetime.datetime.strftime(datetime.datetime.now(),'%Y.%m.%d.%H.%M.%S.%f')

        if r in words:
            if r in found_words:
                last_message = 'already found'
            else:
                found_words.add(r)
                if len(r) == 4:
                    word_score = 1
                else:
                    word_score = len(r)
                if len(set(r)) == 7: # pangram bonus
                    last_message = 'Pangram!'
                    word_score += 7
                score += word_score
                f.write('\t'.join([t, r, str(score)+'\n']))
                if score >= int(genius):
                    last_message += 'Genius achieved!'
        elif r == 's':
            shuffle = True
        elif set(r) - set(letters):
            last_message = 'used wrong letter'
        elif key_letter not in r:
            last_message = f'missing the letter {key_letter}'
        else:
            last_message = 'word not found'
        if r == 'q':
            f.write('#' +t + '\tleaving\n')
            break
