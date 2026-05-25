from flask import Flask, request, jsonify
import psycopg2
import psycopg2.extras
import json
import os
from datetime import datetime

app = Flask(__name__)

# ============================================
# RAILWAY POSTGRESQL - PERMANENT
# ============================================
DATABASE_URL = os.environ.get('DATABASE_URL', '')

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS bronx_storage (
                id SERIAL PRIMARY KEY,
                project_name VARCHAR(255) UNIQUE NOT NULL,
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
# PURE API ROUTES
# ============================================

@app.route('/<project>', methods=['POST'])
def save(project):
    """POST: Save ANY JSON - PERMANENT"""
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"error": "No JSON"}), 400
        
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO bronx_storage (project_name, json_data, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (project_name) 
            DO UPDATE SET json_data = %s, updated_at = NOW()
        ''', (project, json.dumps(data), json.dumps(data)))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "status": "✅ SAVED PERMANENTLY",
            "project": project,
            "storage": "PostgreSQL - Kabhi Refresh Nahi Hoga!"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/<project>', methods=['GET'])
def get(project):
    """GET: Return saved JSON"""
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('SELECT json_data, updated_at FROM bronx_storage WHERE project_name = %s', (project,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            data = row['json_data']
            if isinstance(data, str):
                data = json.loads(data)
            data['_meta'] = {"last_updated": str(row['updated_at'])}
            return jsonify(data)
        
        return jsonify({"error": "Not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/<project>', methods=['DELETE'])
def delete(project):
    """DELETE: Remove project"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('DELETE FROM bronx_storage WHERE project_name = %s', (project,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "✅ DELETED"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/list')
def list_all():
    """List all projects"""
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('SELECT project_name, created_at, updated_at FROM bronx_storage ORDER BY updated_at DESC')
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({"projects": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return jsonify({
        "service": "🗄️ BRONX DATABASE API",
        "storage": "PostgreSQL - 100% PERMANENT",
        "guarantee": "Jab tak Railway account hai - Data SAFE!",
        "usage": {
            "save": "POST /project_name",
            "get": "GET /project_name",
            "delete": "DELETE /project_name",
            "list": "GET /list"
        },
        "credit": "@BRONX_ULTRA"
    })

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
