import json
import os
import re

CHAT_FILE = os.path.join('data', 'chat_messages.json')

# Patrón para detectar tokens/base64 largos (sin espacios, muchos caracteres especiales)
TOKEN_PATTERN = re.compile(r'^[A-Za-z0-9+/=._-]{30,}$')

# Carga el archivo de mensajes
with open(CHAT_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

changed = False
for user, messages in list(data.items()):
    if user.startswith('_'):
        continue
    cleaned = []
    for msg in messages:
        text = msg.get('text', '')
        # Si el texto es sospechoso (muy largo, sin espacios, parece token/base64), lo saltamos
        if isinstance(text, str):
            if TOKEN_PATTERN.match(text) or (len(text) > 40 and text.count(' ') < 2):
                changed = True
                continue
        cleaned.append(msg)
    if len(cleaned) != len(messages):
        data[user] = cleaned
        changed = True

if changed:
    with open(CHAT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print('Mensajes basura eliminados.')
else:
    print('No se encontraron mensajes basura.')
