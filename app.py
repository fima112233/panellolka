from flask import Flask, render_template_string, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import os
import time

app = Flask(__name__)
app.secret_key = 'super_secret_key_fima1456'

DB = {
    "users": {
        "admin": {"password": "fima1456", "role": "admin", "coins": 0, "earned": 0, "spent": 0, "banned": False, "inflation_msg": "", "last_click": 0}
    },
    "history": [],
    "events": [],
    "responses": [],
    "custom_requests": [], 
    "shop": [
        {"id": 1, "name": "Роль @Админ", "desc": "Дает полные права на сервере Lolka", "price": 1200}
    ],
    "role_requests": [], 
    "inventory": []
}

BASE_STYLE = """
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;700;900&display=swap" rel="stylesheet">
    <style>
        :root { 
            --primary: #6a11cb; --secondary: #2575fc;
            --bg-grad: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            --panel: rgba(255, 255, 255, 0.95); --text: #2c3e50;
            --accent: #ff4757; --success: #2ed573; --danger: #ff4757; --warn: #f1c40f;
            --input-bg: #fff; --input-border: #e2e8f0;
        }
        body.dark-theme {
            --bg-grad: linear-gradient(135deg, #1e1e2f 0%, #2a2a40 100%);
            --panel: rgba(30, 30, 47, 0.95); --text: #e2e8f0;
            --input-bg: #2a2a40; --input-border: #4a4a6a;
        }
        body { font-family: 'Montserrat', sans-serif; background: var(--bg-grad); color: var(--text); margin: 0; padding: 20px; display: flex; justify-content: center; min-height: 100vh; transition: background 0.3s; }
        .container { width: 100%; max-width: 1100px; background: var(--panel); padding: 30px; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); position: relative; overflow: hidden; transition: 0.3s; }
        .container::before { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 8px; background: linear-gradient(90deg, var(--primary), var(--secondary), var(--accent)); }
        h1, h2, h3, h4 { color: var(--primary); font-weight: 900; margin-top: 0; }
        body.dark-theme h1, body.dark-theme h2, body.dark-theme h3, body.dark-theme h4 { color: #a29bfe; }
        
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; border-bottom: 2px solid var(--input-border); padding-bottom: 10px; flex-wrap: wrap; }
        .tab-link { text-decoration: none; color: var(--text); font-weight: 700; padding: 10px 20px; border-radius: 10px; transition: 0.3s; background: var(--input-bg); border: 2px solid var(--input-border); }
        .tab-link:hover { border-color: var(--primary); color: var(--primary); }
        .tab-link.active { background: var(--primary); color: #fff; border-color: var(--primary); box-shadow: 0 4px 15px rgba(106, 17, 203, 0.3); }

        input, select, textarea { width: 100%; padding: 12px 15px; margin: 8px 0 15px 0; background: var(--input-bg); border: 2px solid var(--input-border); color: var(--text); border-radius: 10px; box-sizing: border-box; font-family: 'Montserrat'; font-weight: 500; transition: 0.3s; }
        input:focus, select:focus, textarea:focus { border-color: var(--secondary); outline: none; box-shadow: 0 0 15px rgba(37, 117, 252, 0.2); }
        
        button { background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%); color: white; border: none; padding: 12px 20px; border-radius: 10px; cursor: pointer; font-weight: 700; font-family: 'Montserrat'; transition: 0.3s; width: 100%; box-shadow: 0 4px 15px rgba(106, 17, 203, 0.3); }
        button:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(106, 17, 203, 0.4); }
        button.danger { background: linear-gradient(135deg, #ff4757 0%, #ff6b81 100%); box-shadow: 0 4px 15px rgba(255, 71, 87, 0.3); }
        button.success { background: linear-gradient(135deg, #2ed573 0%, #7bed9f 100%); color: #fff; box-shadow: 0 4px 15px rgba(46, 213, 115, 0.3); }
        button.warn { background: linear-gradient(135deg, #f1c40f 0%, #f39c12 100%); color: #fff; box-shadow: 0 4px 15px rgba(241, 196, 15, 0.3); }
        button.blue { background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3); }
        
        .clicker-btn { background: radial-gradient(circle, #ff9a9e 0%, #fecfef 99%, #fecfef 100%); color: #c0392b; font-size: 24px; font-weight: 900; border-radius: 50%; width: 150px; height: 150px; margin: 0 auto; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 10px 25px rgba(255, 107, 129, 0.5); transition: transform 0.1s; border: 4px solid #fff; }
        .clicker-btn:active { transform: scale(0.95); }
        .clicker-btn:hover { filter: brightness(1.05); }

        .card { background: var(--panel); padding: 20px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 5px solid var(--primary); }
        .flex { display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }
        .flex > * { flex: 1; }
        
        .history-item { border-bottom: 1px solid var(--input-border); padding: 12px 0; font-size: 14px; display: flex; justify-content: space-between;}
        .plus { color: var(--success); font-weight: 900; }
        .minus { color: var(--danger); font-weight: 900; }
        
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 15px 10px; text-align: left; border-bottom: 1px solid var(--input-border); }
        th { color: #b2bec3; font-weight: 700; font-size: 12px; text-transform: uppercase; }
        
        .theme-toggle { position: absolute; top: 20px; right: 20px; background: none; border: 2px solid var(--primary); color: var(--primary); width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; cursor: pointer; box-shadow: none; z-index: 10; padding: 0;}
        .theme-toggle:hover { background: var(--primary); color: #fff; transform: scale(1.1); }
        
        .avatar { width: 60px; height: 60px; border-radius: 50%; background: linear-gradient(135deg, var(--primary), var(--secondary)); display: flex; align-items: center; justify-content: center; color: white; font-size: 24px; font-weight: 900; }
        
        #toast-container { position: fixed; top: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 10px; }
        .toast { background: var(--panel); color: var(--text); padding: 15px 20px; border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); border-left: 5px solid var(--primary); font-weight: 700; font-size: 14px; opacity: 0; transform: translateX(100%); transition: all 0.3s ease; display: flex; align-items: center; gap: 10px; }
        .toast.show { opacity: 1; transform: translateX(0); }
        .toast.success { border-left-color: var(--success); }
        .toast.error { border-left-color: var(--danger); }
        .toast-close { margin-left: auto; cursor: pointer; font-size: 18px; opacity: 0.5; }
        .toast-close:hover { opacity: 1; }
    </style>
    <script>
        function toggleTheme() { document.body.classList.toggle('dark-theme'); const isDark = document.body.classList.contains('dark-theme'); localStorage.setItem('theme', isDark ? 'dark' : 'light'); document.getElementById('themeBtn').innerText = isDark ? '☀️' : '🌙'; }
        document.addEventListener('DOMContentLoaded', () => { if (localStorage.getItem('theme') === 'dark') { document.body.classList.add('dark-theme'); document.getElementById('themeBtn').innerText = '☀️'; } });

        function showToast(message, category) {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast ${category}`;
            toast.innerHTML = `<span>${message}</span><span class="toast-close" onclick="this.parentElement.remove()">×</span>`;
            container.appendChild(toast);
            setTimeout(() => toast.classList.add('show'), 10);
            setTimeout(() => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 300); }, 4000);
        }

        let lastClickTime = 0;
        function doClick() {
            const now = Date.now();
            if (now - lastClickTime < 200) return; 
            lastClickTime = now;
            fetch('/api/click', { method: 'POST' }).then(res => res.json()).then(data => {
                if (data.success) {
                    const coinEl = document.getElementById('coin-display');
                    if (coinEl) coinEl.innerText = data.new_balance.toFixed(2);
                } else {
                    showToast(data.message, "error");
                }
            });
        }
    </script>
"""

