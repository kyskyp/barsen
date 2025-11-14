import telebot, sqlite3, time, os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import token

bot = telebot.TeleBot(token)
DB = "barsen_final_fixed.db"
user_progress = {}

# === УДАЛЕНИЕ БД ===
if os.path.exists(DB): os.remove(DB)
conn = sqlite3.connect(DB); c = conn.cursor()
c.execute('CREATE TABLE users (user_id INTEGER PRIMARY KEY, username TEXT, lvl INTEGER DEFAULT 1, exp INTEGER DEFAULT 0, quizzes INTEGER DEFAULT 0, clicks INTEGER DEFAULT 0)')
c.execute('CREATE TABLE achievements (user_id INTEGER, ach_id TEXT, PRIMARY KEY (user_id, ach_id))')
conn.commit(); conn.close()

# === ПРЕДМЕТЫ ===
SUBJECTS = ["Математика", "Физика", "Химия", "Биология", "История", "Русский язык", "Информатика"]
SUB_CODES = ["math","physics","chemistry","biology","history","russian","informatics"]

# === КЛИКЕР УРОВНИ (МАКС 1000) ===
CLICKER_LEVELS = [
    {"min": 0,    "name": "Барсен-ребёнок", "desc": "Маленький Барсен"},
    {"min": 10,   "name": "Барсен-школьник", "desc": "Учится в школе"},
    {"min": 50,   "name": "Барсен-студент", "desc": "Готовится к ЕГЭ"},
    {"min": 100,  "name": "Барсен-учитель", "desc": "Делится знаниями"},
    {"min": 250,  "name": "Барсен-гений", "desc": "Решил P=NP"},
    {"min": 500,  "name": "Барсен-бог", "desc": "Вселенная в голове"},
    {"min": 750,  "name": "Барсен-∞", "desc": "Бесконечность"},
    {"min": 1000, "name": "Бездельник", "desc": "ТЫ ПРОШЁЛ КЛИКЕР!"}
]

# === АЧИВКИ ===
ACHIEVEMENTS = {
    "first": "Первая викторина",
    "perfect": "Идеал (5/5)",
    "genius": "Гений (5/5 на сложном)",
    "idler": "Бездельник (1000 кликов)"
}

