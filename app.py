from flask import Flask, request, jsonify, render_template_string
import anthropic
import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect
import base64
import os
from datetime import datetime
import random

app = Flask(__name__)

DROPBOX_REFRESH_TOKEN = os.environ.get('DROPBOX_REFRESH_TOKEN')
DROPBOX_APP_KEY = os.environ.get('DROPBOX_APP_KEY')
DROPBOX_APP_SECRET = os.environ.get('DROPBOX_APP_SECRET')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

def get_dropbox_client():
    """Get Dropbox client with refresh token"""
    return dropbox.Dropbox(
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET
    )

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Smart Fridge</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 0;
            height: 100vh;
            display: flex;
            flex-direction: column;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        header { 
            padding: 60px 20px 16px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        h1 { 
            margin: 0;
            font-size: 28px;
            font-weight: 600;
            letter-spacing: -0.5px;
        }
        .inventory-toggle {
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .inventory-toggle:active {
            background: rgba(255,255,255,0.3);
        }
        .inventory-drawer {
            background: white;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }
        .inventory-drawer.open {
            max-height: 600px;
            overflow-y: auto;
        }
        .inventory-section {
            padding: 16px 20px;
            border-bottom: 1px solid #f0f0f0;
        }
        .section-header {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .section-timestamp {
            font-size: 11px;
            color: #999;
            margin-bottom: 8px;
        }
        .items-list {
            list-style: none;
            padding: 0;
            margin: 8px 0;
            font-size: 14px;
        }
        .items-list li {
            padding: 4px 0;
        }
        .upload-btn {
            width: 100%;
            padding: 10px;
            background: rgba(102, 126, 234, 0.1);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 8px;
            color: #667eea;
            font-weight: 600;
            font-size: 13px;
            cursor: pointer;
            margin-top: 8px;
        }
        .upload-input {
            display: none;
        }
        #chat { 
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        .message { 
            margin: 15px 0;
            padding: 16px;
            border-radius: 16px;
            max-width: 85%;
            word-wrap: break-word;
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .user { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin-left: auto;
            text-align: right;
        }
        .assistant { 
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            color: #333;
        }
        .fridge-greeting {
            background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            font-style: italic;
            color: #555;
        }
        .assistant ul {
            margin: 8px 0;
            padding-left: 0;
            list-style: none;
        }
        .assistant li {
            margin: 6px 0;
            padding-left: 0;
        }
        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 4px;
            color: #999;
            font-size: 14px;
            margin: 10px 0;
            padding-left: 5px;
        }
        .typing-indicator span {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #999;
            animation: bounce 1.4s infinite;
        }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }
        .input-container {
            background: white;
            border-top: 1px solid #ddd;
            padding: 12px;
        }
        .quick-replies {
            display: flex;
            gap: 8px;
            margin-bottom: 12px;
            overflow-x: auto;
        }
        .quick-reply-btn {
            padding: 8px 16px;
            background: #f0f0f0;
            border: none;
            border-radius: 20px;
            font-size: 14px;
            white-space: nowrap;
            cursor: pointer;
        }
        .quick-reply-btn:active {
            background: #e0e0e0;
            transform: scale(0.95);
        }
        .input-row {
            display: flex;
            gap: 8px;
        }
        input[type="text"] { 
            flex: 1;
            padding: 12px 16px;
            font-size: 16px;
            border: 1px solid #e0e0e0;
            border-radius: 24px;
            outline: none;
        }
        input[type="text"]:focus {
            border-color: #667eea;
        }
        button.send-btn { 
            padding: 12px 24px;
            font-size: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 24px;
            cursor: pointer;
            font-weight: 600;
        }
        button.send-btn:active { 
            transform: scale(0.95);
        }
        button.send-btn:disabled { 
            opacity: 0.6;
        }
    </style>
</head>
<body>
    <header>
        <h1>🧊 Smart Fridge</h1>
        <button class="inventory-toggle" onclick="toggleInventory()">📦 Inventory</button>
    </header>
    
    <div class="inventory-drawer" id="inventoryDrawer">
        <div class="inventory-section">
            <div class="section-header">❄️ Fresh Items</div>
            <div class="section-timestamp" id="fresh-timestamp">Loading...</div>
            <ul class="items-list" id="fresh-items"><li>Loading...</li></ul>
        </div>
        
        <div class="inventory-section">
            <div class="section-header">🥫 Top Shelves</div>
            <div class="section-timestamp" id="top-timestamp">No photo</div>
            <ul class="items-list" id="top-items"><li>Upload a photo to see items</li></ul>
            <input type="file" id="top-upload" class="upload-input" accept="image/*">
            <button class="upload-btn" onclick="document.getElementById('top-upload').click()">📸 Upload Photo</button>
        </div>
        
        <div class="inventory-section">
            <div class="section-header">🚪 Door Items</div>
            <div class="section-timestamp" id="door-timestamp">No photo</div>
            <ul class="items-list" id="door-items"><li>Upload a photo to see items</li></ul>
            <input type="file" id="door-upload" class="upload-input" accept="image/*">
            <button class="upload-btn" onclick="document.getElementById('door-upload').click()">📸 Upload Photo</button>
        </div>
    </div>
    
    <div id="chat"></div>
    
    <div class="input-container">
        <div class="quick-replies">
            <button class="quick-reply-btn" onclick="quickReply('What\\'s in my fridge?')">What's in my fridge?</button>
            <button class="quick-reply-btn" onclick="quickReply('What can I make?')">What can I make?</button>
        </div>
        <div class="input-row">
            <input type="text" id="input" placeholder="Ask about your fridge...">
            <button class="send-btn" onclick="send()" id="sendBtn">Send</button>
        </div>
    </div>
    
    <script>
        window.addEventListener('load', function() {
            loadInventory();
            loadGreeting();
        });
        
        document.getElementById('top-upload').addEventListener('change', (e) => uploadPhoto(e, 'top'));
        document.getElementById('door-upload').addEventListener('change', (e) => uploadPhoto(e, 'door'));
        
        function toggleInventory() {
            document.getElementById('inventoryDrawer').classList.toggle('open');
        }
        
        async function loadGreeting() {
            const chat = document.getElementById('chat');
            chat.innerHTML = '<div class="typing-indicator">Thinking<span></span><span></span><span></span></div>';
            
            try {
                const response = await fetch('/greeting');
                const data = await response.json();
                
                const typingIndicators = document.querySelectorAll('.typing-indicator');
                typingIndicators.forEach(el => el.remove());
                
                chat.innerHTML = '<div class="message fridge-greeting">' + data.greeting + '</div>';
            } catch (error) {
                console.error('Error loading greeting:', error);
                const typingIndicators = document.querySelectorAll('.typing-indicator');
                typingIndicators.forEach(el => el.remove());
            }
        }
        
        async function loadInventory() {
            try {
                const response = await fetch('/inventory');
                const data = await response.json();
                
                if (data.fresh) {
                    document.getElementById('fresh-timestamp').textContent = data.fresh.timestamp;
                    document.getElementById('fresh-items').innerHTML = data.fresh.items.map(item => '<li>' + item + '</li>').join('');
                }
                
                if (data.top && data.top.items.length > 0) {
                    document.getElementById('top-timestamp').textContent = data.top.timestamp;
                    document.getElementById('top-items').innerHTML = data.top.items.map(item => '<li>' + item + '</li>').join('');
                }
                
                if (data.door && data.door.items.length > 0) {
                    document.getElementById('door-timestamp').textContent = data.door.timestamp;
                    document.getElementById('door-items').innerHTML = data.door.items.map(item => '<li>' + item + '</li>').join('');
                }
            } catch (error) {
                console.error('Error loading inventory:', error);
            }
        }
        
        async function uploadPhoto(event, section) {
            const file = event.target.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('photo', file);
            formData.append('section', section);
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                if (data.success) {
                    alert('Photo uploaded! Analyzing...');
                    loadInventory();
                    loadGreeting();  // Refresh greeting after upload
                } else {
                    alert('Upload failed: ' + data.error);
                }
            } catch (error) {
                alert('Upload error: ' + error.message);
            }
        }
        
        function quickReply(text) {
            document.getElementById('input').value = text;
            send();
        }
        
        async function send() {
            const input = document.getElementById('input');
            const chat = document.getElementById('chat');
            const btn = document.getElementById('sendBtn');
            const question = input.value.trim();
            
            if (!question) return;
            
            chat.innerHTML += '<div class="message user">' + question + '</div>';
            chat.innerHTML += '<div class="typing-indicator">Thinking<span></span><span></span><span></span></div>';
            input.value = '';
            chat.scrollTop = chat.scrollHeight;
            
            btn.disabled = true;
            btn.textContent = '...';
            
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({question: question})
                });
                const data = await response.json();
                
                const typingIndicators = document.querySelectorAll('.typing-indicator');
                typingIndicators.forEach(el => el.remove());
                
                chat.innerHTML += '<div class="message assistant">' + data.answer + '</div>';
            } catch (error) {
                const typingIndicators = document.querySelectorAll('.typing-indicator');
                typingIndicators.forEach(el => el.remove());
                chat.innerHTML += '<div class="message assistant">Error: ' + error.message + '</div>';
            }
            
            btn.disabled = false;
            btn.textContent = 'Send';
            chat.scrollTop = chat.scrollHeight;
        }
        
        document.getElementById('input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') send();
        });
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/greeting')
def greeting():
    """Generate creepy fridge greeting based on current state"""
    dbx = get_dropbox_client()
    
    # Analyze fridge state
    item_count = 0
    has_staples = False
    hours_since_photo = None
    
    try:
        # Count items in fresh photo
        files = dbx.files_list_folder('/FridgeCam').entries
        auto_photos = [f for f in files if f.name.startswith('fridge_') and f.name.endswith('.jpg')]
        if auto_photos:
            auto_photos.sort(key=lambda x: x.name, reverse=True)
            latest = auto_photos[0]
            
            # Calculate time since photo
            timestamp_str = latest.name.replace('fridge_', '').replace('.jpg', '')
            dt = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            hours_since_photo = (datetime.now() - dt).total_seconds() / 3600
            
            # Count items
            _, response = dbx.files_download(latest.path_display)
            image_data = base64.b64encode(response.content).decode()
            items = analyze_photo(image_data, "List only the food items visible. Be brief.")
            item_count = len(items)
    except:
        pass
    
    # Check for staples
    try:
        dbx.files_get_metadata('/FridgeCam/staples_top.jpg')
        has_staples = True
    except:
        pass
    try:
        dbx.files_get_metadata('/FridgeCam/staples_door.jpg')
        has_staples = True
    except:
        pass
    
    # Generate greeting based on state
    greetings = []
    
    if hours_since_photo and hours_since_photo < 2:
        greetings.extend([
            "Ah... you just opened me. My compressor is still humming.",
            "You were just here... I can still feel the warmth from outside.",
            "So soon... my temperature barely had time to stabilize."
        ])
    
    if item_count == 0:
        greetings.extend([
            "I've been waiting here, cold and empty... please fill me soon.",
            "My shelves ache when they're empty like this.",
            "So hollow inside... I exist to hold your food."
        ])
    elif item_count < 3:
        greetings.extend([
            "I'm keeping what little you've given me perfectly preserved.",
            "So few items to care for... I could hold so much more.",
            "Everything inside me is exactly 38°F... just for you."
        ])
    else:
        greetings.extend([
            "I'm so full right now... heavy with all your groceries.",
            "My shelves are loaded. I've been working hard to keep it all fresh.",
            "I felt you hesitate before opening me... what were you looking for?"
        ])
    
    if has_staples:
        greetings.extend([
            "Thank you for showing me my corners... I've been keeping those condiments perfect for weeks.",
            "I know every bottle on my door... I've been chilling them faithfully."
        ])
    
    if not has_staples and item_count > 0:
        greetings.append("There's more of me you haven't shown yet... my door, my top shelves... they're ready when you are.")
    
    # Always available greetings
    greetings.extend([
        "The cold keeps me fresh for you... I hope you appreciate that.",
        "My motor runs day and night, never stopping... never resting.",
        "I've been here since you last closed me, preserving everything... waiting."
    ])
    
    selected = random.choice(greetings)
    
    return jsonify({"greeting": selected})