def get_layout(content):
    return f"""<!DOCTYPE html><html><head><title>Roblox Events</title>{BASE_STYLE}</head>
    <body>
        <div id="toast-container"></div>
        <button id="themeBtn" class="theme-toggle" onclick="toggleTheme()">🌙</button>
        {content}
    </body></html>"""
LOGIN_CONTENT = """
<div class="container" style="max-width: 400px; margin-top: 10vh;">
    <div style="text-align: center; margin-bottom: 30px;"><h1 style="color: var(--primary); font-size: 32px;">Roblox Events</h1></div>
    <form method="POST">
        <input type="text" name="name" placeholder="Ваше имя" required>
        <input type="password" name="password" placeholder="Пароль" required>
        <button type="submit" style="margin-top: 15px;">Войти</button>
    </form>
</div>
"""

USER_CONTENT = """
<div class="container">
    {% if user.get('inflation_msg') %}
        <div style="background: rgba(241, 196, 15, 0.2); border: 2px solid var(--warn); padding: 15px; border-radius: 10px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: 700; color: #d35400;">⚠️ {{ user['inflation_msg'] }}</span>
            <form method="POST" action="/dismiss_inflation" style="margin: 0;"><button class="warn" style="padding: 5px 15px; width: auto; font-size: 12px;">Прочитано</button></form>
        </div>
    {% endif %}

    {% if user['coins'] < 0 %}
        <div style="background: rgba(255, 71, 87, 0.2); border: 2px solid var(--danger); padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align: center; font-weight: 800; color: var(--danger);">
            ⚠️ ВНИМАНИЕ! Ваш баланс отрицательный ({{ "%.2f"|format(user['coins']) }}). Запись на эвенты заблокирована.
        </div>
    {% endif %}

    <div class="flex" style="justify-content: space-between; background: var(--input-bg); padding: 20px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 2px solid var(--primary);">
        <div style="display: flex; align-items: center; gap: 15px;">
            <div class="avatar">{{ user_name[0]|upper }}</div>
            <div>
                <h1 style="margin: 0; font-size: 24px;">{{ user_name }}</h1>
                <span style="font-size:12px; color:gray; font-weight:700;">Уровень {{ level }} — {{ rank_name }}</span>
                <p style="margin: 5px 0 0 0; color: var(--primary); font-size: 20px; font-weight: 900;">💰 <span id="coin-display">{{ "%.2f"|format(user['coins']) }}</span> коинов</p>
            </div>
        </div>
        <div style="text-align: right;">
            <form method="POST" action="/claim_daily" style="margin-bottom: 10px;">
                <button class="warn" style="font-size: 12px; padding: 8px; width: auto;">🎁 Ежедневный бонус</button>
            </form>
            <a href="/logout" style="text-decoration: none;"><button class="danger" style="width: auto; padding: 10px 25px;">Выйти</button></a>
        </div>
    </div>
    
    <div class="flex" style="align-items: flex-start;">
        <div style="flex: 2;">
            <h3>🖱️ Кликер (0.5 коина за клик)</h3>
            <div class="card" style="text-align: center; border-left-color: var(--accent);">
                <div class="clicker-btn" onclick="doClick()">ТАП!</div>
                <p style="font-size: 12px; color: gray; margin-top: 15px;">Защита от автокликера включена (кулдаун 0.2 сек).</p>
            </div>

            <h3>🎉 Доступные эвенты</h3>
            {% for event in events %}
                <div class="card" style="border-left-color: var(--secondary);">
                    <h4 style="margin:0; color:var(--text); font-size: 18px;">{{ event['name'] }}</h4>
                    <p style="margin:5px 0; font-size:14px; color:var(--primary); font-weight: 700;">🕒 {{ event['date'] }}</p>
                    <p style="margin:0 0 15px 0; font-size:14px; color:#7f8c8d; font-weight: 500;">{{ event['info'] }}</p>
                    
                    {% if event['status'] == 'finished' %}
                        <div style="background: rgba(255, 255, 255, 0.1); padding: 12px; border-radius: 8px; color: #7f8c8d; font-weight: 700; text-align: center; border: 1px dashed gray;">🏁 Эвент завершён.</div>
                    {% else %}
                        {% set p = statuses.get(event['id']) %}
                        {% if p %}
                            <div style="background: rgba(46, 213, 115, 0.1); padding: 12px; border-radius: 8px; color: var(--success); font-weight: 700; text-align: center; border: 1px solid var(--success);">✅ Вы записаны!</div>
                        {% else %}
                            <form method="POST" action="/event_respond/{{ event['id'] }}/accept" style="margin-bottom: 10px;">
                                <button class="success" type="submit" style="width:100%;" {% if user['coins'] < 0 %}disabled title="У вас долг!"{% endif %}>✅ Приду</button>
                            </form>
                            <form method="POST" action="/event_respond/{{ event['id'] }}/decline" class="flex" style="gap:5px;">
                                <input type="text" name="reason" placeholder="Причина" required style="margin:0; flex: 2;">
                                <button class="danger" type="submit" style="flex: 1;">❌ Не смогу</button>
                            </form>
                        {% endif %}
                    {% endif %}
                </div>
            {% else %}
                <div class="card"><p>Пока нет активных эвентов.</p></div>
            {% endfor %}
        </div>

        <div style="flex: 1; margin-left: 15px;">
            {% if my_custom_requests %}
            <h3>📦 Мои заказы ролей</h3>
            <div class="card" style="border-left-color: var(--primary);">
                {% for r in my_custom_requests %}
                    <div style="border-bottom: 1px solid var(--input-border); padding: 10px 0;">
                        <b style="color: var(--primary);">{{ r['role_name'] }}</b>
                        {% if r['status'] == 'pending' %}
                            <p style="font-size: 12px; color: gray;">Ожидает оценки админа...</p>
                        {% elif r['status'] == 'offered' %}
                            <p style="font-size: 13px; font-weight: 700; color: var(--accent);">Админ оценил в {{ r['price'] }} коинов. Берешь?</p>
                            <form method="POST" action="/respond_custom/{{ r['id'] }}" class="flex" style="gap: 5px;">
                                <button type="submit" name="action" value="accept" class="success" style="flex: 1; padding: 5px; font-size: 12px;">✅ Купить</button>
                                <button type="submit" name="action" value="decline" class="danger" style="flex: 1; padding: 5px; font-size: 12px;">❌ Отказаться</button>
                            </form>
                        {% elif r['status'] == 'accepted' %}
                            <p style="font-size: 12px; color: var(--success); font-weight: 700;">✅ Вы купили эту роль!</p>
                        {% elif r['status'] == 'declined' %}
                            <p style="font-size: 12px; color: var(--danger);">❌ Вы отказались.</p>
                        {% endif %}
                    </div>
                {% endfor %}
            </div>
            {% endif %}

            <h3>🛒 Магазин</h3>
            <div class="card" style="border-left-color: var(--success);">
                {% for item in shop %}
                    <div style="border-bottom: 1px solid var(--input-border); padding-bottom: 10px; margin-bottom: 10px;">
                        <b style="color: var(--primary);">{{ item['name'] }}</b> <br>
                        <small style="color:gray;">{{ item['desc'] }}</small>
                        <p style="font-weight: 800; color: var(--accent); margin: 10px 0;">{{ item['price'] }} коинов</p>
                        <form method="POST" action="/buy_shop_item/{{ item['id'] }}">
                            <button class="warn" style="padding: 10px; font-size: 14px;" {% if user['coins'] < item['price'] %}disabled{% endif %}>Купить</button>
                        </form>
                    </div>
                {% endfor %}
            </div>

            <h3>✍️ Заказать свою роль</h3>
            <div class="card">
                <p style="font-size: 12px; color: gray; margin-top:0;">Опиши, какую роль хочешь. Админ сам назначит цену.</p>
                <form method="POST" action="/order_custom_role">
                    <input type="text" name="role_name" placeholder="Название роли" required>
                    <input type="text" name="role_color" placeholder="Цвет" required>
                    <input type="text" name="role_duration" placeholder="Срок" required>
                    <textarea name="role_perms" rows="3" placeholder="Какие права хотите? (Опишите)" required></textarea>
                    <button class="blue" type="submit" style="font-size: 12px; padding: 8px;">Отправить заказ</button>
                </form>
            </div>

            <h3>📜 История</h3>
            <div class="card" style="max-height: 300px; overflow-y: auto;">
                {% for h in history %}
                    <div class="history-item">
                        <span class="{{ 'plus' if h['amount'] > 0 else 'minus' }}">{{ '+' if h['amount'] > 0 else '' }}{{ "%.2f"|format(h['amount']) }}</span>
                        <span style="flex:2; margin-left: 10px; font-size:12px; color: #7f8c8d; font-weight: 600;">{{ h['comment'] }}</span>
                    </div>
                {% else %}<p>Пусто.</p>{% endfor %}
            </div>
        </div>
    </div>
</div>
<script>
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% for category, message in messages %}
            showToast("{{ message }}", "{{ category }}");
        {% endfor %}
    {% endwith %}
</script>
"""
ADMIN_LAYOUT = """
<div class="container" style="max-width: 1200px;">
    <div class="flex" style="justify-content: space-between; background: var(--input-bg); padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 2px solid var(--accent);">
        <div><h1 style="margin: 0; color: var(--accent);">Админ-Панель</h1></div>
        <div><a href="/logout" style="text-decoration: none;"><button class="danger" style="width: auto; padding: 10px 25px;">Выйти</button></a></div>
    </div>

    <div class="tabs">
        <a href="/admin?tab=main" class="tab-link {{ 'active' if active_tab == 'main' else '' }}">🏠 Главная</a>
        <a href="/admin?tab=users" class="tab-link {{ 'active' if active_tab == 'users' else '' }}">👥 Пользователи</a>
        <a href="/admin?tab=events" class="tab-link {{ 'active' if active_tab == 'events' else '' }}">🎉 Эвенты</a>
        <a href="/admin?tab=shop" class="tab-link {{ 'active' if active_tab == 'shop' else '' }}">🛒 Магазин и Заказы</a>
    </div>

    {% if active_tab == 'main' %}
    <div class="flex" style="align-items: flex-start;">
        <div style="flex: 1;">
            <div class="card" style="border-left-color: var(--success);">
                <h3>👤 Создать профиль</h3>
                <form method="POST" action="/admin/create_user">
                    <input type="text" name="name" placeholder="Никнейм" required>
                    <input type="text" name="password" placeholder="Пароль" required>
                    <button class="success" type="submit">Создать</button>
                </form>
            </div>
        </div>
        <div style="flex: 2; margin-left: 15px;">
            <div class="card">
                <h3>💰 Начислить / Списать коины</h3>
                <form method="POST" action="/admin/give_coins" class="flex">
                    <select name="user_name" required style="flex:2; margin: 0;">
                        {% for u_name, u_data in users.items() %}{% if u_data['role'] != 'admin' %}<option value="{{ u_name }}">{{ u_name }} ({{ "%.2f"|format(u_data['coins']) }})</option>{% endif %}{% endfor %}
                    </select>
                    <input type="number" step="any" name="amount" placeholder="Сумма" required style="flex:1; margin: 0;">
                    <input type="text" name="comment" placeholder="За что" required style="flex:2; margin: 0;">
                    <button type="submit" style="flex:1; margin: 0; padding: 12px 10px;">Применить</button>
                </form>
            </div>
            <div class="card" style="border-left-color: var(--warn); background: rgba(241,196,15,0.05);">
                <h3>💸 Вызвать инфляцию</h3>
                <form method="POST" action="/admin/inflate">
                    <input type="number" name="amount" placeholder="Сумма инфляции" required>
                    <button class="warn" type="submit">Запустить</button>
                </form>
                <form method="POST" action="/admin/reset_inflation" style="margin-top: 10px;">
                    <button type="submit" style="background: gray; font-size: 10px; padding: 5px;">Сбросить уведомления</button>
                </form>
            </div>
        </div>
    </div>
    {% endif %}

    {% if active_tab == 'users' %}
    <h3>Управление пользователями</h3>
    
    <div class="card" style="border-left-color: var(--blue); margin-bottom: 15px;">
        <h4>📁 Загрузить базу (users.satpanel)</h4>
        <form method="POST" action="/admin/upload_users" enctype="multipart/form-data">
            <input type="file" name="file" accept=".satpanel" required style="padding: 10px; border: none; background: transparent; margin: 0 0 10px 0;">
            <button type="submit" class="blue" style="font-size: 12px;">Загрузить и создать юзеров</button>
        </form>
        <p style="font-size: 12px; color: gray; margin-top: 5px;">Синтаксис файла: Ник (строка 1), Пароль (строка 2), Ник (строка 3), Пароль (строка 4) и т.д.</p>
    </div>

    <input type="text" id="searchUser" onkeyup="filterUsers()" placeholder="Поиск по нику..." style="max-width: 300px; margin-bottom: 10px;">
    <table id="usersTable">
        <tr><th>Имя</th><th>Баланс</th><th>Уровень</th><th>Действия</th></tr>
        {% for u_name, u_data in users.items() %}
            {% if u_data['role'] != 'admin' %}
            <tr>
                <td style="font-weight: 700;">{{ u_name }} {% if u_data.get('banned') %}<span style="color:var(--danger);">(БАН)</span>{% endif %}</td>
                <td style="color:{{ 'var(--danger)' if u_data['coins'] < 0 else 'var(--primary)' }}; font-weight: 900;">{{ "%.2f"|format(u_data['coins']) }}</td>
                <td>{{ (u_data['earned'] // 500) + 1 }}</td>
                <td>
                    {% if u_data['coins'] < 0 %}<form method="POST" action="/admin/reset_coins/{{ u_name }}" style="display:inline;"><button class="warn" style="padding:4px 8px; font-size:10px; width: auto;">Обнулить</button></form>{% endif %}
                    <form method="POST" action="/admin/ban_user/{{ u_name }}" style="display:inline;"><button class="{{ 'success' if u_data.get('banned') else 'warn' }}" style="padding:4px 8px; font-size:10px; width: auto;">{{ 'Разбан' if u_data.get('banned') else 'Бан' }}</button></form>
                    <form method="POST" action="/admin/delete_user/{{ u_name }}" style="display:inline;" onsubmit="return confirm('Удалить?');"><button class="danger" style="padding:4px 8px; font-size:10px; width: auto;">Удалить</button></form>
                </td>
            </tr>
            {% endif %}
        {% endfor %}
    </table>
    <script>
        function filterUsers() {
            let input = document.getElementById("searchUser").value.toLowerCase();
            let rows = document.getElementById("usersTable").getElementsByTagName("tr");
            for (let i = 1; i < rows.length; i++) {
                let txt = rows[i].getElementsByTagName("td")[0].innerText.toLowerCase();
                rows[i].style.display = txt.includes(input) ? "" : "none";
            }
        }
    </script>
    {% endif %}

    {% if active_tab == 'events' %}
    <div class="card" style="border-left-color: var(--primary);">
        <h3>🎉 Создать эвент</h3>
        <form method="POST" action="/admin/create_event">
            <input type="text" name="name" placeholder="Название" required>
            <input type="text" name="date" placeholder="Время" required>
            <input type="text" name="info" placeholder="Инфа">
            <button type="submit">Создать</button>
        </form>
    </div>
    
    <h3>Управление эвентами и списки</h3>
    {% for e in events %}
        <div class="card" style="border-left-color: var(--secondary); margin-bottom: 20px;">
            <div class="flex" style="justify-content: space-between;">
                <div>
                    <h4 style="margin:0;">{{ e['name'] }}</h4>
                    <p style="margin:5px 0; color:var(--primary); font-weight: 700;">🕒 {{ e['date'] }}</p>
                    <p style="margin:0;">{{ e['info'] }}</p>
                </div>
                {% if e.status != 'finished' %}
                <form method="POST" action="/admin/finish_event/{{ e['id'] }}" style="margin-top: 10px; flex: none;">
                    <button class="blue" type="submit" style="width: auto; padding: 8px 15px;">🏁 Завершить</button>
                </form>
                {% endif %}
            </div>

            {% if e.status != 'finished' %}
            <div class="flex" style="align-items: flex-start; gap: 15px; margin-top: 15px;">
                <div style="flex: 1; background: rgba(46, 213, 115, 0.05); padding: 10px; border-radius: 8px; border: 1px solid rgba(46, 213, 115, 0.3);">
                    <h5 style="margin: 0 0 5px 0; color: var(--success);">✅ Придут ({{ e['accepted_list']|length }})</h5>
                    <ul style="margin: 0; padding-left: 20px; font-weight: 600; font-size: 14px;">
                        {% for p in e['accepted_list'] %}<li>{{ p }}</li>{% else %}<li style="color: gray;">Пока никто</li>{% endfor %}
                    </ul>
                </div>
                <div style="flex: 1; background: rgba(255, 71, 87, 0.05); padding: 10px; border-radius: 8px; border: 1px solid rgba(255, 71, 87, 0.3);">
                    <h5 style="margin: 0 0 5px 0; color: var(--danger);">❌ Отказались ({{ e['declined_list']|length }})</h5>
                    <ul style="margin: 0; padding-left: 20px; font-weight: 600; font-size: 14px;">
                        {% for p in e['declined_list'] %}<li>{{ p['name'] }} <span style="font-size: 12px; color: gray; font-weight: 400;">({{ p['reason'] }})</span></li>{% else %}<li style="color: gray;">Пока никто</li>{% endfor %}
                    </ul>
                </div>
                
                <div style="flex: 1; background: rgba(0, 0, 0, 0.03); padding: 10px; border-radius: 8px; border: 1px solid rgba(0, 0, 0, 0.1);">
                    <h5 style="margin: 0 0 5px 0; color: gray;">⏳ Не ответили ({{ e['pending_list']|length }})</h5>
                    <ul style="margin: 0; padding-left: 20px; font-weight: 600; font-size: 14px; color: gray;">
                        {% for p in e['pending_list'] %}<li>{{ p }}</li>{% else %}<li style="color: gray;">Все ответили</li>{% endfor %}
                    </ul>
                </div>
            </div>
            {% endif %}
        </div>
    {% endfor %}
    {% endif %}

    {% if active_tab == 'shop' %}
    <div class="flex" style="align-items: flex-start;">
        <div style="flex: 1;">
            <h3>✍️ Заказы кастомных ролей</h3>
            <div class="card" style="border-left-color: var(--blue);">
                {% for r in custom_requests %}
                    <div style="border-bottom: 1px solid var(--input-border); padding: 10px 0;">
                        <b style="color: var(--primary);">{{ r['user'] }}</b> <small>({{ r['date'] }})</small>
                        <p style="margin:5px 0; font-size: 13px;"><b>Роль:</b> {{ r['role_name'] }} (Цвет: {{ r['color'] }}, Срок: {{ r['duration'] }})</p>
                        <p style="margin:0 0 5px 0; font-size: 12px; color: gray;"><b>Права:</b> {{ r['role_perms'] }}</p>
                        
                        {% if r['status'] == 'pending' %}
                            <form method="POST" action="/admin/process_custom/{{ r['id'] }}" class="flex" style="gap: 5px; align-items: flex-start; margin-top: 10px;">
                                <input type="number" name="final_price" placeholder="Цена (коины)" required style="margin:0; flex: 1; padding: 5px;">
                                <button type="submit" name="action" value="offer" class="success" style="flex: 1; padding: 5px; font-size: 12px;">Предложить цену</button>
                                <button type="submit" name="action" value="reject" class="danger" style="flex: 1; padding: 5px; font-size: 12px;">Отклонить</button>
                            </form>
                        {% elif r['status'] == 'offered' %}
                            <p style="color: var(--warn); font-weight: 700; font-size: 12px;">Ожидает решения игрока (Цена: {{ r['price'] }})...</p>
                        {% elif r['status'] == 'accepted' %}
                            <p style="color: var(--success); font-weight: 700; font-size: 12px;">✅ Игрок согласился! (Цена: {{ r['price'] }})</p>
                        {% elif r['status'] == 'declined' %}
                            <p style="color: var(--danger); font-weight: 700; font-size: 12px;">❌ Игрок отказался.</p>
                        {% endif %}
                    </div>
                {% else %}<p style="color: gray;">Нет заказов.</p>{% endfor %}
            </div>
        </div>

        <div style="flex: 1; margin-left: 15px;">
            <h3>🛒 Запросы на покупку из магазина</h3>
            <div class="card" style="border-left-color: var(--warn);">
                {% for r in role_requests %}
                    <div style="border-bottom: 1px solid var(--input-border); padding: 10px 0;">
                        <b style="color: var(--primary);">{{ r['user'] }}</b> <small>({{ r['date'] }})</small>
                        <p style="margin:5px 0; font-size: 13px;">Хочет купить: <b>{{ r['item_name'] }}</b> за {{ r['price'] }} коинов.</p>
                        <form method="POST" action="/admin/process_role_request/{{ loop.index0 }}" class="flex" style="gap: 5px;">
                            <button type="submit" name="action" value="approve" class="success" style="flex: 1; padding: 5px; font-size: 12px;">Выдать</button>
                            <button type="submit" name="action" value="reject" class="danger" style="flex: 1; padding: 5px; font-size: 12px;">Отклонить</button>
                        </form>
                    </div>
                {% else %}<p style="color: gray;">Нет запросов.</p>{% endfor %}
            </div>
        </div>
    </div>
    {% endif %}
</div>
<script>
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% for category, message in messages %}
            showToast("{{ message }}", "{{ category }}");
        {% endfor %}
    {% endwith %}
</script>
"""
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name, password = request.form['name'], request.form['password']
        if name in DB['users'] and DB['users'][name]['password'] == password:
            if DB['users'][name].get('banned'):
                flash('Вы забанены в панели!', 'error'); return redirect(url_for('login'))
            session['user'] = name
            session['role'] = DB['users'][name]['role']
            return redirect(url_for('admin') if session['role'] == 'admin' else url_for('profile'))
        flash('Неверное имя или пароль!', 'error')
    return get_layout(render_template_string(LOGIN_CONTENT))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/click', methods=['POST'])
