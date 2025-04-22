from flask import Flask, render_template, request, redirect, url_for, session
from openai_api import analyze_response_dynamic, finalize_with_followup, generate_summary_report
from get_user_percentiles import generate_user_report
import json
from flask_session import Session

app = Flask(__name__)
app.secret_key = 'supersecretkey'

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR']  = './.flask_session/'
app.config['SESSION_PERMANENT'] = False

Session(app)

with open("questions.json", "r") as f:
    QUESTIONS = json.load(f)

@app.route('/')
def index():
    session.clear()
    session['results'] = {}
    session['q_index'] = 0
    return render_template('index.html')

@app.route('/question', methods=['GET', 'POST'])
def question():
    index = session.get('q_index', 0)
    results = session.get('results', {})

    if request.method == 'POST':
        user_input = request.form['response']
        q = QUESTIONS[index]
        result = analyze_response_dynamic(q['text'], user_input)

        followup = None
        followup_input = None

        if "followup" in result:
            followup = result["followup"]
            return render_template('question.html', q=q, followup=followup, user_input=user_input)

        score = result['score']
        insight = result['insight']

        results[q["id"]] = {
            "trait": q["trait"],
            "question": q["text"],
            "response": user_input,
            "followup": None,
            "followup_response": None,
            "score": score,
            "insight": insight
        }

        session['results'] = results
        session['q_index'] = index + 1
        return redirect(url_for('question'))

    elif request.args.get('followup_response'):
        followup_input = request.args.get('followup_response')
        user_input = request.args.get('user_input')
        followup = request.args.get('followup')
        q = QUESTIONS[index]

        final = finalize_with_followup(q['text'], user_input, followup, followup_input)


        results[q["id"]] = {
            "trait": q["trait"],
            "question": q["text"],
            "response": user_input,
            "followup": followup,
            "followup_response": followup_input,
            "score": final["score"],
            "insight": final["insight"]
        }

        session['results'] = results
        session['q_index'] = index + 1
        return redirect(url_for('question'))

    elif index < len(QUESTIONS):
        q = QUESTIONS[index]
        return render_template('question.html', q=q, followup=None)

    else:
        with open("user_results.json", "w") as f:
            json.dump(results, f, indent=2)
        return redirect(url_for('results'))

@app.route('/results')
def results():
    results = session.get('results', {})

    if not results:
        try:
            with open("user_results.json") as f:
                results = json.load(f)
        except FileNotFoundError:
            return redirect(url_for('index'))

    report_data = generate_user_report(results)
    summary     = generate_summary_report(results, report_data)

    return render_template('result.html',
                           report=report_data,
                           summary=summary)

