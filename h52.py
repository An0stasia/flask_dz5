from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask import Flask, render_template, request, redirect, url_for


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///result_test.db'
db = SQLAlchemy(app)

#создаем классы в нашей базе данных, которые будут включать информацию про пользователя,вопросы и собственнно ответы на вопросы
class User(db.Model):
    __tablename__ = "user"

    user_id = db.Column('user_id', db.Integer, primary_key=True)
    user_age = db.Column('user_age', db.Integer)
    user_gender = db.Column('user_gender', db.Integer)


class Questions(db.Model):
    __tablename__ = "questions"

    question_id = db.Column('question_id', db.Integer, primary_key=True)
    question_text = db.Column('question_text', db.Text, unique=True)


class Answers(db.Model):
    __tablename__ = "answers"

    answer_id = db.Column('answer_id', db.Integer, primary_key=True)
    q1 = db.Column('anwer_1', db.Integer)
    q2 = db.Column('anwer_2', db.Text)
    q3 = db.Column('anwer_3', db.Integer)
    q4 = db.Column('anwer_4', db.Integer)
    q5 = db.Column('anwer_5', db.Integer)
    q6 = db.Column('anwer_6', db.Text)
    q7 = db.Column('anwer_7', db.Integer)


db.init_app(app) #эта штука нужна для правильной работы app.app_context

#этот цикл открывает файл с вопросами, которые нужны для блоков в html коде
with app.app_context():
    try:
        db.create_all()
        with open('Questions.txt', 'r', encoding='UTF-8') as questions_file:
            for stroka in questions_file:
                stroka_new = stroka[:-1]
                question = Questions(question_text=stroka_new)
                db.session.add(question)
                db.session.commit()
    except:
        pass

#собственно дальше прописаны страницы, ничего особенного (/index нужен в случае того, если пользователь захочет перейти на какие-то другие страницы)
@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/base')
def base():
    return render_template('base.html')


@app.route('/anketa')
def anketa():
    questions = Questions.query.all()

    return render_template(
        'anketa-2.html',
        questions=questions
    )


@app.route('/process', methods=['get'])
def answer_anketa():
    # если нет ответов, то отсылаем решать анкету
    if not request.args:
        return redirect(url_for('anketa'))

    # достаем параметры, у меня их не очень много (нет домена, имени, фамилии пользователя), потому что опрос анонимный и мб я себе так облегчила жизнь
    user_age = request.args.get('age')
    user_gender = request.args.get('gender')

    # создаем профиль пользователя
    user = User(
        user_age=user_age,
        user_gender=user_gender,
    )

    # добавляем в базу, сохраняем и получаем юзера с айди
    db.session.add(user)
    db.session.commit()
    db.session.refresh(user)

    # получаем семь ответов на все мои недовопросы
    q1 = request.args.get('q1')
    q2 = request.args.get('q2')
    q3 = request.args.get('q3')
    q4 = request.args.get('q4')
    q5 = request.args.get('q5')
    q6 = request.args.get('q6')
    q7 = request.args.get('q7')

    # привязываем ответы к пользователю, добавляем их в базу и сохраняем
    answer = Answers(answer_id=user.user_id, q1=q1, q2=q2, q3=q3, q4=q4, q5=q5, q6=q6, q7=q7)
    db.session.add(answer)
    db.session.commit()

    return render_template('Ok.html') #если все ок и все сохранилось, то перенаправляем пользователя на страницу /process


@app.route('/statistics')
def statistics():
    all_stat = {}
    age_stats = db.session.query(
        func.avg(User.user_age),
        func.min(User.user_age),
        func.max(User.user_age)
    ).one()
    #это все функции для статистики возраста
    all_stat['age_mean'] = age_stats[0]
    all_stat['age_min'] = age_stats[1]
    all_stat['age_max'] = age_stats[2]
    all_stat['total_count'] = User.query.count()

    #здесь я прописала цикл, который сначала достает мне все значения в user_gender, а потом уже соответсвенно считает сколько кого
    all_people = db.session.query(User.user_gender).all()
    count_men = 0
    count_women = 0
    for person in all_people:
        for per in person:
            if per == 'male':
                count_men += 1
            if per == 'female':
                count_women += 1
    all_stat['male'] = count_men
    all_stat['female'] = count_women

    #абсолютно такой же цикл, что и до этого, но теперь он считает сколько лингвистов/нелингвистов, где high-это лингвист, low-недолингвист, none-не лингвист
    all_linguist = db.session.query(Answers.q1).all()
    count_linguist = 0
    count_ling = 0
    count_notling = 0
    for lg in all_linguist:
        for l in lg:
            if l == 'high':
                count_linguist += 1
            if l == 'low':
                count_ling += 1
            if l == 'none':
                count_notling += 1
    all_stat['high'] = count_linguist
    all_stat['low'] = count_ling
    all_stat['none'] = count_notling

    #достаем вопросы, чтобы потом посчитать среднее значение "нормальности" их звучания
    questions = Questions.query.all()

    #здесь такой блок который собственно и считает среднее значение, нверное это можно было как-то в цикл преобразовать, но вроде и так норм, потому что у меня не так то много вопросов
    all_stat['q2_mean'] = db.session.query(func.avg(Answers.q2)).one()[0]
    q2_answers = db.session.query(Answers.q2).all()
    all_stat['q3_mean'] = db.session.query(func.avg(Answers.q3)).one()[0]
    q3_answers = db.session.query(Answers.q3).all()
    all_stat['q4_mean'] = db.session.query(func.avg(Answers.q4)).one()[0]
    q4_answers = db.session.query(Answers.q4).all()
    all_stat['q5_mean'] = db.session.query(func.avg(Answers.q5)).one()[0]
    q5_answers = db.session.query(Answers.q5).all()
    all_stat['q6_mean'] = db.session.query(func.avg(Answers.q6)).one()[0]
    q6_answers = db.session.query(Answers.q6).all()
    all_stat['q7_mean'] = db.session.query(func.avg(Answers.q7)).one()[0]
    q7_answers = db.session.query(Answers.q7).all()

    return render_template('statistics.html', all_stat=all_stat,  questions=questions)

#торжественно запускаем наш сайт
if __name__ == '__main__':
    app.run()