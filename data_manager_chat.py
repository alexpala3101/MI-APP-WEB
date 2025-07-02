import os
import json
from datetime import datetime

CHAT_FILE = os.path.join('data', 'chat_messages.json')

def load_chat_messages():
    if not os.path.exists(CHAT_FILE):
        return {}
    with open(CHAT_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def save_chat_messages(messages):
    with open(CHAT_FILE, 'w', encoding='utf-8') as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)

def add_chat_message(username, sender, text, image_url=None, order_id=None):
    messages = load_chat_messages()
    if username not in messages:
        messages[username] = []
    msg = {
        'from': sender,
        'text': text,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    if image_url:
        msg['image_url'] = image_url
    if order_id:
        msg['order_id'] = order_id
    messages[username].append(msg)
    save_chat_messages(messages)
    return True

# Devuelve todos los mensajes de un usuario
# (Unificada para evitar conflicto de definiciones)
def get_user_chat(username, order_id=None):
    messages = load_chat_messages()
    user_msgs = messages.get(username, [])
    if order_id:
        return [m for m in user_msgs if m.get('order_id') == order_id]
    return user_msgs

# Devuelve todos los mensajes de un usuario agrupados por order_id
def get_user_chats_by_order(username):
    messages = load_chat_messages()
    user_msgs = messages.get(username, [])
    chats = {}
    for msg in user_msgs:
        oid = msg.get('order_id')
        if not oid:
            continue
        if oid not in chats:
            chats[oid] = []
        chats[oid].append(msg)
    return chats

def get_all_user_chats():
    """Devuelve un dict {username: [mensajes]} con todos los chats agrupados por usuario (compatible con la estructura actual del JSON)."""
    messages = load_chat_messages()
    user_chats = {}
    # Si el archivo es un dict con claves de usuario
    if isinstance(messages, dict):
        for username, msgs in messages.items():
            if username.startswith('_'):  # Ignorar ejemplos u otros metadatos
                continue
            user_chats[username] = msgs
    # Si es una lista de mensajes individuales (estructura alternativa)
    elif isinstance(messages, list):
        for msg in messages:
            username = msg.get('username')
            if username:
                user_chats.setdefault(username, []).append(msg)
    return user_chats
