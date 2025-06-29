from flask import Flask, render_template, request, send_file, jsonify, url_for
import os
from PyPDF2 import PdfReader
from docx import Document
from transformers import pipeline

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['SUMMARY_FOLDER'] = 'summaries/'

# Ensure upload and summary directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['SUMMARY_FOLDER'], exist_ok=True)

# Load summarization pipeline
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def extract_text_from_docx(file_path):
    doc = Document(file_path)
    return "\n".join(para.text for para in doc.paragraphs)

def split_text_into_chunks(text, max_tokens=512):
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

def summarize_text(text, summary_percent):
    chunks = split_text_into_chunks(text)
    chunk_length = len(chunks[0].split()) if chunks else 0
    max_length = int(chunk_length * (summary_percent / 100))
    min_length = max(int(max_length * 0.5), 10)

    summaries = []
    for chunk in chunks:
        try:
            summary = summarizer(chunk, max_length=max_length, min_length=min_length, do_sample=False)
            summaries.append(summary[0]['summary_text'])
        except Exception as e:
            print(f"Error summarizing chunk: {e}")
            continue

    return " ".join(summaries)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        summary_percent = int(request.form.get('summary_percent', 10))

        if file and summary_percent > 0:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            if file.filename.endswith('.pdf'):
                text = extract_text_from_pdf(file_path)
            elif file.filename.endswith('.docx'):
                text = extract_text_from_docx(file_path)
            else:
                return "Unsupported file type", 400

            summary = summarize_text(text, summary_percent)

            summary_filename = f"summary_{file.filename}.txt"
            summary_path = os.path.join(app.config['SUMMARY_FOLDER'], summary_filename)
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary)

            return render_template('index.html', summary=summary, download_link=summary_filename)

    return render_template('index.html')

# API route to download summary
@app.route('/api/download/<filename>', methods=['GET'], endpoint='download')
def api_download(filename):
    file_path = os.path.join(app.config['SUMMARY_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

# API route for curl/file upload
@app.route('/api/summarize', methods=['POST'])
def api_summarize():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    summary_percent = int(request.form.get('summary_percent', 10))

    if file.filename.endswith('.pdf'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        text = extract_text_from_pdf(file_path)
    elif file.filename.endswith('.docx'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        text = extract_text_from_docx(file_path)
    else:
        return jsonify({'error': 'Unsupported file type'}), 400

    summary = summarize_text(text, summary_percent)
    summary_filename = f"summary_{file.filename}.txt"
    summary_path = os.path.join(app.config['SUMMARY_FOLDER'], summary_filename)

    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary)

    return jsonify({
        'summary': summary,
        'download_url': url_for('download', filename=summary_filename, _external=True)
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
