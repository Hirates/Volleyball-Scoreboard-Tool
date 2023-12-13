from flask import Flask, render_template_string, request, jsonify, redirect, url_for, render_template
import requests

app = Flask(__name__)

def read_value(filename, default_value=""):
    try:
        with open(filename, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return default_value

def reset_scores():
    # Implementieren Sie hier die Logik zum Zurücksetzen der Punkte beider Teams
    write_value('team1_score.txt', 0)
    write_value('team2_score.txt', 0)

def write_value(filename, value):
    with open(filename, 'w') as file:
        file.write(str(value))

@app.route('/update/<team>/<action>', methods=['POST'])
def update_score(team, action):
    score_filename = f'{team}_score.txt'
    other_team_score_filename = 'team2_score.txt' if team == 'team1' else 'team1_score.txt'
    sets_filename = f'{team}_sets.txt'
    serving_team_filename = f'{team}_serve.txt'
    other_serving_team_filename = 'team2_serve.txt' if team == 'team1' else 'team1_serve.txt'

    score = int(read_value(score_filename, "0"))
    other_team_score = int(read_value(other_team_score_filename, "0"))
    sets = int(read_value(sets_filename, "0"))

    set_point = False  # Flag für Satzball
    match_point = False  # Flag für Matchball

    if action == 'increment':
        score += 1
        write_value(serving_team_filename, '.')  
        write_value(other_serving_team_filename, '')  

        # Überprüfen auf Satzball
        if score >= 24 and (score - other_team_score) >= 1:
            set_point = True
            try:
                companion_url = "http://127.0.0.1:8888/press/bank/4/10" if team == 'team1' else "http://127.0.0.1:8888/press/bank/4/12"
                requests.get(companion_url)
            except requests.RequestException as e:
                print(f"Fehler beim Senden der Anfrage an Bitfocus Companion für Satzball: {e}")

        # Überprüfen, ob der aktuelle Punktestand einen Satzgewinn bedeutet
        if score >= 25 and (score - other_team_score) >= 2:
            sets += 1
            score = 0
            other_team_score = 0
            write_value(sets_filename, sets)
            set_point = False  # Zurücksetzen des Satzball-Flags

            # Überprüfen auf Matchball
            if sets == 2:  # Annahme: Best of 5 Spiele
                match_point = True
                try:
                    companion_url = "http://127.0.0.1:8888/press/bank/4/18" if team == 'team1' else "http://127.0.0.1:8888/press/bank/4/20"
                    requests.get(companion_url)
                except requests.RequestException as e:
                    print(f"Fehler beim Senden der Anfrage an Bitfocus Companion für Matchball: {e}")

            # Wechselt den Aufschlag nach dem Satzgewinn
            initial_serve = read_value('initial_serve.txt', 'team1')
            if initial_serve == 'team1':
                new_serve = 'team2' if sets % 2 == 1 else 'team1'
            else:
                new_serve = 'team1' if sets % 2 == 1 else 'team2'

            write_value('team1_serve.txt', '.' if new_serve == 'team1' else '')
            write_value('team2_serve.txt', '.' if new_serve == 'team2' else '')

    elif action == 'decrement' and score > 0:
        score -= 1
        # Entfernen des Satzball-Status und Matchball-Status, falls nötig
        if score < 24 or (score - other_team_score) < 1:
            set_point = False
            match_point = False

    write_value(score_filename, score)
    write_value(other_team_score_filename, other_team_score)

    # Rückgabe der aktualisierten Werte und der Status für Satzball und Matchball
    return jsonify(score=score, sets=sets, other_team_score=other_team_score, set_point=set_point, match_point=match_point)

@app.route('/mvp-confirm', methods=['GET', 'POST'])
def mvp_confirm():
    if request.method == 'POST':
        try:
            requests.get("http://127.0.0.1:8888/press/bank/4/25")
        except requests.RequestException as e:
            print(f"Fehler beim Senden der Anfrage an Bitfocus Companion: {e}")
        return redirect(url_for('thank_you'))
    mvp = read_value('mvp.txt', '')
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
        <div class="container team">
            <h2>MVP Bestätigung</h2>
            <p>Ausgewählter MVP: {{ mvp }}</p>
            <form action="/mvp-confirm" method="post">
                <button type="submit" class="button">Pushen</button>
            </form>
        </div>
    </body>
    </html>
    ''', mvp=mvp)

@app.route('/thank-you', methods=['GET'])
def thank_you():
    return render_template('thank_you.html')


@app.route('/setpoint/<team>', methods=['POST'])
def setpoint(team):
    # Logik für Satzball (kann Bedingungen enthalten, um zu prüfen, ob es ein Satzball ist)
    try:
        if team == 'team1':
            companion_url = "http://127.0.0.1:8888/press/bank/4/10"  # Setzen Sie die richtige URL hier
        elif team == 'team2':
            companion_url = "http://127.0.0.1:8888/press/bank/4/12"  # Setzen Sie die richtige URL hier
        requests.get(companion_url)
    except requests.RequestException as e:
        print(f"Fehler beim Senden der Anfrage an Bitfocus Companion für Satzball: {e}")
    # Weitere Aktionen oder Antwort
    return jsonify(success=True)

@app.route('/matchpoint/<team>', methods=['POST'])
def matchpoint(team):
    # Logik für Matchball (kann Bedingungen enthalten, um zu prüfen, ob es ein Matchball ist)
    try:
        if team == 'team1':
            companion_url = "http://127.0.0.1:8888/press/bank/4/18"  # Setzen Sie die richtige URL hier
        elif team == 'team2':
            companion_url = "http://127.0.0.1:8888/press/bank/4/20"  # Setzen Sie die richtige URL hier
        requests.get(companion_url)
    except requests.RequestException as e:
        print(f"Fehler beim Senden der Anfrage an Bitfocus Companion für Matchball: {e}")
    # Weitere Aktionen oder Antwort
    return jsonify(success=True)


@app.route('/timeout/<team>', methods=['POST'])
def timeout(team):
    timeout_filename = f'{team}_timeout.txt'
    timeout_count = int(read_value(timeout_filename, "0"))
    timeout_count += 1
    write_value(timeout_filename, timeout_count)

    try:
        # URL für Bitfocus Companion je nach Team
        if team == 'team1':
            companion_url = "http://127.0.0.1:8888/press/bank/4/2"
        elif team == 'team2':
            companion_url = "http://127.0.0.1:8888/press/bank/4/4"

        requests.get(companion_url)
    except requests.RequestException as e:
        print(f"Fehler beim Senden der Anfrage an Bitfocus Companion: {e}")

    return jsonify(timeout=timeout_count)

@app.route('/mvp')
def mvp():
    mvp_name = read_value('mvp.txt', "Unbekannter Spieler")
    return render_template('mvp.html', mvp_name=mvp_name)

def read_value(file_path, default_value):
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return default_value


@app.route('/zuschauer')
def zuschauer():
    viewers_count = read_value('viewers_count.txt', "0")
    return render_template('zuschauer.html', viewers_count=viewers_count)


@app.route('/match-end', methods=['GET', 'POST'])
def match_end():
    if request.method == 'POST':
        mvp = request.form.get('mvp', '')
        write_value('mvp.txt', mvp)
        return redirect(url_for('mvp_confirm'))

    players = ["Spieler 1", "Spieler 2", "Spieler 3", "Spieler 4", "Spieler 5", 
               "Spieler 6", "Spieler 7", "Spieler 8", "Spieler 9", "Spieler 10"]
    return render_template('match_end.html', players=players)

@app.route('/match-settings', methods=['GET', 'POST'])
def match_settings():
    if request.method == 'POST':
        team1_name = request.form.get('team1_name', '')
        team2_name = request.form.get('team2_name', '')
        serving_team = request.form.get('serving_team', 'team1')

        initial_serve = request.form.get('serving_team', 'team1')
        write_value('initial_serve.txt', initial_serve)

        write_value('team1_name.txt', team1_name)
        write_value('team2_name.txt', team2_name)

        if serving_team == 'team1':
            write_value('team1_serve.txt', '.')
            write_value('team2_serve.txt', '')
        else:
            write_value('team1_serve.txt', '')
            write_value('team2_serve.txt', '.')
        
        if initial_serve == 'team1':
            write_value('team1_serve.txt', '.')
            write_value('team2_serve.txt', '')
        else:
            write_value('team1_serve.txt', '')
            write_value('team2_serve.txt', '.')

        return redirect(url_for('index'))

    team1_name = read_value('team1_name.txt', "Team 1")
    team2_name = read_value('team2_name.txt', "Team 2")
    return render_template('match_settings.html', team1_name=team1_name, team2_name=team2_name)


@app.route('/toggle-serve/<team>', methods=['POST'])
def toggle_serve(team):
    serving_team_filename = f'{team}_serve.txt'
    current_state = read_value(serving_team_filename)
    new_state = '.' if current_state == '' else ''
    write_value(serving_team_filename, new_state)
    return redirect(url_for('index'))

@app.route('/update-name/<team>', methods=['POST'])
def update_team_name(team):
    team_name_filename = f'{team}_name.txt'
    new_name = request.form.get('name', '')
    write_value(team_name_filename, new_name)
    return redirect(url_for('index'))

@app.route('/viewers', methods=['GET', 'POST'])
def viewers():
    if request.method == 'POST':
        viewers_count = request.form.get('viewers', '')
        write_value('viewers_count.txt', viewers_count)
        return redirect(url_for('index'))
    viewers_count = read_value('viewers_count.txt', '0')
    return render_template('viewers.html', viewers_count=viewers_count)

# Stellen Sie sicher, dass die Funktionen write_value und read_value, wie bereits definiert, vorhanden sind
@app.route('/get-scores')
def get_scores():
    team1_score = read_value('team1_score.txt', "0")
    team2_score = read_value('team2_score.txt', "0")
    team1_sets = read_value('team1_sets.txt', "0")
    team2_sets = read_value('team2_sets.txt', "0")
    team1_name = read_value('team1_name.txt', "Team 1")
    team2_name = read_value('team2_name.txt', "Team 2")
    team2_serve = read_value('team2_serve.txt', "Team 2")
    team1_serve = read_value('team1_serve.txt', "Team 1")
    return jsonify(team1_score=team1_score, team2_score=team2_score, 
                   team1_sets=team1_sets, team2_sets=team2_sets, 
                   team1_name=team1_name, team2_name=team2_name, team2_serve=team2_serve, team1_serve=team1_serve)
                    


@app.route('/scoreboard-overlay')
def scoreboard_overlay():
    team1_score = read_value('team1_score.txt', "0")
    team2_score = read_value('team2_score.txt', "0")
    team1_sets = read_value('team1_sets.txt', "0")
    team2_sets = read_value('team2_sets.txt', "0")
    team1_name = read_value('team1_name.txt', "Team 1")
    team2_name = read_value('team2_name.txt', "Team 2")
    team2_serve = read_value('team2_serve.txt', "Team 2")
    team1_serve = read_value('team1_serve.txt', "Team 1")
    return render_template('scoreboard_overlay.html', team1_score=team1_score, team2_score=team2_score, team1_sets=team1_sets, team2_sets=team2_sets, team1_name=team1_name, team2_name=team2_name, team2_serve=team2_serve, team1_serve=team1_serve)



@app.route('/')
def index():
    team1_score = read_value('team1_score.txt', "0")
    team2_score = read_value('team2_score.txt', "0")
    team1_sets = read_value('team1_sets.txt', "0")
    team2_sets = read_value('team2_sets.txt', "0")
    team1_timeout = read_value('team1_timeout.txt', "0")
    team2_timeout = read_value('team2_timeout.txt', "0")
    team1_name = read_value('team1_name.txt', "Team 1")
    team2_name = read_value('team2_name.txt', "Team 2")

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scoreboard</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
        <header>
            <h1>Kollmann Media Scoreboard</h1>
        </header>

        <div class="container">
            <!-- Team 1 -->
            <div class="team" id="team1">
                <!-- Team Name Form -->
                <!-- Score and Sets Display -->
                <h2>{{ team1_name }}: <span id="team1_score">{{ team1_score }}</span> (Sätze Gewonnen <span id="team1_sets">{{ team1_sets }}</span>)</h2>
                <!-- Score Buttons -->
                <button class="button" onclick="updateScore('team1', 'increment')">Punkt +</button>
                <button class="button" onclick="updateScore('team1', 'decrement')">Storno -</button>

                <br/>
                <button class="button" onclick="triggerSetPoint('team1')">Satzball</button>
                <button class="button" onclick="triggerMatchPoint('team1')">Matchball</button>

                <!-- Timeout Display and Button -->
                <h3>Timeouts: <span id="team1_timeout">{{ team1_timeout }}</span></h3>
                <button class="button" onclick="triggerTimeout('team1')">Auszeit</button>
            </div>

            <!-- Team 2 -->
            <div class="team" id="team2">
                <!-- Team Name Form -->
                <!-- Score and Sets Display -->
                <h2>{{ team2_name }}: <span id="team2_score">{{ team2_score }}</span> (Sätze Gewonnen <span id="team2_sets">{{ team2_sets }}</span>)</h2>
                <!-- Score Buttons -->
                <button class="button" onclick="updateScore('team2', 'increment')">Punkt +</button>
                <button class="button" onclick="updateScore('team2', 'decrement')">Storno -</button>
                <br/>
                <button class="button" onclick="triggerSetPoint('team2')">Satzball</button>
                <button class="button" onclick="triggerMatchPoint('team2')">Matchball</button>
                <h3>Timeouts: <span id="team2_timeout">{{ team2_timeout }}</span></h3>
                <button class="button" onclick="triggerTimeout('team2')">Auszeit</button>


            </div>
            <div class="container">
                <!-- Hier fügen wir die Match Control Sektion hinzu -->
                <div class="match-control">
                    <h2>Match Control</h2>
                    <!-- Beispielschaltflächen -->
                    <button class="button" onclick="window.location.href='/match-end'">Match Ende</button>
                    <button class="button" onclick="window.location.href='/viewers'">Zuschauer Zahlen</button>
                    <button class="button" onclick="window.location.href='/match-settings'">Match-Einstellungen</button>
                </div>
            </div>
        </div>




    <script>
        function updateScore(team, action) {
            $.post('/update/' + team + '/' + action, function(data) {
                $('#'+team+'_score').text(data.score);
                $('#'+team+'_sets').text(data.sets);
            }).fail(function() {
                alert('Error: Could not update score');
            });
        }

        function toggleServe(team) {
            $.post('/toggle-serve/' + team, function() {
                // Optional: Fügen Sie hier Logik hinzu, um die Anzeige zu aktualisieren
            }).fail(function() {
                alert('Error: Could not toggle serve');
            });
        }

        function triggerTimeout(team) {
            $.post('/timeout/' + team, function(data) {
                $('#'+team+'_timeout').text(data.timeout);
            }).fail(function() {
                alert('Error: Could not trigger timeout');
            });
        }
        function triggerSetPoint(team) {
        $.post('/setpoint/' + team, function(data) {
            // Optional: Fügen Sie hier Logik hinzu, um die Anzeige zu aktualisieren
        }).fail(function() {
            alert('Error: Could not trigger set point');
        });
    }

    function triggerMatchPoint(team) {
        $.post('/matchpoint/' + team, function(data) {
            // Optional: Fügen Sie hier Logik hinzu, um die Anzeige zu aktualisieren
        }).fail(function() {
            alert('Error: Could not trigger match point');
        });
    }
            function matchControlFunction(action) {
            $.post('/match-control/' + action, function(data) {
                // Logik zur Aktualisierung der Benutzeroberfläche
            }).fail(function() {
                alert('Error: Could not perform match control action');
            });
        }
    function updateScore(team, action) {
    $.post('/update/' + team + '/' + action, function(data) {
        $('#' + team + '_score').text(data.score);
        $('#' + team + '_sets').text(data.sets);
        if (data.set_point) {
            // Anzeigen der Satzball-Benachrichtigung
            alert(team + ' hat Satzball!');
                // if (data.match_point) {
        //     alert(team + ' hat Matchball!');
        }
    }).fail(function() {
        alert('Error: Could not update score');
    });
}

    </script>
    ''', team1_score=team1_score, team2_score=team2_score, team1_sets=team1_sets, team2_sets=team2_sets, team1_timeout=team1_timeout, team2_timeout=team2_timeout, team1_name=team1_name, team2_name=team2_name)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)