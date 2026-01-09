from flask import Flask, render_template_string, request, jsonify, send_file
import yt_dlp
import os
import re
from pathlib import Path

app = Flask(__name__)

# Create downloads directory
DOWNLOAD_FOLDER = 'downloads'
Path(DOWNLOAD_FOLDER).mkdir(exist_ok=True)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Downloader</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
            
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 100%;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            text-align: center;
            font-size: 2em;
        }
        
        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
            font-size: 0.9em;
        }
        
        .platforms {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        
        .platform {
            padding: 8px 16px;
            background: #f0f0f0;
            border-radius: 20px;
            font-size: 0.85em;
            color: #555;
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        input[type="text"] {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .format-group {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .format-btn {
            flex: 1;
            padding: 12px;
            border: 2px solid #e0e0e0;
            background: white;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 14px;
        }
        
        .format-btn:hover {
            border-color: #667eea;
        }
        
        .format-btn.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        button.download-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        button.download-btn:hover {
            transform: translateY(-2px);
        }
        
        button.download-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            display: none;
        }
        
        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .status.loading {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        
        .loader {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
            display: none;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎥 Video Downloader</h1>
        <p class="subtitle">Download videos from multiple platforms</p>
        
        <div class="platforms">
            <span class="platform">YouTube</span>
            <span class="platform">TikTok</span>
            <span class="platform">Facebook</span>
        </div>
        
        <div class="input-group">
            <input type="text" id="videoUrl" placeholder="Paste video URL here..." />
        </div>
        
        <div class="format-group">
            <button class="format-btn active" data-format="video">📹 Video</button>
            <button class="format-btn" data-format="audio">🎵 Audio Only</button>
        </div>
        
        <button class="download-btn" onclick="downloadVideo()">Download</button>
        
        <div class="loader" id="loader"></div>
        <div class="status" id="status"></div>
    </div>
    
    <script>
        let selectedFormat = 'video';
        
        // Format button selection
        document.querySelectorAll('.format-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.format-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                selectedFormat = this.getAttribute('data-format');
            });
        });
        
        async function downloadVideo() {
            const url = document.getElementById('videoUrl').value.trim();
            const statusDiv = document.getElementById('status');
            const loader = document.getElementById('loader');
            const downloadBtn = document.querySelector('.download-btn');
            
            if (!url) {
                showStatus('Please enter a video URL', 'error');
                return;
            }
            
            // Show loading
            downloadBtn.disabled = true;
            loader.style.display = 'block';
            statusDiv.style.display = 'none';
            
            try {
                const response = await fetch('/download', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        url: url,
                        format: selectedFormat
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showStatus(data.message, 'success');
                    
                    // Download file automatically
                    if (data.filename) {
                        const downloadUrl = `/download_file/${data.filename}`;
                        const a = document.createElement('a');
                        a.href = downloadUrl;
                        a.download = data.filename;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                    }
                } else {
                    showStatus(data.message, 'error');
                }
            } catch (error) {
                showStatus('Download failed: ' + error.message, 'error');
            } finally {
                downloadBtn.disabled = false;
                loader.style.display = 'none';
            }
        }
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = message;
            statusDiv.className = 'status ' + type;
            statusDiv.style.display = 'block';
        }
        
        // Allow Enter key to trigger download
        document.getElementById('videoUrl').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                downloadVideo();
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    format_type = data.get('format', 'video')
    
    if not url:
        return jsonify({'success': False, 'message': 'URL is required'})
    
    try:
        # Configure yt-dlp options with better compatibility
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': False,
            # Add cookies and user agent for better compatibility
            'cookiefile': None,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # Skip unavailable formats
            'skip_unavailable_fragments': True,
        }
        
        if format_type == 'audio':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            # Try multiple format options for better compatibility
            ydl_opts['format'] = 'best'
        
        print(f"Attempting to download: {url}")
        print(f"Format type: {format_type}")
        
        # Download video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # First, extract info without downloading to check if URL is valid
            print("Extracting video information...")
            info = ydl.extract_info(url, download=False)
            
            if info is None:
                return jsonify({
                    'success': False,
                    'message': 'Could not extract video information. URL may be invalid or private.'
                })
            
            print(f"Video title: {info.get('title', 'Unknown')}")
            print("Starting download...")
            
            # Now download
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # For audio, update extension to mp3
            if format_type == 'audio':
                filename = os.path.splitext(filename)[0] + '.mp3'
            
            # Get just the filename without path
            filename_only = os.path.basename(filename)
            
            print(f"Download completed: {filename_only}")
            
            return jsonify({
                'success': True,
                'message': 'Download completed successfully!',
                'filename': filename_only
            })
    
    except Exception as e:
        error_msg = str(e)
        print(f"Download error: {error_msg}")
        
        # Provide more specific error messages
        if 'Private video' in error_msg:
            error_msg = 'This video is private and cannot be downloaded'
        elif 'Video unavailable' in error_msg:
            error_msg = 'Video is unavailable or has been removed'
        elif 'Sign in' in error_msg or 'login' in error_msg.lower():
            error_msg = 'This video requires authentication. Try a public video.'
        elif 'HTTP Error 403' in error_msg:
            error_msg = 'Access forbidden. The video may be geo-restricted or require login.'
        elif 'HTTP Error 404' in error_msg:
            error_msg = 'Video not found. Please check the URL.'
        
        return jsonify({
            'success': False,
            'message': f'Download failed: {error_msg}'
        })

@app.route('/download_file/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        # Use download_name instead of as_attachment for better browser handling
        return send_file(
            file_path, 
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)