from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import random
import string
from models import db, bcrypt, User, Locker
from flask_cors import CORS
from sqlalchemy import or_
import os

app = Flask(__name__)

# Konfigurácia tajného kľúča: zo špeciálnej premennej prostredia alebo použije default
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev_default_key")

# Nastavenie cesty k DB z premennej prostredia alebo defaultne sqlite súbor
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///lockers.db")

# Povolenie CORS (Cross-Origin Resource Sharing), aby mohol frontend komunikovať s API
CORS(app)

# Inicializácia SQLAlchemy s aplikáciou
db.init_app(app)

# Inicializácia Bcrypt s aplikáciou (upravuje bcrypt z models.py)
bcrypt.init_app(app)

# Inicializácia LoginManager (pre prihlásenie a správu session)
login_manager = LoginManager(app)

# Nastavme, kam sa majú presmerovať neregistrovaní/neprihlásení užívatelia
login_manager.login_view = "role"



# Funkcia, ktorou Flask-Login načítava používateľa podľa ID
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Hlavná úvodná stránka, kde si používateľ vyberá, či chce ísť do časti pre admina alebo pre bežného užívateľa
@app.route("/")
def role():
    return render_template("role.html")


# Admin dashboard: zobrazí všetky schránky
@app.route("/admin")
@login_required
def admin_dashboard():
    # Získaj všetky schránky z databázy
    lockers = Locker.query.all()
    # Vráť HTML šablónu pre admina, odovzdaj zoznam schránok
    return render_template("admin_dashboard.html", lockers=lockers)


# User dashboard: zobrazí iba tie schránky, ktoré sú voľné, požadované alebo pridelené aktuálnemu používateľovi
@app.route("/user")
@login_required
def user_dashboard():
    # Filtrovanie
    lockers = Locker.query.filter(
        or_(
            Locker.is_active == False,                    # volné
            Locker.requested_by == current_user.id,       # požadované
            Locker.assigned_to == current_user.id         # pridělené
        )
    ).all()
    # Výsledok sa odovzdá do šablóny user_dashboard.html
    return render_template("user_dashboard.html", lockers=lockers)


# Endpoint: Používateľ požiada o priradenie schránky (označí ju ako požadovanú)
@app.route("/request_locker/<int:locker_id>", methods=["POST"])
@login_required
def request_locker(locker_id):
    # Vyhľadá schránku podľa ID
    locker = Locker.query.get(locker_id)
    # Ak schránka existuje a nie je aktívna
    if locker and not locker.is_active:
        # Označí sa v stĺpci requested_by ID aktuálneho používateľa
        locker.requested_by = current_user.id
        db.session.commit() # Uloženie zmeny do DB
        # Vráti JSON s potvrdením úspechu
        return jsonify({"status": "success", "message": "Žiadosť odoslaná!"})
    # Inak vráti chybu
    return jsonify({"status": "error", "message": "Schránka je obsadená"})


# Endpoint: Admin schváli požiadavku na priradenie schránky
@app.route("/approve_locker/<int:locker_id>", methods=["POST"])
@login_required
def approve_locker(locker_id):
    # Načíta schránku podľa ID
    locker = Locker.query.get(locker_id)
    # Ak existuje a má priradené requested_by
    if locker and locker.requested_by:
        # Priraď ho osobe, ktorá požiadala
        locker.assigned_to = locker.requested_by
        # Označ, že je obsadená
        locker.is_active = True
        # Vygeneruj náhodný 4-miestny číselný kód
        locker.code = ''.join(random.choices(string.digits, k=4))
        db.session.commit() # Uloží zmeny
        # Vráti JSON s potvrdením úspechu
        return jsonify({"status": "success", "new_code": locker.code})
    # Inak vráti chybu
    return jsonify({"status": "error", "message": "Schránka neexistuje alebo nemá žiadosť"})


# Endpoint: Admin zamietne požiadavku na schránku
@app.route("/reject_locker/<int:locker_id>", methods=["POST"])
@login_required
def reject_locker(locker_id):
    # Načíta schránku podľa ID
    locker = Locker.query.get(locker_id)
    # Ak existuje a má requested_by
    if locker and locker.requested_by:
        # Odstráni požiadavku
        locker.requested_by = None
        db.session.commit()# Uloží zmenu
        # Vráti JSON s potvrdením úspechu
        return jsonify({"status": "success"})
    # Inak vráti chybu
    return jsonify({"status": "error", "message": "Schránka nemá žiadosť na spracovanie"})


# Endpoint: Prihlásenie administrátora
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        # Získa údaje z formulára
        email = request.form["email"]
        password = request.form["password"]

        # Vyhľadá používateľa s is_admin=True podľa emailu
        admin = User.query.filter_by(email=email, is_admin=True).first()
        # Overí, či heslo súhlasí (pomocou bcrypt)
        if admin and bcrypt.check_password_hash(admin.password, password):
            login_user(admin) # Prihlásenie
            return redirect(url_for("admin_dashboard"))
        # Ak prihlasovanie zlyhá, zobrazí flash správu
        flash("Nesprávne prihlasovacie údaje", "danger")
    # Pri GET vráti HTML šablónu na prihlásenie admina
    return render_template("admin_login.html")