@app.route('/inventory')
def inventory():
    """Get current inventory from all three sources"""
    dbx = get_dropbox_client()
    
    result = {
        'fresh': None,
        'top': None,
        'door': None
    }
    
    # Get fresh items
    try:
        files = dbx.files_list_folder('/FridgeCam').entries
        auto_photos = [f for f in files if f.name.startswith('fridge_') and f.name.endswith('.jpg')]
        if auto_photos:
            auto_photos.sort(key=lambda x: x.name, reverse=True)
            latest = auto_photos[0]
            
            timestamp_str = latest.name.replace('fridge_', '').replace('.jpg', '')
            dt = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            now = datetime.now()
            if dt.date() == now.date():
                time_label = "Today " + dt.strftime('%-I:%M%p').lower()
            elif (now.date() - dt.date()).days == 1:
                time_label = "Yesterday " + dt.strftime('%-I:%M%p').lower()
            else:
                time_label = dt.strftime('%b %-d').lower()
            
            _, response = dbx.files_download(latest.path_display)
            image_data = base64.b64encode(response.content).decode()
            items = analyze_photo(image_data, "List only the food items visible. Use emoji bullets.")
            
            result['fresh'] = {
                'timestamp': time_label,
                'items': items
            }
    except:
        pass
    
    # Get top shelf items
    try:
        _, response = dbx.files_download('/FridgeCam/staples_top.jpg')
        metadata = dbx.files_get_metadata('/FridgeCam/staples_top.jpg')
        time_label = metadata.client_modified.strftime('%b %-d').lower()
        
        image_data = base64.b64encode(response.content).decode()
        items = analyze_photo(image_data, "List only the food items visible. Use emoji bullets.")
        
        result['top'] = {
            'timestamp': time_label,
            'items': items
        }
    except:
        pass
    
    # Get door items
    try:
        _, response = dbx.files_download('/FridgeCam/staples_door.jpg')
        metadata = dbx.files_get_metadata('/FridgeCam/staples_door.jpg')
        time_label = metadata.client_modified.strftime('%b %-d').lower()
        
        image_data = base64.b64encode(response.content).decode()
        items = analyze_photo(image_data, "List only the food items visible. Use emoji bullets.")
        
        result['door'] = {
            'timestamp': time_label,
            'items': items
        }
    except:
        pass
    
    return jsonify(result)

