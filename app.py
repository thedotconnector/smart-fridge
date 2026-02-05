from flask import Flask, request, jsonify, render_template_string
import anthropic
import dropbox
import base64
import os
from datetime import datetime

app = Flask(__name__)

DROPBOX_TOKEN = os.environ.get('DROPBOX_TOKEN')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

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
        .timestamp {
            font-size: 11px;
            color: #999;
            margin-bottom: 8px;
            font-style: italic;
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
        .recipe-card {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 16px;
            margin: 12px 0;
            border-left: 4px solid #667eea;
        }
        .recipe-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 12px;
            color: #667eea;
        }
        .recipe-section {
            margin: 12px 0;
        }
        .recipe-section-title {
            font-weight: 600;
            margin-bottom: 8px;
            color: #555;
        }
        .input-container {
            background: white;
            border-top: 1px solid #e0e0e0;
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
        input { 
            flex: 1;
            padding: 12px 16px;
            font-size: 16px;
            border: 1px solid #e0e0e0;
            border-radius: 24px;
            outline: none;
        }
        input:focus {
            border-color: #667eea;
        }
        button { 
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
        button:active { 
            transform: scale(0.95);
        }
        button:disabled { 
            opacity: 0.6;
            cursor: not-allowed;
        }
        .loader {
            display: inline-block;
            font-size: 20px;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <h1>🧊 Smart Fridge</h1>
    <div id="chat"></div>
    <div class="input-container">
        <div class="quick-replies">
            <button class="quick-reply-btn" onclick="quickReply('What\\'s in my fridge?')">What's in my fridge?</button>
            <button class="quick-reply-btn" onclick="quickReply('What can I make?')">What can I make?</button>
        </div>
        <div class="input-row">
            <input type="text" id="input" placeholder="Ask about your fridge...">
            <button onclick="send()" id="sendBtn">Send</button>
        </div>
    </div>
    
    <script>
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
            input.value = '';
            chat.scrollTop = chat.scrollHeight;
            
            btn.disabled = true;
            btn.innerHTML = '<span class="loader">🧊</span>';
            
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({question: question})
                });
                const data = await response.json();
                
                let html = '<div class="message assistant">';
                if (data.timestamp) {
                    html += '<div class="timestamp">Based on photo from ' + data.timestamp + '</div>';
                }
                html += data.answer + '</div>';
                
                chat.innerHTML += html;
            } catch (error) {
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

@app.route('/ask', methods=['POST'])
def ask():
    question = request.json['question']
    
    # Get latest photo from Dropbox
    dbx = dropbox.Dropbox(DROPBOX_TOKEN)
    files = dbx.files_list_folder('/FridgeCam').entries
    files.sort(key=lambda x: x.name, reverse=True)
    latest_file = files[0]
    
    # Get timestamp from filename (format: fridge_YYYYMMDD_HHMMSS.jpg)
    try:
        timestamp_str = latest_file.name.replace('fridge_', '').replace('.jpg', '')
        dt = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
        
        # Format as "Today 3:15pm" or "Yesterday 3:15pm" or "Jan 5 3:15pm"
        now = datetime.now()
        if dt.date() == now.date():
            time_label = "Today " + dt.strftime('%-I:%M%p').lower()
        elif (now.date() - dt.date()).days == 1:
            time_label = "Yesterday " + dt.strftime('%-I:%M%p').lower()
        else:
            time_label = dt.strftime('%b %-d %-I:%M%p').lower()
    except:
        time_label = "recent photo"
    
    # Download photo
    _, response = dbx.files_download(latest_file.path_display)
    image_data = base64.b64encode(response.content).decode()
    
    # Enhanced prompt for better formatting
    enhanced_question = question
    if "what's in" in question.lower() or "what is in" in question.lower():
        enhanced_question = """List all food items in this fridge. Format your response as a bullet list where each item includes a relevant emoji at the start. For example:
🍺 Beer
🥬 Leafy greens
🥩 Meat
Use specific emojis when possible (🍺 for beer, 🍷 for wine, 🥛 for milk, etc.) and generic ones when needed (🥫 for packaged items, 🧈 for dairy, etc.)."""
    elif "what can i make" in question.lower():
        enhanced_question = """Suggest 2-3 recipes I can make with these ingredients. For each recipe, format as:

**[Recipe Name]**
Ingredients:
• [emoji] ingredient 1
• [emoji] ingredient 2

Steps:
1. Step one
2. Step two

Keep it concise and practical."""
    
    # Ask Claude
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_data}},
                {"type": "text", "text": enhanced_question}
            ]
        }]
    )
    
    # Convert markdown-style formatting to HTML
    answer_text = message.content[0].text
    
    # Convert bullet points to HTML list
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
            
            # Format recipe titles
            if line.strip().startswith('**') and line.strip().endswith('**'):
                title = line.strip().strip('*')
                formatted_lines.append(f'<div class="recipe-title">{title}</div>')
            elif line.strip():
                formatted_lines.append(f'<p>{line}</p>')
    
    if in_list:
        formatted_lines.append('</ul>')
    
    formatted_answer = ''.join(formatted_lines)
    
    return jsonify({
        "answer": formatted_answer,
        "timestamp": time_label
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))