# === КВИЗЫ (7 × 3 × 5) — уже есть в предыдущем коде, вставь сюда ===
QUIZ = {
    "math": {
        "easy": [
            {"q":"2+2=?", "opts":["3","4","5"], "ans":1},
            {"q":"3×3=?", "opts":["6","9","12"], "ans":1},
            {"q":"10-5=?", "opts":["4","5","6"], "ans":1},
            {"q":"Квадрат?", "opts":["3 стороны","4","5"], "ans":1},
            {"q":"1+1=?", "opts":["1","2","3"], "ans":1}
        ],
        "medium": [
            {"q":"2×(3+4)=?", "opts":["14","10","7"], "ans":0},
            {"q":"x²=16 → x=?", "opts":["±4","4","16"], "ans":0},
            {"q":"sin(90°)=?", "opts":["0","1","-1"], "ans":1},
            {"q":"π≈?", "opts":["3.14","2.71","1.61"], "ans":0},
            {"q":"√9=?", "opts":["2","3","4"], "ans":1}
        ],
        "hard": [
            {"q":"d(sin x)/dx=?", "opts":["cos x","-sin x","1"], "ans":0},
            {"q":"∫x dx=?", "opts":["x²/2","x²","ln x"], "ans":0},
            {"q":"lim x→0 sin x/x=?", "opts":["1","0","∞"], "ans":0},
            {"q":"e^iπ=?", "opts":["-1","1","0"], "ans":0},
            {"q":"P=NP?", "opts":["Да","Нет","Неизвестно"], "ans":2}
        ]
    },
    "physics": {
        "easy": [
            {"q":"F=m×a. F=?", "opts":["Масса","Сила","Ускорение"], "ans":1},
            {"q":"c=?", "opts":["3×10⁸","300","3×10⁶"], "ans":0},
            {"q":"G=?", "opts":["9.8","6.67×10⁻¹¹","1"], "ans":1},
            {"q":"E=mc² — это?", "opts":["Энергия","Скорость","Масса"], "ans":0},
            {"q":"I=U/R — это?", "opts":["Закон Ома","Закон Ньютона","Закон Кулона"], "ans":0}
        ],
        "medium": [
            {"q":"λ×f=?", "opts":["v","E","P"], "ans":0},
            {"q":"Δx Δp ≥ ?", "opts":["ħ/2","0","∞"], "ans":0},
            {"q":"E=?", "opts":["mc²","mv²/2","mgh"], "ans":0},
            {"q":"F=qvB — это?", "opts":["Сила Лоренца","Гравитация","Трение"], "ans":0},
            {"q":"P=IV — это?", "opts":["Мощность","Сила","Энергия"], "ans":0}
        ],
        "hard": [
            {"q":"∇·E=?", "opts":["ρ/ε₀","0","B"], "ans":0},
            {"q":"Шрёдингер: iħ∂ψ/∂t=?", "opts":["Hψ","Eψ","pψ"], "ans":0},
            {"q":"c=1/√(ε₀μ₀)?", "opts":["Да","Нет","Иногда"], "ans":0},
            {"q":"Эффект Комптона?", "opts":["Рассеяние","Поглощение","Отражение"], "ans":0},
            {"q":"Квантовая запутанность?", "opts":["Да","Нет","Миф"], "ans":0}
        ]
    },
    "chemistry": {
        "easy": [
            {"q":"H₂O=?", "opts":["Кислород","Вода","Углекислый газ"], "ans":1},
            {"q":"NaCl=?", "opts":["Соль","Кислота","Щелочь"], "ans":0},
            {"q":"CO₂=?", "opts":["Кислород","Углекислый газ","Водород"], "ans":1},
            {"q":"pH воды=?", "opts":["0","7","14"], "ans":1},
            {"q":"O₂ — это?", "opts":["Газ","Жидкость","Твёрдое"], "ans":0}
        ],
        "medium": [
            {"q":"Na + Cl₂ → ?", "opts":["NaCl","NaCl₂","Na₂Cl"], "ans":0},
            {"q":"H₂SO₄ — это?", "opts":["Кислота","Щелочь","Соль"], "ans":0},
            {"q":"CH₄ — это?", "opts":["Метан","Этан","Пропан"], "ans":0},
            {"q":"pH<7 — это?", "opts":["Кислота","Щелочь","Нейтрально"], "ans":0},
            {"q":"Атомный номер углерода?", "opts":["6","8","12"], "ans":0}
        ],
        "hard": [
            {"q":"Гибридизация CH₄?", "opts":["sp","sp²","sp³"], "ans":2},
            {"q":"ΔH<0=?", "opts":["Экзотермия","Эндотермия","Изотермия"], "ans":0},
            {"q":"pKa уксусной≈?", "opts":["4.76","7.00","14.00"], "ans":0},
            {"q":"Льюисова кислота?", "opts":["Принимает e⁻","Отдаёт e⁻","Нейтральна"], "ans":0},
            {"q":"Квантовая химия?", "opts":["Да","Нет","Миф"], "ans":0}
        ]
    },
    "biology": {
        "easy": [
            {"q":"Клетка — основа жизни?", "opts":["Да","Нет","Иногда"], "ans":0},
            {"q":"ДНК в ядре?", "opts":["Да","Нет","В митохондриях"], "ans":0},
            {"q":"Фотосинтез в?", "opts":["Хлоропластах","Митохондриях","Ядре"], "ans":0},
            {"q":"ATP=?", "opts":["Энергия","Белок","Гормон"], "ans":0},
            {"q":"Митоз=?", "opts":["Деление","Слияние","Мутация"], "ans":0}
        ],
        "medium": [
            {"q":"Кодон=?", "opts":["3 нуклеотида","1","2"], "ans":0},
            {"q":"Фенотип=?", "opts":["Генотип+среда","Только ген","Только среда"], "ans":0},
            {"q":"Мейоз=?", "opts":["Половые клетки","Соматические","Вирусы"], "ans":0},
            {"q":"Эволюция=?", "opts":["Дарвин","Ламарк","Оба"], "ans":2},
            {"q":"РНК=?", "opts":["Переносчик","Хранилище","Катализатор"], "ans":0}
        ],
        "hard": [
            {"q":"CRISPR=?", "opts":["Редактирование генов","Вирус","Белок"], "ans":0},
            {"q":"Эпигенетика=?", "opts":["Изменение без ДНК","Мутация","Репликация"], "ans":0},
            {"q":"Горизонтальный перенос?", "opts":["Между видами","Внутри вида","Миф"], "ans":0},
            {"q":"Клеточный цикл?", "opts":["G1,S,G2,M","G0,G1,S","M,G2"], "ans":0},
            {"q":"Теломеры=?", "opts":["Укорачиваются","Удлиняются","Стабильны"], "ans":0}
        ]
    },
    "history": {
        "easy": [
            {"q":"Пирамиды=?", "opts":["Египет","Мексика","Китай"], "ans":0},
            {"q":"Колумб открыл?", "opts":["Америку","Австралию","Антарктиду"], "ans":0},
            {"q":"1812=?", "opts":["Отечественная война","ВОВ","Крымская"], "ans":0},
            {"q":"Рим основан?", "opts":["753 до н.э.","476 н.э.","1000"], "ans":0},
            {"q":"Моисей=?", "opts":["Египет","Израиль","Вавилон"], "ans":0}
        ],
        "medium": [
            {"q":"Куликово поле=?", "opts":["1380","1240","1812"], "ans":0},
            {"q":"Революция 1789=?", "opts":["Франция","Россия","Америка"], "ans":0},
            {"q":"Пётр I=?", "opts":["Реформы","Революция","Война"], "ans":0},
            {"q":"Магна Карта=?", "opts":["1215","1066","1776"], "ans":0},
            {"q":"Холодная война=?", "opts":["СССР vs США","ВОВ","Корея"], "ans":0}
        ],
        "hard": [
            {"q":"Ренессанс начался в?", "opts":["Италия","Франция","Англия"], "ans":0},
            {"q":"1776=?", "opts":["США","Франция","Россия"], "ans":0},
            {"q":"Берлинская стена=?", "opts":["1961","1989","1945"], "ans":0},
            {"q":"Пакт Молотова-Риббентропа=?", "opts":["1939","1941","1945"], "ans":0},
            {"q":"Кто открыл Америку до Колумба?", "opts":["Викинги","Китайцы","Никто"], "ans":0}
        ]
    },
    "russian": {
        "easy": [
            {"q":"Падежей в русском?", "opts":["5","6","7"], "ans":1},
            {"q":"Антоним 'холодный'?", "opts":["Тёплый","Горячий","Мокрый"], "ans":0},
            {"q":"Приставка 'пере-'?", "opts":["Да","Нет","Иногда"], "ans":0},
            {"q":"'Книга' — корень?", "opts":["книг-","книж-","кн-"], "ans":0},
            {"q":"'Бежать' — глагол?", "opts":["Да","Нет","Существительное"], "ans":0}
        ],
        "medium": [
            {"q":"Главное в предложении?", "opts":["Подл+сказ","Только подл","Только сказ"], "ans":0},
            {"q":"Омонимы=?", "opts":["Одинаковое написание","Синонимы","Антонимы"], "ans":0},
            {"q":"'Солнце' — род?", "opts":["Мужской","Женский","Средний"], "ans":2},
            {"q":"'Идти' — вид?", "opts":["Совершенный","Несовершенный","Оба"], "ans":1},
            {"q":"'Красиво' — это?", "opts":["Наречие","Прилагательное","Глагол"], "ans":0}
        ],
        "hard": [
            {"q":"Морфема=?", "opts":["Минимальная единица","Слово","Предложение"], "ans":0},
            {"q":"Синтаксис=?", "opts":["Связь слов","Звуки","Буквы"], "ans":0},
            {"q":"Золотой век русской литературы?", "opts":["XIX","XVIII","XX"], "ans":0},
            {"q":"'Быть' — спряжение?", "opts":["1-е","2-е","Особое"], "ans":2},
            {"q":"'Человек' — одушевлённое?", "opts":["Да","Нет","Иногда"], "ans":0}
        ]
    },
    "informatics": {
        "easy": [
            {"q":"len([1,2,3])=?", "opts":["3","2","4"], "ans":0},
            {"q":"1+1 в двоичной=?", "opts":["10","11","1"], "ans":0},
            {"q":"RAM=?", "opts":["Оперативная память","Жёсткий диск","Процессор"], "ans":0},
            {"q":"CPU=?", "opts":["Процессор","Монитор","Клавиатура"], "ans":0},
            {"q":"IP=?", "opts":["Адрес","Пароль","Имя"], "ans":0}
        ],
        "medium": [
            {"q":"O(n²)=?", "opts":["Квадратичная","Линейная","Логарифмическая"], "ans":0},
            {"q":"append()=?", "opts":["Добавляет","Удаляет","Сортирует"], "ans":0},
            {"q":"[1,2]*3=?", "opts":["[1,2,1,2,1,2]","[3,6]","[1,2]"], "ans":0},
            {"q":"def f(): pass — это?", "opts":["Функция","Переменная","Класс"], "ans":0},
            {"q":"HTTP 200=?", "opts":["Успех","Ошибка","Редирект"], "ans":0}
        ],
        "hard": [
            {"q":"P vs NP=?", "opts":["Нерешена","P=NP","P≠NP"], "ans":0},
            {"q":"Хэш-таблица=?", "opts":["O(1)","O(n)","O(log n)"], "ans":0},
            {"q":"Кубиты=?", "opts":["0 и 1 одновременно","0 или 1","Только 1"], "ans":0},
            {"q":"Turing complete?", "opts":["Может всё","Ограничен","Миф"], "ans":0},
            {"q":"Гёдель=?", "opts":["Неполнота","Полнота","Равенство"], "ans":0}
        ]
    }
}

