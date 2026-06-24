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
        img = cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_CUBIC)
    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    lab = cv2.merge((clahe.apply(l), a, b))
    return cv2.cvtColor(cv2.cvtColor(lab, cv2.COLOR_LAB2BGR), cv2.COLOR_BGR2RGB)

def extract_embedding(img):
    img = preprocess_image(img)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    # Use OpenCV haar cascade (very fast, no model download needed)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
    if len(faces) == 0:
        return None, "No face detected"
    
    # Crop the face
    x, y, w, h = faces[0]
    face_crop = img[y:y+h, x:x+w]
    face_resized = cv2.resize(face_crop, (32, 32))
    
    # Create embedding from pixel values (simple but fast)
    embedding = face_resized.flatten().astype(np.float32)
    embedding = embedding / np.linalg.norm(embedding)
    
    return embedding.tolist(), "opencv"

def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

def faces_match(e1, e2, threshold=0.75):
    return cosine_sim(e1, e2) >= threshold
