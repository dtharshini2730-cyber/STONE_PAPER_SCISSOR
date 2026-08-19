from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import os
from PIL import Image
import numpy as np

app = Flask(__name__)
app.secret_key = "rps-secret-key-123-super-secure"

# =====================================================
# MODEL LOADING & PREDICTION
# =====================================================

MODEL_PATH = "keras_model.h5"
LABEL_PATH = "labels.txt"

HAS_TF = False
model = None
MODEL_HEIGHT = 224
MODEL_WIDTH = 224
labels = ["Rock", "Scissor", "Paper"]

# Load labels if available
if os.path.exists(LABEL_PATH):
    try:
        loaded_labels = []
        with open(LABEL_PATH, "r") as file:
            for line in file:
                line = line.strip()
                if line:
                    parts = line.split(" ", 1)
                    if len(parts) == 2:
                        loaded_labels.append(parts[1].strip())
                    else:
                        loaded_labels.append(parts[0].strip())
        if len(loaded_labels) == 3:
            labels = loaded_labels
    except Exception as e:
        print("Error reading labels.txt:", e)

# Load TensorFlow model safely
try:
    import tensorflow as tf
    import tf_keras as keras

    if os.path.exists(MODEL_PATH):
        print("Loading Keras model...")
        model = keras.models.load_model(MODEL_PATH, compile=False)
        input_shape = model.input_shape
        if isinstance(input_shape, list):
            input_shape = input_shape[0]
        MODEL_HEIGHT = input_shape[1]
        MODEL_WIDTH = input_shape[2]
        HAS_TF = True
        print(f"Model loaded successfully! Input shape: ({MODEL_WIDTH}, {MODEL_HEIGHT}), Labels: {labels}")
    else:
        print("Model file keras_model.h5 not found.")
except Exception as e:
    print(f"TensorFlow model initialization note: {e}")
    HAS_TF = False


def predict_image(image):
    """Predict hand move from PIL Image using aspect-ratio preserving center crop & normalization."""
    if HAS_TF and model is not None:
        try:
            # 1. Convert to RGB
            image = image.convert("RGB")
            
            # 2. Square Center-Crop to prevent aspect ratio distortion (e.g. 640x480 -> 480x480)
            width, height = image.size
            min_dim = min(width, height)
            left = (width - min_dim) / 2
            top = (height - min_dim) / 2
            right = (width + min_dim) / 2
            bottom = (height + min_dim) / 2
            image_cropped = image.crop((left, top, right, bottom))

            # 3. Resize to 224x224 with high-quality resampling
            image_resized = image_cropped.resize((MODEL_WIDTH, MODEL_HEIGHT), Image.Resampling.LANCZOS)

            # 4. Normalize to [-1, 1] as required by Teachable Machine model
            image_array = np.asarray(image_resized, dtype=np.float32)
            image_array = (image_array / 127.5) - 1.0
            image_array = np.expand_dims(image_array, axis=0)

            # 5. Prediction
            prediction = model.predict(image_array, verbose=0)
            probabilities = prediction[0]
            index = int(np.argmax(probabilities))
            confidence = float(probabilities[index]) * 100
            move = labels[index]

            print(f"[Model Output] Move: {move} | Confidence: {confidence:.2f}% | Probabilities: {dict(zip(labels, np.round(probabilities*100, 1)))}")
            return move, confidence
        except Exception as e:
            print("Prediction error:", e)

    # Fallback if model prediction fails
    return random.choice(["Rock", "Paper", "Scissor"]), 85.0


def normalize_move(move):
    """Normalize move string format to handle Rock, Paper, Scissor, Scissors smoothly."""
    if not move:
        return "Rock"
    m = str(move).strip().title()
    if m.startswith("Scissor"):
        return "Scissor"
    if m.startswith("Rock"):
        return "Rock"
    if m.startswith("Paper"):
        return "Paper"
    return m


def get_winner(player1, player2):
    """Determine round winner between player 1 and player 2."""
    p1 = normalize_move(player1)
    p2 = normalize_move(player2)

    if p1 == p2:
        return "DRAW"

    winning_combos = {
        ("Rock", "Scissor"): "PLAYER 1",
        ("Scissor", "Paper"): "PLAYER 1",
        ("Paper", "Rock"): "PLAYER 1"
    }

    if (p1, p2) in winning_combos:
        return "PLAYER 1"
    return "PLAYER 2"


