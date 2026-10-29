from flask import Flask, render_template_string, request, redirect, url_for, flash, session, g
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key_fima1456'
DATABASE = 'events.db'

# --- БАЗА ДАННЫХ ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None: db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                coins INTEGER DEFAULT 0,
                total_earned INTEGER DEFAULT 0,
                total_spent INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount INTEGER, comment TEXT, date TEXT
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, date TEXT, info TEXT
            );
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT, event_id INTEGER, user_id INTEGER, status TEXT, reason TEXT
            );
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, text TEXT, date TEXT, admin_reply TEXT
            );
        ''')
        try:
            db.execute("INSERT INTO users (name, password, role) VALUES ('admin', 'fima1456', 'admin')")
            db.commit()
        except sqlite3.IntegrityError:
            pass

# --- HTML ШАБЛОНЫ ---
BASE_STYLE = """
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;700;900&display=swap" rel="stylesheet">
    <style>
        :root { 
            --primary: #6a11cb; 
            --secondary: #2575fc;
            --bg-grad: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            --panel: rgba(255, 255, 255, 0.9);
            --text: #2c3e50;
            --accent: #ff4757;
            --success: #2ed573;
            --danger: #ff4757;
        }
        body { 
            font-family: 'Montserrat', sans-serif; 
            background: var(--bg-grad);
            color: var(--text); 
            margin: 0; 
            padding: 20px; 
            display: flex; 
            justify-content: center; 
            min-height: 100vh;
        }
        .container { 
            width: 100%; 
            max-width: 1000px; 
            background: var(--panel); 
            padding: 30px; 
            border-radius: 20px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1); 
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.5);
            position: relative;
            overflow: hidden;
        }
        .container::before {
            content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 8px;
            background: linear-gradient(90deg, var(--primary), var(--secondary), var(--accent));
        }
        h1, h2, h3 { color: var(--primary); font-weight: 900; margin-top: 0; }
        
        input, select, textarea { 
            width: 100%; padding: 12px 15px; margin: 8px 0 15px 0; 
            background: #fff; border: 2px solid #e2e8f0; 
            color: #333; border-radius: 10px; box-sizing: border-box; 
            font-family: 'Montserrat'; font-weight: 500; transition: 0.3s; 
        }
        input:focus, select:focus, textarea:focus { 
            border-color: var(--secondary); outline: none; 
            box-shadow: 0 0 15px rgba(37, 117, 252, 0.2); 
        }
        
        button { 
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%); 
            color: white; border: none; 
            padding: 12px 20px; border-radius: 10px; cursor: pointer; 
            font-weight: 700; font-family: 'Montserrat'; transition: 0.3s; 
            width: 100%; box-shadow: 0 4px 15px rgba(106, 17, 203, 0.3);
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(106, 17, 203, 0.4); }
        button.danger { background: linear-gradient(135deg, #ff4757 0%, #ff6b81 100%); box-shadow: 0 4px 15px rgba(255, 71, 87, 0.3); }
        button.success { background: linear-gradient(135deg, #2ed573 0%, #7bed9f 100%); color: #fff; box-shadow: 0 4px 15px rgba(46, 213, 115, 0.3); }
        
        .card { 
            background: #fff; padding: 20px; border-radius: 15px; 
            margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border-left: 5px solid var(--primary);
        }
        .flex { display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }
        .flex > * { flex: 1; }
        
        .history-item { border-bottom: 1px solid #f1f2f6; padding: 12px 0; font-size: 14px; display: flex; justify-content: space-between;}
        .plus { color: var(--success); font-weight: 900; }
        .minus { color: var(--danger); font-weight: 900; }
        
        .tooltip { position: relative; display: inline-block; cursor: help; font-size: 13px; color: #7f8c8d; margin-bottom: 5px; width: 100%; text-align: left;}
        .tooltip .tooltiptext { 
            visibility: hidden; width: 220px; background-color: var(--text); color: #fff; 
            text-align: center; border-radius: 8px; padding: 10px; 
            position: absolute; z-index: 10; bottom: 130%; left: 50%; margin-left: -110px; 
            opacity: 0; transition: opacity 0.3s; font-size: 12px; 
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }
        
        .reply-box { background: #f8f9fa; padding: 10px; border-radius: 8px; border-left: 3px solid var(--accent); margin-top: 8px; font-size: 13px;}
        .badge { background: #e2e8f0; color: var(--primary); padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 800; }
        .badge-admin { background: #ffeaa7; color: #d63031; }
        
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 15px 10px; text-align: left; border-bottom: 1px solid #f1f2f6; }
        th { color: #b2bec3; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
    </style>
"""

LOGIN_HTML = """
<!DOCTYPE html><html><head><title>Вход</title>""" + BASE_STYLE + """</head><body>
<div class="container" style="max-width: 400px; margin-top: 10vh;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: var(--primary); font-size: 32px; text-shadow: 0 2px 10px rgba(106,17,203,0.2);">Roblox Events</h1>
        <p style="color: #7f8c8d; font-weight: 500;">Вход в личный кабинет</p>
    </div>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div style="background: #fff3f3; border: 1px solid var(--danger); padding: 10px; border-radius: 8px; margin-bottom: 15px; color: var(--danger); text-align: center; font-weight: 600;">
                    {{ message }}
                </div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <form method="POST">
        <div class="tooltip">Имя пользователя <span class="tooltiptext">Введите имя, которое выдал админ</span></div>
        <input type="text" name="name" placeholder="Ваше имя" required>
        
        <div class="tooltip">Пароль <span class="tooltiptext">Введите пароль, который выдал админ</span></div>
        <input type="password" name="password" placeholder="Ваш пароль" required>
        
        <button type="submit" style="margin-top: 15px;">Войти в систему</button>
    </form>
</div></body></html>
"""

USER_HTML = """
<!DOCTYPE html><html><head><title>Профиль</title>""" + BASE_STYLE + """</head><body>
<div class="container">
    <div class="flex" style="justify-content: space-between; background: #fff; padding: 20px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 2px solid var(--primary);">
        <div>
            <h1 style="margin: 0;">Профиль: {{ user['name'] }}</h1>
            <span class="badge badge-user" style="margin-top: 5px; display:inline-block;">Участник</span>
            <p style="margin: 15px 0 0 0; color: var(--primary); font-size: 22px; font-weight: 900;">💰 {{ user['coins'] }} коинов</p>
            <p style="margin: 5px 0 0 0; font-size: 13px; color: #7f8c8d; font-weight: 600;">
                Заработано: <span class="plus">+{{ user['total_earned'] }}</span> | Потрачено: <span class="minus">-{{ user['total_spent'] }}</span>
            </p>
        </div>
        <div>
            <a href="/logout" style="text-decoration: none;"><button class="danger" style="width: auto; padding: 10px 25px;">Выйти</button></a>
        </div>
    </div>
    
    <div class="flex" style="align-items: flex-start;">
        <!-- ЛЕВАЯ КОЛОНКА -->
        <div style="flex: 2;">
            <h3>🎉 Доступные эвенты</h3>
            {% for event in events %}
                <div class="card" style="border-left-color: var(--secondary);">
                    <h4 style="margin:0; color:var(--text); font-size: 18px;">{{ event['name'] }}</h4>
                    <p style="margin:5px 0; font-size:14px; color:var(--primary); font-weight: 700;">🕒 {{ event['date'] }}</p>
                    <p style="margin:0 0 15px 0; font-size:14px; color:#7f8c8d; font-weight: 500;">{{ event['info'] }}</p>
                    
                    {% set p = statuses.get(event['id']) %}
                    {% if p %}
                        {% if p['status'] == 'accepted' %}
                            <div style="background: rgba(46, 213, 115, 0.1); padding: 12px; border-radius: 8px; color: var(--success); font-weight: 700; text-align: center; border: 1px solid var(--success);">
                                ✅ Вы подтвердили участие!
                            </div>
                        {% elif p['status'] == 'declined' %}
                            <div style="background: rgba(255, 71, 87, 0.1); padding: 12px; border-radius: 8px; color: var(--danger); font-weight: 700; text-align: center; border: 1px solid var(--danger);">
                                ❌ Отказ. Причина: {{ p['reason'] }}
                            </div>
                        {% endif %}
                    {% else %}
                        <div class="flex" style="gap: 10px;">
                            <form method="POST" action="/event_respond/{{ event['id'] }}/accept" style="flex: 1;">
                                <button class="success" type="submit" style="width:100%;">✅ Приду</button>
                            </form>
                            <form method="POST" action="/event_respond/{{ event['id'] }}/decline" style="display:flex; gap:5px; flex: 1;">
                                <input type="text" name="reason" placeholder="Причина отказа" required style="margin:0; flex: 2;">
                                <button class="danger" type="submit" style="flex: 1;">❌ Не смогу</button>
                            </form>
                        </div>
                    {% endif %}
                </div>
            {% else %}
                <div class="card"><p style="color: #7f8c8d; font-weight: 600;">Пока нет активных эвентов. Ждите анонсов!</p></div>
            {% endfor %}
        </div>

        <!-- ПРАВАЯ КОЛОНКА -->
        <div style="flex: 1; margin-left: 15px;">
            <h3>🏆 Топ игроков</h3>
            <div class="card" style="border-left-color: var(--accent);">
                <ol style="margin:0; padding-left: 20px; font-size: 15px; font-weight: 600;">
                    {% for t in top_users %}
                        <li style="margin-bottom: 8px;">{{ t['name'] }} — <b class="plus">{{ t['coins'] }}</b></li>
                    {% endfor %}
                </ol>
            </div>

            <h3>📩 Запросы админу</h3>
            <div class="card">
                <form method="POST" action="/send_request">
                    <div class="tooltip">Текст запроса <span class="tooltiptext">Задайте вопрос или попросите роль</span></div>
                    <textarea name="text" rows="3" placeholder="Ваш вопрос..." required style="margin-bottom: 10px;"></textarea>
                    <button type="submit" style="font-size: 14px;">Отправить</button>
                </form>
                
                {% for r in my_requests %}
                    <div style="border-top:1px solid #f1f2f6; margin-top:15px; padding-top:10px; font-size:14px;">
                        <div style="font-weight: 600; color: var(--text);"><span style="color: var(--primary);">Вы:</span> {{ r['text'] }}</div>
                        {% if r['admin_reply'] %}
                            <div class="reply-box"><b>Админ:</b> {{ r['admin_reply'] }}</div>
                        {% else %}
                            <small style="color:#b2bec3; font-weight: 600; margin-top: 5px; display: block;">Ожидает ответа...</small>
                        {% endif %}
                    </div>
                {% endfor %}
            </div>

            <h3>📜 История</h3>
            <div class="card" style="max-height: 300px; overflow-y: auto;">
                {% for h in history %}
                    <div class="history-item">
                        <span class="{{ 'plus' if h['amount'] > 0 else 'minus' }}">{{ '+' if h['amount'] > 0 else '' }}{{ h['amount'] }}</span>
                        <span style="flex:2; margin-left: 10px; font-size:13px; color: #7f8c8d; font-weight: 600;">{{ h['comment'] }}</span>
                    </div>
                {% else %}
                    <p style="color: #b2bec3; font-weight: 600;">История пуста.</p>
                {% endfor %}
            </div>
        </div>
    </div>
</div></body></html>
"""

ADMIN_HTML = """
<!DOCTYPE html><html><head><title>Админка</title>""" + BASE_STYLE + """</head><body>
<div class="container" style="max-width: 1200px;">
    <div class="flex" style="justify-content: space-between; background: #fff; padding: 20px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 2px solid var(--accent);">
        <div>
            <h1 style="margin: 0; color: var(--accent);">Админ-Панель</h1>
            <span class="badge badge-admin">Главный администратор</span>
        </div>
        <div>
            <a href="/logout" style="text-decoration: none;"><button class="danger" style="width: auto; padding: 10px 25px;">Выйти</button></a>
        </div>
    </div>

    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div style="background: rgba(46, 213, 115, 0.1); border: 1px solid var(--success); padding: 12px; border-radius: 8px; margin-bottom: 15px; color: var(--success); font-weight: 700;">
                    {{ message }}
                </div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    <div class="flex" style="align-items: flex-start;">
        <div style="flex: 1;">
            <div class="card" style="border-left-color: var(--success);">
                <h3>👤 Создать профиль</h3>
                <form method="POST" action="/admin/create_user">
                    <div class="tooltip">Имя <span class="tooltiptext">Отображаемое имя (рус/англ)</span></div>
                    <input type="text" name="name" placeholder="Никнейм" required>
                    
                    <div class="tooltip">Пароль <span class="tooltiptext">Пароль для входа участника</span></div>
                    <input type="text" name="password" placeholder="Пароль" required>
                    
                    <button class="success" type="submit">Создать профиль</button>
                </form>
            </div>

            <div class="card" style="border-left-color: var(--primary);">
                <h3>🎉 Создать эвент</h3>
                <form method="POST" action="/admin/create_event">
                    <div class="tooltip">Название <span class="tooltiptext">Например: Гонки в Брукхейвене</span></div>
                    <input type="text" name="name" placeholder="Название" required>
                    
                    <div class="tooltip">Дата и время <span class="tooltiptext">Например: 28.10 в 19:00</span></div>
                    <input type="text" name="date" placeholder="Время" required>
                    
                    <div class="tooltip">Информация <span class="tooltiptext">Где собираемся, что делать и т.д.</span></div>
                    <input type="text" name="info" placeholder="Доп. инфа">
                    
                    <button type="submit">Создать эвент</button>
                </form>
            </div>

            <div class="card" style="border-left-color: var(--accent);">
                <h3>💸 Массовое начисление</h3>
                <form method="POST" action="/admin/give_all">
                    <div class="tooltip">Сумма <span class="tooltiptext">Введите 300 для начисления или -100 для списания</span></div>
                    <input type="number" step="any" name="amount" placeholder="Сумма (+/-)" required>
                    
                    <div class="tooltip">Комментарий <span class="tooltiptext">За что начисляем (увидит юзер)</span></div>
                    <input type="text" name="comment" placeholder="Комментарий" required>
                    
                    <button type="submit">Начислить всем</button>
                </form>
            </div>
        </div>

        <div style="flex: 2; margin-left: 15px;">
            <div class="card">
                <h3>💰 Начислить / Списать коины</h3>
                <form method="POST" action="/admin/give_coins" class="flex">
                    <select name="user_id" required style="flex:2; margin: 0;">
                        {% for u in users %}
                            <option value="{{ u['id'] }}">{{ u['name'] }} ({{ u['coins'] }})</option>
                        {% endfor %}
                    </select>
                    <input type="number" step="any" name="amount" placeholder="Сумма (+/-)" required style="flex:1; margin: 0;">
                    <input type="text" name="comment" placeholder="За что" required style="flex:2; margin: 0;">
                    <button type="submit" style="flex:1; margin: 0; padding: 12px 10px;">Применить</button>
                </form>
            </div>

            <h3>📩 Запросы от участников</h3>
            <div class="card" style="max-height: 250px; overflow-y: auto;">
                {% for r in requests %}
                    <div style="border-bottom: 1px solid #f1f2f6; padding: 10px 0;">
                        <b style="color: var(--primary);">{{ r['name'] }}</b> <small>({{ r['date'] }})</small>
                        <p style="margin:5px 0; font-weight: 600;">{{ r['text'] }}</p>
                        <form method="POST" action="/admin/reply_request/{{ r['id'] }}" class="flex" style="gap: 5px;">
                            <input type="text" name="reply" placeholder="Ответ" style="margin:0;">
                            <button type="submit" class="success" style="flex: 1; padding: 8px;">Ответить</button>
                            <button type="submit" class="danger" formaction="/admin/delete_request/{{ r['id'] }}" formnovalidate style="flex: 1; padding: 8px;">Удалить</button>
                        </form>
                    </div>
                {% else %}
                    <p style="color: #b2bec3; font-weight: 600;">Нет активных запросов.</p>
                {% endfor %}
            </div>
        </div>
    </div>

    <h3 style="margin-top: 30px;">Управление пользователями</h3>
    <table>
        <tr><th>Имя</th><th>Баланс</th><th>Получено</th><th>Действия</th></tr>
        {% for u in users %}
        <tr>
            <td style="font-weight: 700;">{{ u['name'] }}</td>
            <td style="color:var(--primary); font-weight: 900;">{{ u['coins'] }}</td>
            <td class="plus">{{ u['total_earned'] }}</td>
            <td>
                <form method="POST" action="/admin/delete_user/{{ u['id'] }}" style="display:inline;" onsubmit="return confirm('Удалить юзера?');">
                    <button class="danger" style="padding:6px 12px; font-size:12px; width: auto;">Удалить</button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </table>

    <!-- СПИСКИ УЧАСТНИКОВ -->
    <h3 style="margin-top: 30px;">🎉 Управление эвентами и списки участников</h3>
    {% for e in events %}
    <div class="card" style="border-left-color: var(--secondary); margin-bottom: 15px;">
        <div class="flex" style="justify-content: space-between; margin-bottom: 10px;">
            <div>
                <h4 style="margin: 0; font-size: 18px;">{{ e['name'] }}</h4>
                <p style="margin: 5px 0; color: var(--primary); font-weight: 600;">🕒 {{ e['date'] }}</p>
            </div>
            <form method="POST" action="/admin/delete_event/{{ e['id'] }}" style="display:inline;" onsubmit="return confirm('Удалить эвент?');">
                <button class="danger" style="padding:6px 12px; font-size:12px; width: auto;">Удалить эвент</button>
            </form>
        </div>

        <div class="flex" style="align-items: flex-start; gap: 20px; margin-top: 15px;">
            <!-- ТЕ, КТО ПРИДЕТ -->
            <div style="flex: 1; background: rgba(46, 213, 115, 0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(46, 213, 115, 0.3);">
                <h5 style="margin: 0 0 10px 0; color: var(--success);">✅ Придут ({{ e['accepted_list']|length }})</h5>
                <ul style="margin: 0; padding-left: 20px; font-weight: 600;">
                    {% for p in e['accepted_list'] %}
                        <li>{{ p['name'] }}</li>
                    {% else %}
                        <li style="color: gray; font-weight: 400;">Пока никто</li>
                    {% endfor %}
                </ul>
            </div>

            <!-- ТЕ, КТО ОТКАЗАЛСЯ -->
            <div style="flex: 1; background: rgba(255, 71, 87, 0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255, 71, 87, 0.3);">
                <h5 style="margin: 0 0 10px 0; color: var(--danger);">❌ Отказались ({{ e['declined_list']|length }})</h5>
                <ul style="margin: 0; padding-left: 20px; font-weight: 600;">
                    {% for p in e['declined_list'] %}
                        <li>{{ p['name'] }} <span style="font-size: 12px; color: gray; font-weight: 400;">(Причина: {{ p['reason'] }})</span></li>
                    {% else %}
                        <li style="color: gray; font-weight: 400;">Пока никто</li>
                    {% endfor %}
                </ul>
            </div>
            
            <!-- ТЕ, КТО ЕЩЕ НЕ ОТВЕТИЛ -->
            <div style="flex: 1; background: rgba(0, 0, 0, 0.03); padding: 15px; border-radius: 10px; border: 1px solid rgba(0, 0, 0, 0.1);">
                <h5 style="margin: 0 0 10px 0; color: gray;">⏳ Не ответили ({{ e['pending_list']|length }})</h5>
                <ul style="margin: 0; padding-left: 20px; font-weight: 600; color: gray;">
                    {% for p in e['pending_list'] %}
                        <li>{{ p['name'] }}</li>
                    {% else %}
                        <li style="color: gray; font-weight: 400;">Все ответили</li>
                    {% endfor %}
                </ul>
            </div>
        </div>
    </div>
    {% endfor %}

    <h3 style="margin-top: 30px;">Последние операции по коинам</h3>
    <div class="card" style="max-height: 250px; overflow-y: auto;">
        {% for h in global_history %}
            <div class="history-item">
                <b style="color: var(--primary);">{{ h['name'] }}</b>: 
                <span class="{{ 'plus' if h['amount'] > 0 else 'minus' }}">{{ '+' if h['amount'] > 0 else '' }}{{ h['amount'] }}</span> 
                — <span style="color: #7f8c8d; font-weight: 500;">{{ h['comment'] }}</span> 
                <small style="color:#b2bec3; float:right;">{{ h['date'] }}</small>
            </div>
        {% endfor %}
    </div>
</div></body></html>
"""

# --- МАРШРУТЫ ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE name = ? AND password = ?', (name, password)).fetchone()
        
        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            if user['role'] == 'admin':
                return redirect(url_for('admin'))
            return redirect(url_for('profile'))
        else:
            flash('Неверное имя или пароль!', 'error')
            
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if 'user_id' not in session or session.get('role') == 'admin': return redirect(url_for('login'))
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    events = db.execute('SELECT * FROM events').fetchall()
    history = db.execute('SELECT * FROM history WHERE user_id = ? ORDER BY id DESC', (user['id'],)).fetchall()
    my_requests = db.execute('SELECT * FROM requests WHERE user_id = ? ORDER BY id DESC', (user['id'],)).fetchall()
    top_users = db.execute('SELECT name, coins FROM users WHERE role != "admin" ORDER BY coins DESC LIMIT 5').fetchall()
    
    parts = db.execute('SELECT * FROM participants WHERE user_id = ?', (user['id'],)).fetchall()
    statuses = {p['event_id']: p for p in parts}
    
    return render_template_string(USER_HTML, user=user, events=events, history=history, statuses=statuses, top_users=top_users, my_requests=my_requests)

@app.route('/event_respond/<int:event_id>/<action>', methods=['POST'])
def event_respond(event_id, action):
    if 'user_id' not in session or session.get('role') == 'admin': return redirect(url_for('login'))
    db = get_db()
    p = db.execute('SELECT * FROM participants WHERE event_id = ? AND user_id = ?', (event_id, session['user_id'])).fetchone()
    
    if action == 'accept':
        if p: db.execute('UPDATE participants SET status="accepted", reason="" WHERE id=?', (p['id'],))
        else: db.execute('INSERT INTO participants (event_id, user_id, status) VALUES (?, ?, "accepted")', (event_id, session['user_id']))
    elif action == 'decline':
        reason = request.form.get('reason', 'Без причины')
        if p: db.execute('UPDATE participants SET status="declined", reason=? WHERE id=?', (reason, p['id']))
        else: db.execute('INSERT INTO participants (event_id, user_id, status, reason) VALUES (?, ?, "declined", ?)', (event_id, session['user_id'], reason))
    db.commit()
    return redirect(url_for('profile'))

@app.route('/send_request', methods=['POST'])
def send_request():
    if 'user_id' not in session or session.get('role') == 'admin': return redirect(url_for('login'))
    text = request.form.get('text')
    if text:
        db = get_db()
        db.execute('INSERT INTO requests (user_id, text, date) VALUES (?, ?, ?)', (session['user_id'], text, datetime.now().strftime("%d.%m.%Y %H:%M")))
        db.commit()
        flash('Запрос отправлен!', 'success')
    return redirect(url_for('profile'))

# --- АДМИНКА ---
@app.route('/admin')
def admin():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    db = get_db()
    
    users_raw = db.execute('SELECT * FROM users').fetchall()
    users = [dict(u) for u in users_raw]
    
    # Получаем обычных юзеров для блока "Не ответили"
    normal_users = [u for u in users if u['role'] != 'admin']
    
    events_raw = db.execute('SELECT * FROM events ORDER BY id DESC').fetchall()
    events = []
    
    for e in events_raw:
        ev_dict = dict(e)
        
        # Получаем всех, кто ответил на этот эвент
        parts = db.execute('''SELECT p.status, p.reason, u.name 
                              FROM participants p 
                              JOIN users u ON p.user_id = u.id 
                              WHERE p.event_id = ?''', (e['id'],)).fetchall()
        
        accepted = []
        declined = []
        responded_names = []
        
        # Разделяем на согласившихся и отказавшихся
        for p in parts:
            responded_names.append(p['name'])
            if p['status'] == 'accepted':
                accepted.append({'name': p['name']})
            elif p['status'] == 'declined':
                declined.append({'name': p['name'], 'reason': p['reason']})
        
        # Вычисляем тех, кто не ответил (все юзеры минус ответившие)
        pending = []
        for u in normal_users:
            if u['name'] not in responded_names:
                pending.append({'name': u['name']})
                
        ev_dict['accepted_list'] = accepted
        ev_dict['declined_list'] = declined
        ev_dict['pending_list'] = pending
        
        events.append(ev_dict)

    requests_raw = db.execute('SELECT r.*, u.name FROM requests r JOIN users u ON r.user_id = u.id ORDER BY r.id DESC').fetchall()
    requests = [dict(r) for r in requests_raw]
    
    global_history_raw = db.execute('SELECT h.*, u.name FROM history h JOIN users u ON h.user_id = u.id ORDER BY h.id DESC LIMIT 50').fetchall()
    global_history = [dict(h) for h in global_history_raw]
    
    return render_template_string(ADMIN_HTML, users=users, requests=requests, events=events, global_history=global_history)

@app.route('/admin/create_user', methods=['POST'])
def admin_create_user():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    name = request.form.get('name')
    password = request.form.get('password')
    db = get_db()
    try:
        db.execute('INSERT INTO users (name, password) VALUES (?, ?)', (name, password))
        db.commit()
        flash(f'Профиль {name} создан!', 'success')
    except sqlite3.IntegrityError:
        flash('Ошибка: имя занято.', 'error')
    return redirect(url_for('admin'))

@app.route('/admin/give_coins', methods=['POST'])
def admin_give_coins():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    user_id = request.form.get('user_id')
    try:
        amount = int(float(request.form.get('amount')))
    except ValueError:
        flash('Ошибка: неверный формат суммы.', 'error')
        return redirect(url_for('admin'))
        
    comment = request.form.get('comment')
    db = get_db()
    
    if amount > 0:
        db.execute('UPDATE users SET coins = coins + ?, total_earned = total_earned + ? WHERE id = ?', (amount, amount, user_id))
    else:
        db.execute('UPDATE users SET coins = coins + ?, total_spent = total_spent + ? WHERE id = ?', (amount, abs(amount), user_id))
        
    db.execute('INSERT INTO history (user_id, amount, comment, date) VALUES (?, ?, ?, ?)', (user_id, amount, comment, datetime.now().strftime("%d.%m.%Y %H:%M")))
    db.commit()
    flash(f'Успешно изменено на {amount}!', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/give_all', methods=['POST'])
def admin_give_all():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    try:
        amount = int(float(request.form.get('amount')))
    except ValueError:
        flash('Ошибка: неверный формат суммы.', 'error')
        return redirect(url_for('admin'))
        
    comment = request.form.get('comment')
    db = get_db()
    
    users = db.execute('SELECT id FROM users WHERE role != "admin"').fetchall()
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    for u in users:
        if amount > 0:
            db.execute('UPDATE users SET coins = coins + ?, total_earned = total_earned + ? WHERE id = ?', (amount, amount, u['id']))
        else:
            db.execute('UPDATE users SET coins = coins + ?, total_spent = total_spent + ? WHERE id = ?', (amount, abs(amount), u['id']))
        db.execute('INSERT INTO history (user_id, amount, comment, date) VALUES (?, ?, ?, ?)', (u['id'], amount, comment, now))
    
    db.commit()
    flash(f'Всем начислено по {amount}!', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/create_event', methods=['POST'])
def admin_create_event():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    db = get_db()
    db.execute('INSERT INTO events (name, date, info) VALUES (?, ?, ?)', (request.form['name'], request.form['date'], request.form['info']))
    db.commit()
    flash('Эвент создан!', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/reply_request/<int:req_id>', methods=['POST'])
def admin_reply_request(req_id):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    reply = request.form.get('reply')
    db = get_db()
    if reply:
        db.execute('UPDATE requests SET admin_reply = ? WHERE id = ?', (reply, req_id))
        db.commit()
    return redirect(url_for('admin'))

@app.route('/admin/delete_request/<int:req_id>', methods=['POST'])
def admin_delete_request(req_id):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    db = get_db()
    db.execute('DELETE FROM requests WHERE id = ?', (req_id,))
    db.commit()
    return redirect(url_for('admin'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    db = get_db()
    db.execute('DELETE FROM users WHERE id = ? AND role != "admin"', (user_id,))
    db.execute('DELETE FROM history WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM participants WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM requests WHERE user_id = ?', (user_id,))
    db.commit()
    flash('Пользователь удален.', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/delete_event/<int:event_id>', methods=['POST'])
def admin_delete_event(event_id):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    db = get_db()
    db.execute('DELETE FROM events WHERE id = ?', (event_id,))
    db.execute('DELETE FROM participants WHERE event_id = ?', (event_id,))
    db.commit()
    flash('Эвент удален.', 'success')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
