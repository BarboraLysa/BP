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
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev_default_key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///lockers.db")
CORS(app)
db.init_app(app)
bcrypt.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "role"




@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



@app.route("/")
def role():
    return render_template("role.html")


@app.route("/admin")
@login_required
def admin_dashboard():
    lockers = Locker.query.all()
    return render_template("admin_dashboard.html", lockers=lockers)

@app.route("/user")
@login_required
def user_dashboard():
    lockers = Locker.query.filter(
        or_(
            Locker.is_active == False,                    # volné
            Locker.requested_by == current_user.id,       # požadované
            Locker.assigned_to == current_user.id         # pridělené
        )
    ).all()
    return render_template("user_dashboard.html", lockers=lockers)

@app.route("/request_locker/<int:locker_id>", methods=["POST"])
@login_required
def request_locker(locker_id):
    locker = Locker.query.get(locker_id)
    if locker and not locker.is_active:
        locker.requested_by = current_user.id
        db.session.commit()
        return jsonify({"status": "success", "message": "Žiadosť odoslaná!"})
    return jsonify({"status": "error", "message": "Schránka je obsadená"})

@app.route("/approve_locker/<int:locker_id>", methods=["POST"])
@login_required
def approve_locker(locker_id):
    locker = Locker.query.get(locker_id)
    if locker and locker.requested_by:
        locker.assigned_to = locker.requested_by
        locker.is_active = True
        locker.code = ''.join(random.choices(string.digits, k=4))
        db.session.commit()
        return jsonify({"status": "success", "new_code": locker.code})
    return jsonify({"status": "error", "message": "Schránka neexistuje alebo nemá žiadosť"})

@app.route("/reject_locker/<int:locker_id>", methods=["POST"])
@login_required
def reject_locker(locker_id):
    locker = Locker.query.get(locker_id)
    if locker and locker.requested_by:
        locker.requested_by = None
        db.session.commit()
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Schránka nemá žiadosť na spracovanie"})

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        admin = User.query.filter_by(email=email, is_admin=True).first()
        if admin and bcrypt.check_password_hash(admin.password, password):
            login_user(admin)
            return redirect(url_for("admin_dashboard"))
        flash("Nesprávne prihlasovacie údaje", "danger")
    return render_template("admin_login.html")

@app.route("/user_login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("user_dashboard"))
        flash("Nesprávne prihlasovacie údaje", "danger")
    return render_template("user_login.html")

@app.route("/user_register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Účet vytvorený, môžete sa prihlásiť", "success")
        return redirect(url_for("user_login"))

    return render_template("user_register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("role"))


@app.route('/check_code', methods=['POST'])
def check_code():
    data = request.get_json()
    entered_code = data.get("code")

    if not entered_code:
        return "invalid", 400

    # Skontroluj, či zadaný kód patrí nejakej aktívnej schránke
    locker = Locker.query.filter_by(code=entered_code, is_active=True).first()
    if locker:
        
        locker.is_active = False
        locker.assigned_to = None
        locker.requested_by = None
        locker.code = None
        db.session.commit()

        return f"locker{locker.id}", 200
    return "invalid", 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all() 


        if Locker.query.count() == 0:
            for _ in range(2):
                db.session.add(Locker())
            db.session.commit()

    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)


