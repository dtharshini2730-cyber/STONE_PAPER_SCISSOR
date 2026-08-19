# ✊ HAND WARS - The Ultimate Stone • Paper • Scissors Battle

An interactive **2-Player Local Rock-Paper-Scissors Web Application** powered by **Flask** and a **TensorFlow / Keras Deep Learning Model**. Players can use their computer's **Live WebCam** or upload hand gesture images to play against each other.

---

## 🌟 Key Features

- 🎥 **Live WebCam Stream**: Real-time camera feed using HTML5 `getUserMedia` API with instant snapshot capture.
- 📁 **File Upload Fallback**: Manual image upload option for systems without camera access.
- 🤖 **AI-Powered Move Detection**: Instant gesture classification (`Rock`, `Paper`, `Scissor`) using a pre-trained Keras model.
- 🔒 **Fair Turn-Based Mechanics**: Player 1's move is securely locked and hidden until Player 2 submits their gesture.
- 📊 **Match Scoreboard & History**: Real-time round progress, cumulative score tracking, and detailed round history.
- 🎨 **Modern Dark UI**: Sleek, responsive interface built with custom glassmorphism CSS.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10–3.13, Flask, TensorFlow, `tf-keras`, Pillow, NumPy
- **Frontend**: HTML5, Vanilla CSS3, JavaScript (WebCam API, Canvas API)
- **Machine Learning**: Keras H5 Computer Vision Model (`keras_model.h5`)

---

## 🚀 Quick Start

### 1. Prerequisites
Ensure you have **Python 3.10+** installed on your system.

### 2. Clone the Repository
```bash
git clone https://github.com/dtharshini2730-cyber/STONE_PAPER_SCISSOR.git
cd STONE_PAPER_SCISSOR
```

### 3. Create a Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the Application
```bash
python app.py
```

### 6. Play the Game
Open your web browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 📁 Repository Structure

```text
STONE_PAPER_SCISSOR/
├── app.py              # Main Flask application server & routing logic
├── keras_model.h5      # Pre-trained Keras image classification model
├── labels.txt          # Class labels (Rock, Scissor, Paper)
├── requirements.txt    # Python package dependencies
├── static/
│   └── style.css       # Main stylesheet (Dark mode design)
└── templates/
    ├── index.html      # Game setup & round selector page
    ├── game.html       # Main arena page (WebCam capture & player cards)
    └── final.html      # Final match results & victory screen
```

---

## 🛡️ License

This project is open-source and available under the [MIT License](LICENSE).
