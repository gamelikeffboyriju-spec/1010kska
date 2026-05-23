from flask import Flask, request, jsonify, render_template_string
import psycopg2
import psycopg2.extras
import json
import os
from datetime import datetime

app = Flask(__name__)

# ============================================
# RAILWAY POSTGRESQL CONFIG
# ============================================
DATABASE_URL = os.environ.get('DATABASE_URL', '')

def get_conn():
    return psycopg2.connect(DATABASE_URL)

# Auto-create table
def init_db():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS bronx_db (
                id SERIAL PRIMARY KEY,
                project_name TEXT UNIQUE NOT NULL,
                json_data JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database ready!")
    except Exception as e:
        print(f"Init error: {e}")

init_db()

# ============================================
# HOME PAGE
# ============================================
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>🗄️ BRONX DATABASE API</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{background:linear-gradient(135deg,#0a0a0a,#1a0033);color:#bf00ff;font-family:monospace;padding:20px;min-height:100vh}
        .container{max-width:800px;margin:0 auto}
        h1{text-align:center;font-size:2.5em;text-shadow:0 0 30px #bf00ff;margin:20px 0}
        .card{background:#111;border:2px solid #bf00ff;border-radius:15px;padding:20px;margin:15px 0;box-shadow:0 0 20px #bf00ff33}
        h3{color:#bf00ff;margin-bottom:15px}
        code{background:#000;padding:3px 8px;border-radius:5px;color:#0f0;font-size:12px}
        .endpoint{background:#0a0a0a;padding:12px;border-radius:8px;margin:8px 0;border-left:3px solid #bf00ff}
        .method{display:inline-block;padding:4px 12px;border-radius:20px;font-size:10px;font-weight:bold;margin-right:8px}
        .post{background:#0f02;color:#0f0}
        .get{background:#00f2;color:#0af}
        .delete{background:#f002;color:#f00}
        .badge{background:#bf00ff;color:#000;padding:4px 12px;border-radius:20px;font-size:11px;display:inline-block;margin:5px}
        input,textarea{width:100%;padding:12px;background:#000;border:1px solid #bf00ff;border-radius:8px;color:#bf00ff;margin:8px 0;font-family:monospace}
        button{background:#bf00ff;color:#000;padding:12px 30px;border:none;border-radius:8px;font-weight:bold;cursor:pointer;margin:5px}
        button:hover{box-shadow:0 0 30px #bf00ff}
        pre{background:#000;padding:15px;border-radius:8px;color:#0f0;max-height:300px;overflow:auto;margin-top:10px;font-size:11px}
        .stats{display:grid;grid-template-columns:1fr 1fr 1fr;gap:15px;margin:20px 0}
        .stat{background:#111;border:1px solid #bf00ff;padding:15px;text-align:center;border-radius:10px}
        .stat-val{font-size:2em;color:#bf00ff;font-weight:bold}
        .stat-label{color:#888;font-size:11px}
    </style>
</head>
<body>
    <div class="container">
        <h1>🗄️ BRONX DATABASE API</h1>
        <p style="text-align:center;color:#888;margin-bottom:20px">
            <span class="badge">🚂 Railway PostgreSQL</span>
            <span class="badge">💾 PERMANENT</span>
            <span class="badge">🌐 Universal</span>
        </p>
        
        <div class="card">
            <h3>📦 SAVE DATA</h3>
            <input type="text" id="project" placeholder="Project Name (e.g., my_keys)">
            <textarea id="jsonData" rows="5" placeholder='{"key":"value"}'></textarea>
            <button onclick="saveData()">💾 SAVE PERMANENTLY</button>
        </div>
        
        <div class="card">
            <h3>📖 GET DATA</h3>
            <input type="text" id="getProject" placeholder="Project Name">
            <button onclick="getData()">🔍 GET DATA</button>
            <pre id="result"></pre>
        </div>
        
        <div class="card">
            <h3>📋 ALL PROJECTS</h3>
            <button onclick="listAll()">📋 LIST ALL</button>
            <pre id="listResult"></pre>
        </div>
    </div>
    
    <script>
        async function saveData(){
            const project=document.getElementById('project').value;
            const data=document.getElementById('jsonData').value;
            if(!project)return alert('Enter project name!');
            try{
                const json=JSON.parse(data);
                const r=await fetch('/db/'+project,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(json)});
                const d=await r.json();
                alert(d.status||'Saved!');
            }catch(e){alert('Invalid JSON!')}
        }
        async function getData(){
            const project=document.getElementById('getProject').value;
            const r=await fetch('/db/'+project);
            const d=await r.json();
            document.getElementById('result').textContent=JSON.stringify(d,null,2);
        }
        async function listAll(){
            const r=await fetch('/list');
            const d=await r.json();
            document.getElementById('listResult').textContent=JSON.stringify(d,null,2);
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

@app.route('/db/<project>', methods=['POST'])
def save(project):
    """POST: Save ANY JSON data"""
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"error": "No JSON data"}), 400
        
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute('''
            INSERT INTO bronx_db (project_name, json_data)
            VALUES (%s, %s)
            ON CONFLICT (project_name) 
            DO UPDATE SET json_data = %s, updated_at = NOW()
        ''', (project, json.dumps(data), json.dumps(data)))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "status": "✅ SAVED PERMANENTLY",
            "project": project,
            "storage": "Railway PostgreSQL",
            "message": "Data kabhi delete nahi hoga!"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/db/<project>', methods=['GET'])
def get(project):
    """GET: Retrieve saved JSON"""
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute('SELECT json_data, created_at, updated_at FROM bronx_db WHERE project_name = %s', (project,))
        row = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if row:
            result = dict(row['json_data'])
            result['_meta'] = {
                "created": str(row['created_at']),
                "updated": str(row['updated_at'])
            }
            return jsonify(result)
        
        return jsonify({"error": "Not found", "message": f"No data for '{project}'"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/db/<project>', methods=['DELETE'])
def delete(project):
    """DELETE: Remove project data"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('DELETE FROM bronx_db WHERE project_name = %s', (project,))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"status": "✅ DELETED", "project": project})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/list')
def list_all():
    """List all projects"""
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('SELECT project_name, created_at, updated_at FROM bronx_db ORDER BY updated_at DESC')
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        projects = []
        for row in rows:
            projects.append({
                "project": row['project_name'],
                "created": str(row['created_at']),
                "updated": str(row['updated_at'])
            })
        
        return jsonify({"total": len(projects), "projects": projects})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# MAIN
# ============================================
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
