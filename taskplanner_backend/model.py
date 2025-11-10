import numpy as np
import pickle
from sklearn.ensemble import RandomForestRegressor
from database import connect

MODEL_FILE = "duration_model.pkl"

# Train or load model
def get_model():
    try:
        with open(MODEL_FILE, "rb") as f:
            return pickle.load(f)
    except:
        model = RandomForestRegressor()
        # default training (fake data to initialize)
        X = np.array([[1, 3], [2, 5], [5, 2], [3, 1]])
        y = np.array([30, 60, 20, 45])
        model.fit(X, y)
        with open(MODEL_FILE, "wb") as f:
            pickle.dump(model, f)
        return model

def train_model():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT importance, completed_hour, duration_minutes FROM tasks WHERE duration_minutes IS NOT NULL")
    rows = cur.fetchall()

    if len(rows) < 5:
        return

    X = np.array([[r[0], r[1]] for r in rows])
    y = np.array([r[2] for r in rows])

    model = RandomForestRegressor()
    model.fit(X, y)

    with open(MODEL_FILE, "wb") as f:
        pickle.dump(model, f)

def predict_duration(importance, hour):
    model = get_model()
    X = np.array([[importance, hour]])
    return float(model.predict(X)[0])