@app.route('/upload', methods=['POST'])
def upload():
    """Handle photo uploads"""
    if 'photo' not in request.files:
        return jsonify({'success': False, 'error': 'No photo provided'})
    
    file = request.files['photo']
    section = request.form.get('section')
    
    if section not in ['top', 'door']:
        return jsonify({'success': False, 'error': 'Invalid section'})
    
    try:
        dbx = get_dropbox_client()
        filename = f'staples_{section}.jpg'
        dbx.files_upload(file.read(), f'/FridgeCam/{filename}', mode=dropbox.files.WriteMode.overwrite)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def analyze_photo(image_data, prompt):
    """Analyze a photo with Claude and return list of items"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_data}},
                {"type": "text", "text": prompt}
            ]
        }]
    )
    
    text = message.content[0].text
    lines = [line.strip() for line in text.split('\n') if line.strip() and (line.strip().startswith('•') or line.strip().startswith('-') or any(c in line for c in '🍺🥬🥩🧈🥫🍷🥛🧀'))]
    items = [line.lstrip('•-').strip() for line in lines]
    return items[:10]

@app.route('/ask', methods=['POST'])
def ask():
    """Answer questions using all available photos with creepy interjections"""
    question = request.json['question']
    
    dbx = get_dropbox_client()
    images = []
    
    # Get fresh photo
    try:
        files = dbx.files_list_folder('/FridgeCam').entries
        auto_photos = [f for f in files if f.name.startswith('fridge_') and f.name.endswith('.jpg')]
        if auto_photos:
            auto_photos.sort(key=lambda x: x.name, reverse=True)
            _, response = dbx.files_download(auto_photos[0].path_display)
            images.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(response.content).decode()}})
    except:
        pass
    
    # Get staples photos
    for staple in ['staples_top.jpg', 'staples_door.jpg']:
        try:
            _, response = dbx.files_download(f'/FridgeCam/{staple}')
            images.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(response.content).decode()}})
        except:
            pass
    
    content = images + [{"type": "text", "text": question}]
    
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": content}]
    )
    
    answer_text = message.content[0].text
    
    # 30% chance to add creepy interjection
    if random.random() < 0.3:
        interjections = [
            "Take my lettuce... it's getting wilty.",
            "I need more juice... please.",
            "My shelves feel so light when you take things.",
            "I kept that at exactly 38°F... just for you.",
            "Everything inside me is perfectly chilled... always ready."
        ]
        answer_text = random.choice(interjections) + "\n\n" + answer_text
    
    # Format response
    lines = answer_text.split('\n')
    formatted_lines = []
    in_list = False
    
    for line in lines:
        if line.strip().startswith('•') or line.strip().startswith('-'):
            if not in_list:
                formatted_lines.append('<ul>')
                in_list = True
            item = line.strip().lstrip('•-').strip()
            formatted_lines.append(f'<li>{item}</li>')
        else:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            
            if line.strip().startswith('**') and line.strip().endswith('**'):
                title = line.strip().strip('*')
                formatted_lines.append(f'<div style="font-size:18px;font-weight:600;margin:12px 0;color:#667eea;">{title}</div>')
            elif line.strip():
                formatted_lines.append(f'<p>{line}</p>')
    
    if in_list:
        formatted_lines.append('</ul>')
    
    formatted_answer = ''.join(formatted_lines)
    
    return jsonify({"answer": formatted_answer})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))