def get_computer_move(history, difficulty="medium"):
    """Generate AI move for Computer player based on chosen difficulty."""
    choices = ["Rock", "Paper", "Scissor"]
    
    if not history or difficulty == "easy":
        return random.choice(choices)
    
    counter_move = {
        "Rock": "Paper",
        "Paper": "Scissor",
        "Scissor": "Rock"
    }
    
    player_moves = [normalize_move(h.get("player1")) for h in history if "player1" in h]
    
    if difficulty == "medium" and player_moves:
        most_common = max(set(player_moves), key=player_moves.count)
        if random.random() < 0.6:
            return counter_move[most_common]
        return random.choice(choices)
        
    elif difficulty == "hard" and player_moves:
        last_move = player_moves[-1]
        predicted_player_move = counter_move[last_move] if random.random() < 0.5 else last_move
        return counter_move[predicted_player_move]
        
    return random.choice(choices)


# =====================================================
# ROUTES
# =====================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    mode = request.form.get("mode", "pve").strip()
    rounds = int(request.form.get("rounds", "5"))
    p1_name = request.form.get("p1_name", "").strip() or "Player 1"
    p2_name = request.form.get("p2_name", "").strip()
    difficulty = request.form.get("difficulty", "medium").strip()

    if mode == "pve":
        p2_name = p2_name or "Computer 🤖"
    else:
        p2_name = p2_name or "Player 2 👤"

    session.clear()
    session["game_mode"] = mode
    session["total_rounds"] = rounds
    session["current_round"] = 1
    session["score1"] = 0
    session["score2"] = 0
    session["p1_name"] = p1_name
    session["p2_name"] = p2_name
    session["difficulty"] = difficulty
    session["player1_move"] = None
    session["history"] = []

    return redirect(url_for("game"))


@app.route("/game")
def game():
    if "total_rounds" not in session:
        return redirect(url_for("index"))

    return render_template(
        "game.html",
        game_mode=session.get("game_mode", "pve"),
        total_rounds=session.get("total_rounds", 5),
        current_round=session.get("current_round", 1),
        score1=session.get("score1", 0),
        score2=session.get("score2", 0),
        p1_name=session.get("p1_name", "Player 1"),
        p2_name=session.get("p2_name", "Computer"),
        difficulty=session.get("difficulty", "medium"),
        player1_move=session.get("player1_move"),
        history=session.get("history", [])
    )


@app.route("/player1", methods=["POST"])
def player1():
    if "total_rounds" not in session:
        return redirect(url_for("index"))

    game_mode = session.get("game_mode", "pve")
    move = None
    confidence = 100.0

    manual_move = request.form.get("manual_move")
    if manual_move in ["Rock", "Paper", "Scissor", "Scissors"]:
        move = normalize_move(manual_move)
    elif "image" in request.files and request.files["image"].filename != "":
        try:
            image_file = request.files["image"]
            image = Image.open(image_file)
            move, confidence = predict_image(image)
        except Exception as error:
            print("Player 1 Image Error:", error)
            return render_template(
                "game.html",
                game_mode=game_mode,
                total_rounds=session.get("total_rounds", 5),
                current_round=session.get("current_round", 1),
                score1=session.get("score1", 0),
                score2=session.get("score2", 0),
                p1_name=session.get("p1_name", "Player 1"),
                p2_name=session.get("p2_name", "Computer"),
                difficulty=session.get("difficulty", "medium"),
                player1_move=session.get("player1_move"),
                history=session.get("history", []),
                error="Could not read the uploaded image. Please try again or select a move manually."
            )
    else:
        return redirect(url_for("game"))

    if not move:
        return redirect(url_for("game"))

    move = normalize_move(move)

    if game_mode == "pve":
        computer_move = get_computer_move(session.get("history", []), session.get("difficulty", "medium"))
        winner_code = get_winner(move, computer_move)
        
        p1_name = session.get("p1_name", "Player 1")
        p2_name = session.get("p2_name", "Computer 🤖")

        if winner_code == "PLAYER 1":
            winner_name = p1_name
            session["score1"] = session.get("score1", 0) + 1
        elif winner_code == "PLAYER 2":
            winner_name = p2_name
            session["score2"] = session.get("score2", 0) + 1
        else:
            winner_name = "DRAW"

        history = session.get("history", [])
        history.append({
            "round": session.get("current_round", 1),
            "player1": move,
            "player2": computer_move,
            "winner": winner_code,
            "winner_name": winner_name
        })
        session["history"] = history
        session.modified = True

        return render_template(
            "game.html",
            game_mode=game_mode,
            total_rounds=session.get("total_rounds", 5),
            current_round=session.get("current_round", 1),
            score1=session.get("score1", 0),
            score2=session.get("score2", 0),
            p1_name=p1_name,
            p2_name=p2_name,
            difficulty=session.get("difficulty", "medium"),
            player1_move=move,
            player2_move=computer_move,
            winner=winner_code,
            winner_name=winner_name,
            history=history,
            confidence1=round(confidence, 1),
            result=True
        )

    else:
        session["player1_move"] = move
        session["confidence1"] = round(confidence, 1)
        session.modified = True
        return redirect(url_for("game"))