# === АНИМАЦИИ ===
def animate(chat_id, text):
    msg = bot.send_message(chat_id, text)
    for _ in range(3):
        time.sleep(0.3)
        try: bot.edit_message_text(text + "." * (_+1), chat_id, msg.message_id)
        except: pass

# === КНОПКИ ===
def main_menu():
    m = InlineKeyboardMarkup(row_width=1)
    m.add(InlineKeyboardButton("Начать викторину", callback_data="quiz_start"))
    m.add(InlineKeyboardButton("Барсен кликер", callback_data="clicker_start"))
    return m

def subject_menu():
    m = InlineKeyboardMarkup(row_width=2)
    for i, sub in enumerate(SUBJECTS):
        m.add(InlineKeyboardButton(sub, callback_data=f"sub_{SUB_CODES[i]}"))
    return m

def level_menu(sub):
    m = InlineKeyboardMarkup(row_width=3)
    m.add(InlineKeyboardButton("Лёгкий", callback_data=f"lvl_easy_{sub}"),
          InlineKeyboardButton("Средний", callback_data=f"lvl_medium_{sub}"),
          InlineKeyboardButton("Сложный", callback_data=f"lvl_hard_{sub}"))
    return m

def clicker_button(clicks):
    m = InlineKeyboardMarkup()
    m.add(InlineKeyboardButton(f"Клик! ({clicks})", callback_data="click"))
    m.add(InlineKeyboardButton("Назад", callback_data="back"))
    return m

