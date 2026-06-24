import bcrypt
import numpy as np
import cv2
import os
import time
import socket
import streamlit as st
from io import BytesIO
from PIL import Image
from db import get_conn


def hash_pw(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def check_pw(pw, hashed):
    return bcrypt.checkpw(pw.encode(), hashed.encode())

def get_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except:
        return "127.0.0.1"

def log_login(user_id, method, status):
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO login_history (user_id,login_method,login_status,ip_address) VALUES (%s,%s,%s,%s)",
            (user_id, method, status, get_ip()))
        conn.commit()
        conn.close()
    except:
        pass

def camera_to_array(cam_bytes):
    return np.array(Image.open(BytesIO(cam_bytes.getvalue())).convert("RGB"))

def save_face_image(cam_bytes, email):
    os.makedirs("face_images", exist_ok=True)
    safe = email.replace("@", "_at_").replace(".", "_")
    path = f"face_images/{safe}_{int(time.time())}.jpg"
    Image.open(BytesIO(cam_bytes.getvalue())).convert("RGB").save(path)
    return path

def preprocess_image(img):
    h, w = img.shape[:2]
    if w < 640:
        scale = 640 / w
        img   = cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_CUBIC)
    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    lab   = cv2.merge((clahe.apply(l), a, b))
    return cv2.cvtColor(cv2.cvtColor(lab, cv2.COLOR_LAB2BGR), cv2.COLOR_BGR2RGB)

def extract_embedding(img):
    from deepface import DeepFace
    img = preprocess_image(img)
    for backend in ["opencv","ssd","mtcnn","retinaface"]:
        try:
            r = DeepFace.represent(img_path=img, model_name="Facenet",
                                   enforce_detection=True, detector_backend=backend)
            return r[0]["embedding"], backend
        except:
            continue
    try:
        r = DeepFace.represent(img_path=img, model_name="Facenet",
                               enforce_detection=False, detector_backend="opencv")
        return r[0]["embedding"], "opencv(no-enforce)"
    except Exception as e:
        return None, str(e)

def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

def faces_match(e1, e2, threshold=0.70):
    return cosine_sim(e1, e2) >= threshold