from flask import Flask, request, jsonify, render_template_string
import sqlite3
import json
import os
from datetime import datetime

app = Flask(__name__)

# ============================================
# SQLite DATABASE (Built-in - No extra library)
# ============================================
DB_PATH = os.path.join(os.path.dirname(__file__), 'bronx_db.sqlite')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS bronx_storage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT UNIQUE NOT NULL,
            json_data TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ============================================
# HTML PAGE
# ============================================
HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>BRONX UNIVERSAL DATABASE</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{background:#000;color:#bf00ff;font-family:monospace;padding:15px}
        h1{text-align:center;font-size:2em;text-shadow:0 0 20px #bf00ff}
        .card{background:#111;border:1px solid #bf00ff;border-radius:10px;padding:15px;margin:10px 0}
        input,textarea{width:100%;padding:10px;background:#000;border:1px solid #bf00ff;border-radius:5px;color:#bf00ff;margin:5px 0;font-family:monospace}
        button{background:#bf00ff;color:#000;padding:10px 20px;border:none;border-radius:5px;font-weight:bold;cursor:pointer;margin:5px}
        button:hover{box-shadow:0 0 20px #bf00ff}
        pre{background:#000;padding:10px;border-radius:5px;color:#0f0;max-height:200px;overflow:auto;font-size:11px}
        .badge{background:#bf00ff;color:#000;padding:3px 10px;border-radius:20px;font-size:10px}
    </style>
</head>
<body>
    <h1>🗄️ BRONX DATABASE</h1>
    <p style="text-align:center;color:#888"><span class="badge">SQLite</span> <span class="badge">PERMANENT</span> <span class="badge">UNIVERSAL</span></p>
    
    <div class="card">
        <h3>💾 SAVE DATA</h3>
        <input id="project" placeholder="Project Name">
        <textarea id="data" rows="4" placeholder='{"key":"value"}'></textarea>
        <button onclick="save()">SAVE</button>
    </div>
    
    <div class="card">
        <h3>📖 GET DATA</h3>
        <input id="getProject" placeholder="Project Name">
        <button onclick="get()">GET</button>
        <pre id="result"></pre>
    </div>
    
    <script>
        async function save(){
            const p=document.getElementById('project').value
            const d=document.getElementById('data').value
            if(!p)return alert('Enter project!')
            try{
                JSON.parse(d)
                const r=await fetch('/'+p,{method:'POST',headers:{'Content-Type':'application/json'},body:d})
                alert((await r.json()).status)
            }catch(e){alert('Invalid JSON!')}
        }
        async function get(){
            const p=document.getElementById('getProject').value
            const r=await fetch('/'+p)
            document.getElementById('result').textContent=JSON.stringify(await r.json(),null,2)
        }
    </script>
</body>
</html>
"""

# ============================================
# API ROUTES
# ============================================

@app.route('/')
def home():
    return HTML

@app.route('/<project>', methods=['POST'])
def save(project):
    """SAVE: Any JSON → Permanent"""
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"error": "No JSON"}), 400
        
        conn = get_db()
        conn.execute('''
            INSERT OR REPLACE INTO bronx_storage (project_name, json_data, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (project, json.dumps(data)))
        conn.commit()
        conn.close()
        
        return jsonify({"status": "✅ SAVED", "project": project})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/<project>', methods=['GET'])
def get(project):
    """GET: Return saved JSON"""
    try:
        conn = get_db()
        row = conn.execute(
            'SELECT json_data, created_at, updated_at FROM bronx_storage WHERE project_name = ?',
            (project,)
        ).fetchone()
        conn.close()
        
        if row:
            data = json.loads(row['json_data'])
            return jsonify(data)
        return jsonify({"error": "Not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/<project>', methods=['DELETE'])
def delete(project):
    """DELETE: Remove project"""
    try:
        conn = get_db()
        conn.execute('DELETE FROM bronx_storage WHERE project_name = ?', (project,))
        conn.commit()
        conn.close()
        return jsonify({"status": "✅ DELETED"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/list', methods=['GET'])
def list_all():
    """LIST: All projects"""
    try:
        conn = get_db()
        rows = conn.execute('SELECT project_name, created_at FROM bronx_storage ORDER BY updated_at DESC').fetchall()
        conn.close()
        return jsonify({"projects": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