def bottom_menu():
    return ReplyKeyboardMarkup(resize_keyboard=True, row_width=2).add(
        KeyboardButton("Начать"), KeyboardButton("Профиль"),
        KeyboardButton("Топ"), KeyboardButton("Ачивки")
    )

# === СТАРТ ===
@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (uid, m.from_user.username or "Ученик"))
    conn.commit(); conn.close()
    animate(m.chat.id, "Барсен просыпается")
    bot.send_message(m.chat.id,
        "*ПОМОЩНИК БАРСЕН*\n"
        "7 предметов • 3 уровня • 5 вопросов\n"
        "*Пасхалка:* кликер в меню",
        reply_markup=main_menu(), parse_mode='Markdown')
    bot.send_message(m.chat.id, "Выбери действие:", reply_markup=bottom_menu())

# === ТЕКСТ ===
@bot.message_handler(func=lambda m: m.text in ["Начать", "Профиль", "Топ", "Ачивки"])
def txt(m):
    uid = m.from_user.id
    if m.text == "Начать": start(m)
    elif m.text == "Профиль": profile(uid, m)
    elif m.text == "Топ": top(m)
    elif m.text == "Ачивки": ach(uid, m)

# === CALLBACK ===
@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    uid = c.from_user.id; data = c.data
    try:
        if data == "quiz_start":
            bot.edit_message_text("Выбери предмет:", c.message.chat.id, c.message.message_id, reply_markup=subject_menu())
        elif data.startswith("sub_"):
            sub = data.split("_")[1]
            name = SUBJECTS[SUB_CODES.index(sub)]
            bot.edit_message_text(f"Уровень для *{name}*:", c.message.chat.id, c.message.message_id, reply_markup=level_menu(sub), parse_mode='Markdown')
        elif data.startswith("lvl_"):
            level, sub = data.split("_")[1], data.split("_")[2]
            user_progress[uid] = {"sub": sub, "lvl": level, "q": 0, "score": 0}
            ask(uid, sub, level, 0)
        elif data.startswith("ans_"):
            handle_ans(c, uid)

        elif data == "clicker_start":
            clicks = get_clicks(uid)
            level = get_clicker_level(clicks)
            text = format_clicker(clicks, level)
            bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=clicker_button(clicks), parse_mode='Markdown')
        elif data == "click":
            add_click(uid)
            clicks = get_clicks(uid)
            level = get_clicker_level(clicks)
            text = format_clicker(clicks, level)
            bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=clicker_button(clicks), parse_mode='Markdown')
            if clicks in [l["min"] for l in CLICKER_LEVELS[1:]]:
                bot.send_message(uid, f"*УРОВЕНЬ: {CLICKER_LEVELS[level]['name']}*")
                if clicks >= 1000:
                    unlock_achievement(uid, "idler")

        elif data == "back":
            bot.edit_message_text("*Помощник Барсен*", c.message.chat.id, c.message.message_id, reply_markup=main_menu(), parse_mode='Markdown')
    except Exception as e: print(e)