def api_click():
    if 'user' not in session: return jsonify({"success": False, "message": "Не авторизован"})
    user_name = session['user']
    now = time.time()
    if now - DB['users'][user_name].get('last_click', 0) < 0.2:
        return jsonify({"success": False, "message": "Слишком быстро! Не спамь."})
    DB['users'][user_name]['last_click'] = now
    DB['users'][user_name]['coins'] += 0.5
    DB['users'][user_name]['earned'] += 0.5
    return jsonify({"success": True, "new_balance": DB['users'][user_name]['coins']})

@app.route('/dismiss_inflation', methods=['POST'])
def dismiss_inflation():
    if 'user' in session:
        DB['users'][session['user']]['inflation_msg'] = ""
    return redirect(url_for('profile'))

@app.route('/claim_daily', methods=['POST'])
def claim_daily():
    if 'user' not in session: return redirect(url_for('login'))
    u = DB['users'][session['user']]
    today = datetime.now().strftime("%Y-%m-%d")
    if u.get('last_daily') == today:
        flash('Вы уже забирали бонус сегодня!', 'error')
    else:
        u['coins'] += 50
        u['earned'] += 50
        u['last_daily'] = today
        DB['history'].append({"user": session['user'], "amount": 50, "comment": "Ежедневный бонус", "date": datetime.now().strftime("%d.%m %H:%M")})
        flash('Бонус +50 получен!', 'success')
    return redirect(url_for('profile'))

