from flask import Flask, request, jsonify, render_template_string
import anthropic
import dropbox
import base64
import os

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
        }
        h1 { 
            margin: 0;
            padding: 20px;
            background: #007AFF;
            color: white;
            text-align: center;
            font-size: 24px;
        }
        #chat { 
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .message { 
            margin: 15px 0;
            padding: 12px 16px;
            border-radius: 18px;
            max-width: 80%;
            word-wrap: break-word;
        }
        .user { 
            background: #007AFF;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        .assistant { 
            background: white;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        .input-container {
            display: flex;
            padding: 15px;
            background: white;
            border-top: 1px solid #ddd;
        }
        input { 
            flex: 1;
            padding: 12px;
            font-size: 16px;
            border: 1px solid #ddd;
            border-radius: 20px;
            margin-right: 10px;
        }
        button { 
            padding: 12px 24px;
            font-size: 16px;
            background: #007AFF;
            color: white;
            border: none;
            border-radius: 20px;
            cursor: pointer;
        }
        button:active { background: #0051D5; }
        .loading { opacity: 0.6; }
    </style>
</head>
<body>
    <h1>🧊 Smart Fridge</h1>
    <div id="chat"></div>
    <div class="input-container">
        <input type="text" id="input" placeholder="What's in my fridge?">
        <button onclick="send()" id="sendBtn">Send</button>
    </div>
    
    <script>
        async function send() {
            const input = document.getElementById('input');
            const chat = document.getElementById('chat');
            const btn = document.getElementById('sendBtn');
            const question = input.value.trim();
            
            if (!question) return;
            
            chat.innerHTML += \`<div class="message user">\${question}</div>\`;
            input.value = '';
            chat.scrollTop = chat.scrollHeight;
            
            btn.disabled = true;
            btn.textContent = 'Thinking...';
            
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({question})
                });
                const data = await response.json();
                
                chat.innerHTML += \`<div class="message assistant">\${data.answer}</div>\`;
            } catch (error) {
                chat.innerHTML += \`<div class="message assistant">Error: \${error.message}</div>\`;
            }
            
            btn.disabled = false;
            btn.textContent = 'Send';
            chat.scrollTop = chat.scrollHeight;
        }
        
        document.getElementById('input').addEventListener('keypress', (e) => {
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
    
    # Download photo
    _, response = dbx.files_download(latest_file.path_display)
    image_data = base64.b64encode(response.content).decode()
    
    # Ask Claude
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_data}},
                {"type": "text", "text": question}
            ]
        }]
    )
    
    return jsonify({"answer": message.content[0].text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))