# === КЛИКЕР ===
def get_clicks(uid):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT clicks FROM users WHERE user_id=?", (uid,))
    res = c.fetchone(); conn.close()
    return res[0] if res else 0

def add_click(uid):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("UPDATE users SET clicks=clicks+1 WHERE user_id=?", (uid,))
    conn.commit(); conn.close()

def get_clicker_level(clicks):
    for i, lvl in enumerate(CLICKER_LEVELS):
        if clicks < lvl["min"]: return i-1
    return len(CLICKER_LEVELS)-1

def format_clicker(clicks, level):
    lvl = CLICKER_LEVELS[level]
    next_lvl = CLICKER_LEVELS[level+1] if level < len(CLICKER_LEVELS)-1 else None
    if next_lvl:
        progress = min(int(clicks / next_lvl["min"] * 10), 10)
    else:
        progress = 10
    bar = "█" * progress + "░" * (10 - progress)
    return (
        f"*Кликер Барсена*\n\n"
        f"*{lvl['name']}*\n"
        f"{lvl['desc']}\n"
        f"Клик: *{clicks}*\n"
        f"{bar}\n"
        f"До следующего: *{next_lvl['min'] if next_lvl else 'ФИНАЛ'}*"
    )

# === ВИКТОРИНА ===
def ask(uid, sub, lvl, q_idx):
    q = QUIZ[sub][lvl][q_idx]
    m = InlineKeyboardMarkup(row_width=1)
    for i, opt in enumerate(q["opts"]):
        m.add(InlineKeyboardButton(opt, callback_data=f"ans_{sub}_{q_idx}_{i}"))
    m.add(InlineKeyboardButton("Назад", callback_data="quiz_start"))
    bot.send_message(uid, f"{sub.upper()} | {lvl.capitalize()} | Вопрос {q_idx+1}/5\n\n{q['q']}", reply_markup=m, parse_mode='Markdown')

