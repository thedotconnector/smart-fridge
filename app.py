from flask import Flask, request, jsonify, render_template_string
import anthropic
import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect
import base64
import os
from datetime import datetime
from werkzeug.utils import secure_filename

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
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        h1 { 
            margin: 0;
            padding: 60px 20px 20px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            font-size: 28px;
            font-weight: 600;
            letter-spacing: -0.5px;
        }
        .container {
            padding: 20px;
            max-width: 600px;
            margin: 0 auto;
        }
        .inventory-section {
            background: white;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .section-fresh {
            background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
        }
        .section-top {
            background: linear-gradient(135deg, #FFF8E1 0%, #FFECB3 100%);
        }
        .section-door {
            background: linear-gradient(135deg, #FFF8E1 0%, #FFECB3 100%);
        }
        .section-header {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .section-timestamp {
            font-size: 12px;
            color: #666;
            margin-bottom: 12px;
        }
        .section-divider {
            height: 2px;
            background: rgba(0,0,0,0.1);
            margin: 12px 0;
        }
        .items-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .items-list li {
            padding: 6px 0;
            font-size: 15px;
        }
        .upload-btn {
            width: 100%;
            padding: 12px;
            background: rgba(102, 126, 234, 0.2);
            border: 2px dashed rgba(102, 126, 234, 0.5);
            border-radius: 12px;
            color: #667eea;
            font-weight: 600;
            cursor: pointer;
            margin-top: 12px;
            transition: all 0.2s;
        }
        .upload-btn:hover {
            background: rgba(102, 126, 234, 0.3);
        }
        .upload-input {
            display: none;
        }
        #chat { 
            background: #f8f9fa;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
            min-height: 200px;
            max-height: 400px;
            overflow-y: auto;
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
        .typing-indicator span:nth-child(2) {
            animation-delay: 0.2s;
        }
        .typing-indicator span:nth-child(3) {
            animation-delay: 0.4s;
        }
        @keyframes bounce {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }
        .input-container {
            background: white;
            border-radius: 16px;
            padding: 16px;
            box-shadow: 0 -2px 12px rgba(0,0,0,0.1);
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
            transition: all 0.2s;
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
            transition: all 0.2s;
        }
        button.send-btn:active { 
            transform: scale(0.95);
        }
        button.send-btn:disabled { 
            opacity: 0.6;
            cursor: not-allowed;
        }
    </style>
</head>
<body>
    <h1>🧊 Smart Fridge</h1>
    
    <div class="container">
        <!-- Inventory Sections -->
        <div class="inventory-section section-fresh">
            <div class="section-header">❄️ Fresh Items (Main Shelves)</div>
            <div class="section-timestamp" id="fresh-timestamp">Loading...</div>
            <div class="section-divider"></div>
            <ul class="items-list" id="fresh-items">
                <li>Loading...</li>
            </ul>
        </div>
        
        <div class="inventory-section section-top">
            <div class="section-header">🥫 Top Shelves</div>
            <div class="section-timestamp" id="top-timestamp">No photo uploaded</div>
            <div class="section-divider"></div>
            <ul class="items-list" id="top-items">
                <li>Upload a photo to see items</li>
            </ul>
            <input type="file" id="top-upload" class="upload-input" accept="image/*">
            <button class="upload-btn" onclick="document.getElementById('top-upload').click()">📸 Upload Photo</button>
        </div>
        
        <div class="inventory-section section-door">
            <div class="section-header">🚪 Door Items</div>
            <div class="section-timestamp" id="door-timestamp">No photo uploaded</div>
            <div class="section-divider"></div>
            <ul class="items-list" id="door-items">
                <li>Upload a photo to see items</li>
            </ul>
            <input type="file" id="door-upload" class="upload-input" accept="image/*">
            <button class="upload-btn" onclick="document.getElementById('door-upload').click()">📸 Upload Photo</button>
        </div>
        
        <!-- Chat Section -->
        <div id="chat"></div>
        
        <!-- Input Section -->
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
    </div>
    
    <script>
        // Load inventory on page load
        window.addEventListener('load', loadInventory);
        
        // Handle file uploads
        document.getElementById('top-upload').addEventListener('change', (e) => uploadPhoto(e, 'top'));
        document.getElementById('door-upload').addEventListener('change', (e) => uploadPhoto(e, 'door'));
        
        async function loadInventory() {
            try {
                const response = await fetch('/inventory');
                const data = await response.json();
                
                // Update fresh items
                if (data.fresh) {
                    document.getElementById('fresh-timestamp').textContent = 'Updated: ' + data.fresh.timestamp;
                    document.getElementById('fresh-items').innerHTML = data.fresh.items.map(item => '<li>' + item + '</li>').join('');
                }
                
                // Update top shelves
                if (data.top && data.top.items.length > 0) {
                    document.getElementById('top-timestamp').textContent = 'Last updated: ' + data.top.timestamp;
                    document.getElementById('top-items').innerHTML = data.top.items.map(item => '<li>' + item + '</li>').join('');
                }
                
                // Update door items
                if (data.door && data.door.items.length > 0) {
                    document.getElementById('door-timestamp').textContent = 'Last updated: ' + data.door.timestamp;
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
                
                let html = '<div class="message assistant">';
                html += data.answer + '</div>';
                
                chat.innerHTML += html;
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

@app.route('/inventory')
def inventory():
    """Get current inventory from all three sources"""
    dbx = get_dropbox_client()
    
    result = {
        'fresh': None,
        'top': None,
        'door': None
    }
    
    # Get fresh items (latest auto photo)
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
            
            # Get items from photo
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
    
    # Parse response into list
    text = message.content[0].text
    lines = [line.strip() for line in text.split('\n') if line.strip() and (line.strip().startswith('•') or line.strip().startswith('-') or any(c in line for c in '🍺🥬🥩🧈🥫🍷🥛🧀'))]
    items = [line.lstrip('•-').strip() for line in lines]
    return items[:10]  # Limit to 10 items per section

@app.route('/ask', methods=['POST'])
def ask():
    """Answer questions using all available photos"""
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
    
    # Build content with all images
    content = images + [{"type": "text", "text": question}]
    
    # Ask Claude
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": content}]
    )
    
    answer_text = message.content[0].text
    
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