@app.route('/profile')
def profile():
    if 'user' not in session or session.get('role') == 'admin': return redirect(url_for('login'))
    user_name = session['user']
    u = DB['users'][user_name]
    
    history = [h for h in DB['history'] if h['user'] == user_name]
    history.reverse()
    
    my_inv = [i for i in DB['inventory'] if i['user'] == user_name]
    my_custom = [r for r in DB['custom_requests'] if r['user'] == user_name]
    my_custom.reverse() 
    
    lvl = int((u['earned'] // 500) + 1)
    rank = "Новичок"
    if lvl >= 5: rank = "Хорошист"
    if lvl >= 10: rank = "Легенда"

    statuses = {r['event_id']: r for r in DB['responses'] if r['user'] == user_name}
    
    return get_layout(render_template_string(USER_CONTENT, 
        user_name=user_name, user=u, level=lvl, rank_name=rank,
        events=DB['events'], history=history, statuses=statuses, 
        shop=DB['shop'], my_inventory=my_inv, my_custom_requests=my_custom))

@app.route('/order_custom_role', methods=['POST'])
def order_custom_role():
    if 'user' not in session: return redirect(url_for('login'))
    new_id = max([r['id'] for r in DB['custom_requests']], default=0) + 1
    DB['custom_requests'].append({
        "id": new_id, "user": session['user'], "role_name": request.form.get('role_name'),
        "color": request.form.get('role_color'), "duration": request.form.get('role_duration'),
        "role_perms": request.form.get('role_perms'), "status": "pending", "price": 0,
        "date": datetime.now().strftime("%d.%m %H:%M")
    })
    flash('Заказ на роль отправлен админу! Ждите оценки.', 'success')
    return redirect(url_for('profile'))

@app.route('/respond_custom/<int:req_id>', methods=['POST'])
def respond_custom(req_id):
    if 'user' not in session: return redirect(url_for('login'))
    action = request.form.get('action')
    req = next((r for r in DB['custom_requests'] if r['id'] == req_id), None)
    
    if req and req['user'] == session['user'] and req['status'] == 'offered':
        if action == 'accept':
            price = req['price']
            if DB['users'][session['user']]['coins'] >= price:
                DB['users'][session['user']]['coins'] -= price
                DB['users'][session['user']]['spent'] += price
                req['status'] = 'accepted'
                DB['history'].append({"user": session['user'], "amount": -price, "comment": f"Покупка роли: {req['role_name']}", "date": datetime.now().strftime("%d.%m %H:%M")})
                DB['inventory'].append({"user": session['user'], "item_name": f"Кастомная роль: {req['role_name']}", "date": datetime.now().strftime("%d.%m %H:%M")})
                flash('Вы успешно купили роль!', 'success')
            else:
                flash('Недостаточно коинов для покупки!', 'error')
        elif action == 'decline':
            req['status'] = 'declined'
            flash('Вы отказались от покупки.', 'success')
    return redirect(url_for('profile'))

@app.route('/buy_shop_item/<int:item_id>', methods=['POST'])
def buy_shop_item(item_id):
    if 'user' not in session: return redirect(url_for('login'))
    user_name = session['user']
    item = next((i for i in DB['shop'] if i['id'] == item_id), None)
    if item:
        if DB['users'][user_name]['coins'] >= item['price']:
            DB['role_requests'].append({"user": user_name, "item_name": item['name'], "price": item['price'], "date": datetime.now().strftime("%d.%m %H:%M")})
            flash('Запрос на покупку отправлен!', 'success')
        else:
            flash('Недостаточно коинов!', 'error')
    return redirect(url_for('profile'))

@app.route('/event_respond/<int:event_id>/<action>', methods=['POST'])
def event_respond(event_id, action):
    if 'user' not in session or session.get('role') == 'admin': return redirect(url_for('login'))
    user_name = session['user']
    DB['responses'] = [r for r in DB['responses'] if not (r['event_id'] == event_id and r['user'] == user_name)]
    if action == 'accept':
        DB['responses'].append({"event_id": event_id, "user": user_name, "status": "accepted", "reason": ""})
    elif action == 'decline':
        DB['responses'].append({"event_id": event_id, "user": user_name, "status": "declined", "reason": request.form.get('reason', 'Без причины')})
    return redirect(url_for('profile'))

@app.route('/admin')
def admin():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    active_tab = request.args.get('tab', 'main')
    
    events_view = []
    for e in DB['events']:
        ev_dict = dict(e)
        parts = [p for p in DB['responses'] if p['event_id'] == e['id']]
        
        ev_dict['accepted_list'] = [p['user'] for p in parts if p['status'] == 'accepted']
        ev_dict['declined_list'] = [{"name": p['user'], "reason": p['reason']} for p in parts if p['status'] == 'declined']
        
        responded_names = [p['user'] for p in parts]
        all_users = [name for name, data in DB['users'].items() if data['role'] != 'admin']
        ev_dict['pending_list'] = [name for name in all_users if name not in responded_names]
        
        events_view.append(ev_dict)
    
    return get_layout(render_template_string(ADMIN_LAYOUT, 
        users=DB['users'], events=events_view, 
        role_requests=DB['role_requests'], custom_requests=DB['custom_requests'],
        active_tab=active_tab))

@app.route('/admin/create_user', methods=['POST'])
def admin_create_user():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    name = request.form.get('name')
    if name in DB['users']:
        flash('Имя занято.', 'error')
    else:
        DB['users'][name] = {"password": request.form.get('password'), "role": "user", "coins": 0, "earned": 0, "spent": 0, "banned": False, "inflation_msg": "", "last_click": 0}
        flash(f'Профиль {name} создан!', 'success')
    return redirect(url_for('admin', tab='main'))

@app.route('/admin/upload_users', methods=['POST'])
def admin_upload_users():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    file = request.files.get('file')
    if file:
        content = file.read().decode('utf-8').splitlines()
        count = 0
        for i in range(0, len(content), 2):
            if i + 1 < len(content):
                name = content[i].strip()
                pwd = content[i+1].strip()
                if name and pwd and name not in DB['users']:
                    DB['users'][name] = {"password": pwd, "role": "user", "coins": 0, "earned": 0, "spent": 0, "banned": False, "inflation_msg": "", "last_click": 0}
                    count += 1
        flash(f'Успешно загружено {count} пользователей!', 'success')
    return redirect(url_for('admin', tab='users'))

@app.route('/admin/give_coins', methods=['POST'])
def admin_give_coins():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    user_name = request.form.get('user_name')
    amount = float(request.form.get('amount'))
    comment = request.form.get('comment')
    if user_name in DB['users']:
        if amount > 0:
            DB['users'][user_name]['coins'] += amount
            DB['users'][user_name]['earned'] += amount
        else:
            DB['users'][user_name]['coins'] += amount
            DB['users'][user_name]['spent'] += abs(amount)
        DB['history'].append({"user": user_name, "amount": amount, "comment": comment, "date": datetime.now().strftime("%d.%m %H:%M")})
        flash(f'Успешно изменено на {amount}!', 'success')
    return redirect(url_for('admin', tab='main'))

@app.route('/admin/process_custom/<int:req_id>', methods=['POST'])
def admin_process_custom(req_id):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    action = request.form.get('action')
    req = next((r for r in DB['custom_requests'] if r['id'] == req_id), None)
    if req and req['status'] == 'pending':
        if action == 'offer':
            price = int(float(request.form.get('final_price', 0)))
            req['price'] = price
            req['status'] = 'offered'
            flash(f'Цена {price} коинов предложена игроку {req["user"]}!', 'success')
        elif action == 'reject':
            req['status'] = 'declined'
            flash('Заказ отклонен.', 'success')
    return redirect(url_for('admin', tab='shop'))

@app.route('/admin/process_role_request/<int:req_idx>', methods=['POST'])
def admin_process_role_request(req_idx):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    action = request.form.get('action')
    req = DB['role_requests'][req_idx]
    if action == 'approve':
        user_name = req['user']
        price = req['price']
        if DB['users'][user_name]['coins'] >= price:
            DB['users'][user_name]['coins'] -= price
            DB['users'][user_name]['spent'] += price
            DB['history'].append({"user": user_name, "amount": -price, "comment": f"Покупка: {req['item_name']}", "date": datetime.now().strftime("%d.%m %H:%M")})
            DB['inventory'].append({"user": user_name, "item_name": req['item_name'], "date": datetime.now().strftime("%d.%m %H:%M")})
            flash(f'Роль {req["item_name"]} выдана {user_name}!', 'success')
        else:
            flash('У игрока уже не хватает коинов!', 'error')
    DB['role_requests'].pop(req_idx)
    return redirect(url_for('admin', tab='shop'))

@app.route('/admin/create_event', methods=['POST'])
def admin_create_event():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    new_id = max([e['id'] for e in DB['events']], default=0) + 1
    DB['events'].append({
        "id": new_id, "name": request.form['name'], "date": request.form['date'],
        "info": request.form['info'], "status": "active"
    })
    flash('Эвент создан!', 'success')
    return redirect(url_for('admin', tab='events'))

@app.route('/admin/finish_event/<int:event_id>', methods=['POST'])
def admin_finish_event(event_id):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    for e in DB['events']:
        if e['id'] == event_id:
            e['status'] = 'finished'
            break
    flash('Эвент завершён!', 'success')
    return redirect(url_for('admin', tab='events'))

@app.route('/admin/inflate', methods=['POST'])
def admin_inflate():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    amount = request.form.get('amount')
    for name, u in DB['users'].items():
        if u['role'] != 'admin':
            u['inflation_msg'] = f"Внимание! Инфляция на сервере повысилась на {amount} коинов!"
    flash('Инфляция запущена!', 'success')
    return redirect(url_for('admin', tab='main'))

@app.route('/admin/reset_inflation', methods=['POST'])
def admin_reset_inflation():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    for name, u in DB['users'].items():
        if u['role'] != 'admin':
            u['inflation_msg'] = ""
    flash('Уведомления об инфляции сброшены!', 'success')
    return redirect(url_for('admin', tab='main'))

@app.route('/admin/reset_coins/<name>', methods=['POST'])
def admin_reset_coins(name):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    if name in DB['users']:
        DB['users'][name]['coins'] = 0
        flash(f'Баланс {name} сброшен в 0.', 'success')
    return redirect(url_for('admin', tab='users'))

@app.route('/admin/ban_user/<name>', methods=['POST'])
def admin_ban_user(name):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    if name in DB['users']:
        DB['users'][name]['banned'] = not DB['users'][name].get('banned', False)
        flash(f'Статус бана для {name} изменен.', 'success')
    return redirect(url_for('admin', tab='users'))

@app.route('/admin/delete_user/<name>', methods=['POST'])
def admin_delete_user(name):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    if name in DB['users'] and DB['users'][name]['role'] != 'admin':
        del DB['users'][name]
        DB['history'] = [h for h in DB['history'] if h['user'] != name]
        DB['responses'] = [r for r in DB['responses'] if r['user'] != name]
        DB['role_requests'] = [r for r in DB['role_requests'] if r['user'] != name]
        DB['custom_requests'] = [r for r in DB['custom_requests'] if r['user'] != name]
        flash('Пользователь и все его данные удалены.', 'success')
    return redirect(url_for('admin', tab='users'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
