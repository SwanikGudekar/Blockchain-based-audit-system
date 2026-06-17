from flask import Flask, render_template, request, redirect, session, jsonify
import json, os, secrets, hashlib
from datetime import datetime

# ✅ INIT APP
app = Flask(__name__)
app.secret_key = "secret123"

USER_FILE = "users.json"
LOG_FILE = "logs.json"

# ---------------- FILE SETUP ----------------
for file in [USER_FILE, LOG_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump([], f)

# ---------------- HELPERS ----------------
def load_users():
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

def load_logs():
    with open(LOG_FILE, "r") as f:
        return json.load(f)

def save_logs(logs):
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_private_key():
    return secrets.token_hex(32)

def generate_hash(data):
    return hashlib.sha256(data.encode()).hexdigest()

# 🔗 ADD BLOCK (CORE BLOCKCHAIN LOGIC)
def add_block(ip, email, action, old_value, new_value):
    logs = load_logs()

    prev_hash = logs[-1]["hash"] if logs else "0"
    timestamp = str(datetime.now())

    block_string = f"{ip}{email}{action}{old_value}{new_value}{timestamp}{prev_hash}"
    current_hash = generate_hash(block_string)

    block = {
        "index": len(logs) + 1,
        "ip": ip,
        "email": email,
        "action": action,
        "old_value": old_value,
        "new_value": new_value,
        "timestamp": timestamp,
        "prev_hash": prev_hash,
        "hash": current_hash
    }

    logs.append(block)
    save_logs(logs)

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        users = load_users()
        user_ip = request.remote_addr

        private_key = generate_private_key()

        new_user = {
            "email": request.form["email"],
            "username": request.form["username"],
            "password": hash_password(request.form["password"]),
            "private_key": private_key,
            "balance": 100000,
            "total_amount": 150000,
            "deposit": 50000,
            "fd": 30000,
            "address": "Not Set"
        }

        users.append(new_user)
        save_users(users)

        # 🔗 LOG REGISTER
        add_block(user_ip, new_user["email"], "REGISTER", "-", "-")

        return render_template("register_success.html", private_key=private_key)

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = load_users()
        user_ip = request.remote_addr

        for user in users:
            if (
                user["email"] == request.form["email"] and
                user["password"] == hash_password(request.form["password"]) and
                user["private_key"] == request.form["private_key"]
            ):
                session["email"] = user["email"]

                # 🔗 LOG LOGIN
                add_block(user_ip, user["email"], "LOGIN", "-", "-")

                return jsonify({
                    "status": "success",
                    "user": {
                        "email": user["email"],
                        "username": user["username"],
                        "address": user["address"]
                    }
                })

        return jsonify({"status": "error"})

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "email" not in session:
        return redirect("/login")

    users = load_users()

    for user in users:
        if user["email"] == session["email"]:
            return render_template("dashboard.html", user=user)

    return "User not found"

# ---------------- UPDATE PROFILE ----------------
@app.route("/update", methods=["POST"])
def update():
    if "email" not in session:
        return redirect("/login")

    users = load_users()
    user_ip = request.remote_addr

    for user in users:
        if user["email"] == session["email"]:

            old_email = user["email"]
            old_address = user["address"]

            new_email = request.form["email"]
            new_address = request.form["address"]

            # 🔗 EMAIL CHANGE LOG
            if old_email != new_email:
                add_block(user_ip, old_email, "EMAIL_CHANGE", old_email, new_email)

            # 🔗 ADDRESS CHANGE LOG
            if old_address != new_address:
                add_block(user_ip, old_email, "ADDRESS_CHANGE", old_address, new_address)

            # update data
            user["email"] = new_email
            user["address"] = new_address

            session["email"] = new_email

    save_users(users)
    return "OK"

# ---------------- LOGS API ----------------
@app.route("/logs")
def get_logs():
    logs = load_logs()

    # add next_hash for UI
    for i in range(len(logs)):
        if i < len(logs) - 1:
            logs[i]["next_hash"] = logs[i+1]["hash"]
        else:
            logs[i]["next_hash"] = "NULL"

    return jsonify(logs)

# ---------------- VERIFY BLOCKCHAIN ----------------
@app.route("/verify")
def verify():
    logs = load_logs()

    for i in range(len(logs)):
        block = logs[i]

        # 🔹 Recreate hash
        data_string = f"{block['ip']}{block['email']}{block['action']}{block['old_value']}{block['new_value']}{block['timestamp']}{block['prev_hash']}"
        recalculated_hash = hashlib.sha256(data_string.encode()).hexdigest()

        # ❌ Check if hash is tampered
        if block["hash"] != recalculated_hash:
            return jsonify({
                "status": "invalid",
                "reason": f"Block {block['index']} hash mismatch"
            })

        # 🔹 Check chain linking
        if i > 0:
            if block["prev_hash"] != logs[i-1]["hash"]:
                return jsonify({
                    "status": "invalid",
                    "reason": f"Block {block['index']} prev_hash mismatch"
                })

    return jsonify({"status": "valid"})

# ---------------- LOG VIEW PAGE ----------------
@app.route("/logs-view")
def logs_view():
    return render_template("logs.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# redirect user to crypto transger ganache page
@app.route('/crypto')
def crypto():
    return render_template('crypto.html')# your crypto page

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)