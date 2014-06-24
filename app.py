#!/usr/bin/python

from flask import Flask, render_template, redirect, request, url_for
from pickle import load, dump
from os.path import isfile
from random import choice
from string import lowercase
from gallow_structs import gallow_structs

app = Flask(__name__)

def dump_session_details():
    '''
    -- This function dumps a section of session related details ('session_details')
    on local machine.
    -- It is called after any change in state is observed. This is done in order to
    ensure that games' states remain persistent with server - games' states can be
    easily recreated then.
    '''
    temp = {}
    for name in session_details:
        temp[name] = {'won' : session_details[name]['won'], \
        'lost' : session_details[name]['lost'], \
        'is_new_game' : session_details[name]['is_new_game']}
    dump(temp, open('sessions.pickled', 'wb'))

@app.route('/welcome')
def welcome():
    '''
    -- Welcome page!
    -- This function is the endpoint with which players interact with. 
    -- Assumption : Player names are unique!
    '''
    return render_template('welcome.html')

@app.route('/index', methods = ['GET', 'POST'])
def hello():
    '''
    -- It is responsible for initializing the state of game.
    -- This function also ensures that a player is unable to cheat the game - should the
       player intend to refresh / abandon a game mid-stream, it would be counted as a loss.
    -- All the GET requests are made via internal sources : there is a verification
       mechanism (albeit, simplistic) to ensure that these requests are generated by 
       the internal mechanism. All POST interactions are with the player.
    
    -- Inside 'session_details' DS:
     - lost   			 : count of games lost
     - won  			 : count of games won
     - answer 			 : randomly selected word
     - answer_so_far 	 : answer formed by combining guesses presented by player
     - chars_encountered : set containing character chosen by player
     - chance_number 	 : count of the chances elapsed.
     - is_new_game 		 : used to maintain the current status of game

    '''
    if request.method == 'POST':
        name = request.form['name'].strip()
    elif 'token' in request.args:
        if str(hash(request.args['name'])) == request.args['token']:
            name = request.args.get('name').strip()
        else:
            return redirect(url_for('welcome'))
    else:
        return redirect(url_for('welcome'))
    
    global session_details

    if name not in session_details:
        session_details[name] = {'won':0, 'lost':0, 'is_new_game': True}
    session_details[name]['answer'] = choice(words)
    session_details[name]['answer_so_far'] = '-'*len(session_details[name]['answer'])
    session_details[name]['chars_encountered'] = set()
    session_details[name]['chance_number'] = 0

    if not session_details[name]['is_new_game']:
        session_details[name]['lost'] += 1
        session_details[name]['is_new_game'] = True
        dump_session_details()

    return render_template('game.html', \
        pattern = session_details[name]['answer_so_far'], \
        gallows = gallow_structs[session_details[name]['chance_number']], \
        wins = session_details[name]['won'], losses = session_details[name]['lost'], \
        buttons = [i for i in lowercase], player_name = name)

@app.route('/game/<string:name>', methods = ['POST'])
def hangman_game(name):
    '''
	--- Actual game logic is contained within this function.
	--- Once a player clicks on available set of characters, a POST request is made to this endpoint.
	    The request carries the value of clicked button as a string ("char_input").  The values stored
            in this set are used for generating list of remaining characters (which could be used as 
            guesses) at UI. The character passed using POST (i.e. "char_input") is then used for replacing
            parts of "answer_so_far", i.e. wherever there is a positional match in "answer". If "answer_so_far"
            becomes the "answer" or the number of available chances (i.e. "chance_number") is exhausted,
            the execution redirects itself to the "/index" endpoint. Also, "new_game" variable maintains the
            current state of game. This variable ensures that a user is unable to abandon / refersh the 
            game midway.
    '''
    
    global session_details
    
    name = name.strip()
    char_input = request.form['name'].strip()
    
    if char_input not in session_details[name]['chars_encountered']:

        session_details[name]['is_new_game'] = False
        session_details[name]['chars_encountered'].add(char_input)

        if char_input in session_details[name]['answer']:
            temp = session_details[name]['answer_so_far']
            stored_answer = session_details[name]['answer']
            
            for i in range(len(temp)):
                if temp[i] == '-' and stored_answer[i] == char_input:
                    temp = temp[:i] + char_input + temp[i+1:]
            session_details[name]['answer_so_far'] = temp
        else:
            session_details[name]['chance_number'] += 1

        if session_details[name]['answer_so_far'] ==  session_details[name]['answer'] :    
            session_details[name]['is_new_game'] = True
            session_details[name]['won'] += 1
            dump_session_details()
            
            return redirect(url_for('hello')+'?name=%s&token=%s'%(name, hash(name)))

        if session_details[name]['chance_number'] == 10:
            session_details[name]['is_new_game'] = True
            if session_details[name]['answer_so_far'] ==  session_details[name]['answer'] :    
                session_details[name]['won'] += 1
            else:
                session_details[name]['lost'] += 1
            dump_session_details()
            
            return redirect(url_for('hello')+'?name=%s&token=%s'%(name, hash(name)))

    characters_guessed = session_details[name]['chars_encountered']
    dump_session_details()
    
    return render_template('game.html', \
        pattern = session_details[name]['answer_so_far'], \
        gallows = gallow_structs[session_details[name]['chance_number']], \
        wins = session_details[name]['won'], losses = session_details[name]['lost'], \
        buttons = [i for i in lowercase if i not in characters_guessed], \
        player_name = name)

if __name__ == '__main__':
    
    words = []
    if not isfile('words.pickled'):
        with open('/usr/share/dict/words') as fi:
            for line in fi:
                word = line.strip()
                unique_chars = len(set(word))
                if len(word) > 2 and unique_chars <= 10 and "'" not in word:
                    words.append( word.lower() )
            dump(words, open('words.pickled', 'wb'))
    else:
        words = load(open('words.pickled', 'rb'))

    if not words:
        print "Could not locate the list of words!"
        exit(1)

    session_details = {}
    if isfile('sessions.pickled'):
        session_details = load(open('sessions.pickled', 'rb'))

    app.run(debug = True)



