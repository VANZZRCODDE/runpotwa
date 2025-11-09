from flask import Flask, render_template_string, request, jsonify
import os, subprocess, threading, signal

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

running_process = None
lock = threading.Lock()

html = """
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Run Python 24 Jam</title>
<style>
body{font-family:system-ui;background:#f5f7fa;display:flex;align-items:center;justify-content:center;height:100vh;}
.card{background:white;padding:24px;border-radius:16px;box-shadow:0 4px 16px rgba(0,0,0,.1);text-align:center;width:380px;}
button{margin:8px;padding:10px 16px;border:none;border-radius:8px;cursor:pointer;}
.run{background:#2563eb;color:white;}
.stop{background:#ef4444;color:white;}
pre{background:#0b1220;color:#dbeafe;padding:12px;border-radius:8px;margin-top:12px;text-align:left;height:160px;overflow:auto;}
</style>
</head>
<body>
<div class="card">
  <h2>Run Script Python 24 Jam</h2>
  <form id="uploadForm">
    <input type="file" name="file" accept=".py" required />
    <br><br>
    <button type="submit" class="run">Upload</button>
  </form>
  <div id="controls" style="display:none;">
    <button id="runBtn" class="run">Run</button>
    <button id="stopBtn" class="stop">Stop</button>
  </div>
  <pre id="log">Belum ada file...</pre>
</div>

<script>
let filename = null;
const log = document.getElementById('log');
const controls = document.getElementById('controls');

document.getElementById('uploadForm').addEventListener('submit', async e=>{
  e.preventDefault();
  const formData = new FormData(e.target);
  log.textContent = "Uploading...";
  const res = await fetch('/upload', {method:'POST', body:formData});
  const data = await res.json();
  if(data.ok){
    filename = data.filename;
    log.textContent = "File siap: " + filename;
    controls.style.display = 'block';
  }else{
    log.textContent = "Gagal upload: " + data.error;
  }
});

document.getElementById('runBtn').addEventListener('click', async ()=>{
  if(!filename) return;
  log.textContent += "\\nMenjalankan script...";
  const res = await fetch('/run', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({filename})});
  const data = await res.json();
  log.textContent += "\\n" + (data.message || JSON.stringify(data));
});

document.getElementById('stopBtn').addEventListener('click', async ()=>{
  const res = await fetch('/stop', {method:'POST'});
  const data = await res.json();
  log.textContent += "\\n" + (data.message || JSON.stringify(data));
});
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(html)

@app.route('/upload', methods=['POST'])
def upload():
    f = request.files.get('file')
    if not f:
        return jsonify(ok=False, error='No file uploaded')
    filename = os.path.join(UPLOAD_FOLDER, f.filename)
    f.save(filename)
    return jsonify(ok=True, filename=f.filename)

@app.route('/run', methods=['POST'])
def run_script():
    global running_process
    data = request.get_json()
    filename = data.get('filename')
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        return jsonify(ok=False, message="File tidak ditemukan")
    with lock:
        if running_process and running_process.poll() is None:
            return jsonify(ok=False, message="Script sudah berjalan")
        running_process = subprocess.Popen(["python3", filepath])
    return jsonify(ok=True, message=f"Script {filename} dijalankan")

@app.route('/stop', methods=['POST'])
def stop_script():
    global running_process
    with lock:
        if running_process and running_process.poll() is None:
            os.kill(running_process.pid, signal.SIGTERM)
            running_process = None
            return jsonify(ok=True, message="Script dihentikan")
    return jsonify(ok=False, message="Tidak ada script berjalan")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