def handle_ans(c, uid):
    if uid not in user_progress: return
    parts = c.data.split("_")
    sub, q_idx, ans = parts[1], int(parts[2]), int(parts[3])
    lvl = user_progress[uid]["lvl"]
    if ans == QUIZ[sub][lvl][q_idx]["ans"]:
        user_progress[uid]["score"] += 1
        bot.answer_callback_query(c.id, "Верно!")
    user_progress[uid]["q"] += 1
    if user_progress[uid]["q"] < 5:
        ask(uid, sub, lvl, user_progress[uid]["q"])
    else:
        end_quiz(uid, sub, lvl)

def end_quiz(uid, sub, lvl):
    score = user_progress[uid]["score"]
    exp = score * 20 + {"easy":20, "medium":40, "hard":60}[lvl]
    add_exp(uid, exp)
    name = SUBJECTS[SUB_CODES.index(sub)]
    bot.send_message(uid, f"*Готово!*\n*{name}* | *{lvl.capitalize()}*\n*{score}/5* | +{exp} EXP", reply_markup=main_menu(), parse_mode='Markdown')
    if score == 5: unlock_achievement(uid, "perfect")
    if score == 5 and lvl == "hard": unlock_achievement(uid, "genius")
    unlock_achievement(uid, "first")
    del user_progress[uid]

def add_exp(uid, exp):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("UPDATE users SET exp=exp+?, quizzes=quizzes+1 WHERE user_id=?", (exp, uid))
    c.execute("SELECT exp, lvl FROM users WHERE user_id=?", (uid,))
    e, l = c.fetchone()
    nl = 1 + e // 200
    if nl > l:
        c.execute("UPDATE users SET lvl=? WHERE user_id=?", (nl, uid))
        bot.send_message(uid, f"*УРОВЕНЬ {nl}!*")
    conn.commit(); conn.close()

# === АЧИВКИ ===
def unlock_achievement(uid, ach_id):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO achievements VALUES (?, ?)", (uid, ach_id))
    conn.commit(); conn.close()
    if c.rowcount:
        bot.send_message(uid, f"*Ачивка: {ACHIEVEMENTS[ach_id]}*")

# === ПРОФИЛЬ, ТОП, АЧИВКИ ===
def profile(uid, msg):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT lvl, exp, quizzes, clicks FROM users WHERE user_id=?", (uid,))
    l, e, q, cl = c.fetchone(); conn.close()
    need = 200 + (l-1)*50
    progress = min(int((e % need) / need * 10), 10)
    bar = "█" * progress + "░" * (10 - progress)
    text = f"*Профиль*\nУровень: *{l}*\nОпыт: *{e % need}/{need}*\n{bar}\nВикторин: *{q}*\nКликов: *{cl}*"
    bot.send_message(msg.chat.id, text, reply_markup=main_menu(), parse_mode='Markdown')

def top(msg):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT username, exp FROM users ORDER BY exp DESC LIMIT 10")
    rows = c.fetchall(); conn.close()
    text = "*Топ-10*\n" + ("\n".join([f"{i+1}. {n} — {e} EXP" for i,(n,e) in enumerate(rows)]) or "Пусто!")
    bot.send_message(msg.chat.id, text, reply_markup=main_menu(), parse_mode='Markdown')

def ach(uid, msg):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute("SELECT ach_id FROM achievements WHERE user_id=?", (uid,))
    unlocked = [r[0] for r in c.fetchall()]; conn.close()
    text = "*Ачивки*\n"
    for aid, name in ACHIEVEMENTS.items():
        status = "Получено" if aid in unlocked else "Не получено"
        text += f"{status} — *{name}*\n"
    bot.send_message(msg.chat.id, text, reply_markup=main_menu(), parse_mode='Markdown')

# === ЗАПУСК ===
if __name__ == "__main__":
    print("БАРСЕН — ФИНАЛ 2.0. ВСЁ ИСПРАВЛЕНО. 1000 КЛИКОВ = ФИНАЛ.")
    bot.infinity_polling()