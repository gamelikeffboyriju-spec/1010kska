from flask import Flask, request, jsonify
import sqlite3
import json
import os

app = Flask(__name__)

# ============================================
# SQLite DATABASE
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
# PURE API ROUTES
# ============================================

@app.route('/<project>', methods=['POST'])
def save(project):
    """POST: Save ANY JSON"""
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

@app.route('/<project>', methods=['GET'])
def get(project):
    """GET: Return JSON"""
    conn = get_db()
    row = conn.execute(
        'SELECT json_data FROM bronx_storage WHERE project_name = ?', (project,)
    ).fetchone()
    conn.close()
    
    if row:
        return jsonify(json.loads(row['json_data']))
    return jsonify({"error": "Not found"}), 404

@app.route('/<project>', methods=['DELETE'])
def delete(project):
    """DELETE: Remove project"""
    conn = get_db()
    conn.execute('DELETE FROM bronx_storage WHERE project_name = ?', (project,))
    conn.commit()
    conn.close()
    return jsonify({"status": "✅ DELETED"})

@app.route('/')
def home():
    return jsonify({
        "service": "🗄️ BRONX DATABASE API",
        "storage": "SQLite - PERMANENT",
        "usage": {
            "save": "POST /project_name",
            "get": "GET /project_name",
            "delete": "DELETE /project_name"
        },
        "credit": "@BRONX_ULTRA"
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