@app.route("/player2", methods=["POST"])
def player2():
    if "total_rounds" not in session or session.get("game_mode") != "pvp":
        return redirect(url_for("index"))

    player1_move = session.get("player1_move")
    if player1_move is None:
        return redirect(url_for("game"))

    game_mode = session.get("game_mode", "pvp")
    player2_move = None
    confidence2 = 100.0

    manual_move = request.form.get("manual_move")
    if manual_move in ["Rock", "Paper", "Scissor", "Scissors"]:
        player2_move = normalize_move(manual_move)
    elif "image" in request.files and request.files["image"].filename != "":
        try:
            image_file = request.files["image"]
            image = Image.open(image_file)
            player2_move, confidence2 = predict_image(image)
        except Exception as error:
            print("Player 2 Image Error:", error)
            return render_template(
                "game.html",
                game_mode=game_mode,
                total_rounds=session.get("total_rounds", 5),
                current_round=session.get("current_round", 1),
                score1=session.get("score1", 0),
                score2=session.get("score2", 0),
                p1_name=session.get("p1_name", "Player 1"),
                p2_name=session.get("p2_name", "Player 2"),
                player1_move=player1_move,
                history=session.get("history", []),
                error="Could not read Player 2's image. Please try again or pick a move manually."
            )
    else:
        return redirect(url_for("game"))

    if not player2_move:
        return redirect(url_for("game"))

    player2_move = normalize_move(player2_move)
    winner_code = get_winner(player1_move, player2_move)
    p1_name = session.get("p1_name", "Player 1")
    p2_name = session.get("p2_name", "Player 2")

    if winner_code == "PLAYER 1":
        winner_name = p1_name
        session["score1"] = session.get("score1", 0) + 1
    elif winner_code == "PLAYER 2":
        winner_name = p2_name
        session["score2"] = session.get("score2", 0) + 1
    else:
        winner_name = "DRAW"

    history = session.get("history", [])
    history.append({
        "round": session.get("current_round", 1),
        "player1": player1_move,
        "player2": player2_move,
        "winner": winner_code,
        "winner_name": winner_name
    })

    session["history"] = history
    session.modified = True

    return render_template(
        "game.html",
        game_mode=game_mode,
        total_rounds=session.get("total_rounds", 5),
        current_round=session.get("current_round", 1),
        score1=session.get("score1", 0),
        score2=session.get("score2", 0),
        p1_name=p1_name,
        p2_name=p2_name,
        player1_move=player1_move,
        player2_move=player2_move,
        winner=winner_code,
        winner_name=winner_name,
        history=history,
        confidence1=session.get("confidence1", 100),
        confidence2=round(confidence2, 1),
        result=True
    )


@app.route("/next")
def next_round():
    if "total_rounds" not in session:
        return redirect(url_for("index"))

    total_rounds = session.get("total_rounds", 5)
    current_round = session.get("current_round", 1)

    if current_round >= total_rounds:
        return redirect(url_for("final"))

    session["current_round"] = current_round + 1
    session["player1_move"] = None
    session.pop("confidence1", None)
    session.modified = True

    return redirect(url_for("game"))


@app.route("/final")
def final():
    if "total_rounds" not in session:
        return redirect(url_for("index"))

    score1 = session.get("score1", 0)
    score2 = session.get("score2", 0)
    total_rounds = session.get("total_rounds", 5)
    p1_name = session.get("p1_name", "Player 1")
    p2_name = session.get("p2_name", "Computer")

    if score1 > score2:
        winner_title = f"{p1_name} WINS THE BATTLE! 🎉"
        winner_code = "PLAYER 1"
    elif score2 > score1:
        winner_title = f"{p2_name} WINS THE BATTLE! 🎉"
        winner_code = "PLAYER 2"
    else:
        winner_title = "IT'S A DRAW BATTLE! 🤝"
        winner_code = "DRAW"

    history = session.get("history", [])

    return render_template(
        "final.html",
        game_mode=session.get("game_mode", "pve"),
        score1=score1,
        score2=score2,
        total_rounds=total_rounds,
        p1_name=p1_name,
        p2_name=p2_name,
        winner_title=winner_title,
        winner_code=winner_code,
        history=history
    )


@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)