# Endpoint: Prihlásenie bežného používateľa
@app.route("/user_login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        # Získa údaje z formulára
        email = request.form["email"]
        password = request.form["password"]

         # Vyhľadá používateľa podľa emailu (bez ohľadu na is_admin)
        user = User.query.filter_by(email=email).first()
        # Overenie hesla
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user) # Prihlásenie
            return redirect(url_for("user_dashboard"))
        # Ak prihlasovanie zlyhá, zobrazí flash správu
        flash("Nesprávne prihlasovacie údaje", "danger")
    # Pri GET vráti HTML šablónu na prihlásenie používateľa
    return render_template("user_login.html")


# Endpoint: Registrácia nového používateľa
@app.route("/user_register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        # Získa údaje z formulára
        name = request.form["name"]
        email = request.form["email"]
        # Zahashuje heslo
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")

        # Vytvoríme nový objekt User
        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        # Zobrazí flash správu o úspešnej registrácii
        flash("Účet vytvorený, môžete sa prihlásiť", "success")
        # Presmeruje na prihlásenie používateľa
        return redirect(url_for("user_login"))
    
    # Pri GET len zobrazí šablónu na registráciu
    return render_template("user_register.html")


# Endpoint: Odhlásenie
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("role"))


# API endpoint: Overenie zadaného kódu pre odomknutie schránky
@app.route('/check_code', methods=['POST'])
def check_code():
    # Očakáva JSON payload s kľúčom "code"
    data = request.get_json()
    entered_code = data.get("code")

    # Ak kód nebol zadaný, vráti 400
    if not entered_code:
        return "invalid", 400

    # Vyhľadá schránku podľa kódu, ktorá je zároveň aktívna
    locker = Locker.query.filter_by(code=entered_code, is_active=True).first()
    if locker:
        # Ak existuje, zresetuje jej stav:
        locker.is_active = False
        locker.assigned_to = None
        locker.requested_by = None
        locker.code = None
        db.session.commit()

        # Vráti textový reťazec
        return f"locker{locker.id}", 200
    # Ak nebol nájdený žiaden zodpovedajúci záznam
    return "invalid", 200


# API endpoint: Vygenerovanie nového kódu pre určitú schránku
@app.route("/generate_code/<int:locker_id>", methods=["POST"])
@login_required
def generate_code(locker_id):
    # Načíta schránku podľa ID
    locker = Locker.query.get(locker_id)
    # Ak neexistuje, vráti chybu 404
    if not locker:
        return jsonify({"status": "error", "message": "Schránka neexistuje"}), 404
    # Ak už schránka je aktívna (obsadená), vráti chybu 400
    if locker.is_active:
        return jsonify({"status": "error", "message": "Schránka už obsadená"}), 400

    # Inak vygeneruje 4-miestny číselný kód 
    code = ''.join(random.choices(string.digits, k=4))
    locker.code = code
    locker.is_active = True
    db.session.commit()
    # Vráti JSON s informáciou o úspechu, ID schránky a vygenerovanom kóde
    return jsonify({"status": "success", "locker_id": locker.id, "code": code}), 200


# API endpoint: Reset kódu z určitej schránky 
@app.route("/delete_code/<int:locker_id>", methods=["POST"])
@login_required
def delete_code(locker_id):
    # Načíta schránku podľa ID
    locker = Locker.query.get(locker_id)
    # Ak neexistuje, vráti chybu 404
    if not locker:
        return jsonify({"status": "error", "message": "Schránka neexistuje"}), 404

    # Ak schránka nie je aktívna alebo už nemá kód, vráti chybu 400
    if not locker.is_active or not locker.code:
        return jsonify({"status": "error", "message": "Žiadny kód na vymazanie"}), 400

    # Inak zresetuje stav:
    locker.code = None
    locker.is_active = False
    locker.assigned_to = None
    locker.requested_by = None
    db.session.commit()
    # Vráti JSON s úspechom a ID schránky
    return jsonify({"status": "success", "locker_id": locker.id}), 200

# Spustenie aplikácie, inicializácia databázy a predvytvorenie niekoľkých schránok
if __name__ == "__main__":
    with app.app_context():
        # Vytvorí všetky tabuľky definované v modeloch (ak neexistujú)
        db.create_all() 

        # Ak je tabuľka Locker prázdna, vytvorí dve nové, prázdne schránky
        if Locker.query.count() == 0:
            for _ in range(2):
                db.session.add(Locker())
            db.session.commit()

     # Načíta port z environment premennej alebo použije 5000
    port = int(os.environ.get("PORT", 5000))
    # Spustíme Flask server v debug móde a povolí prístup z akéhokoľvek hostiteľa
    app.run(debug=True, host="0.0.0.0", port=port)


