from flask import Flask, render_template, request
from bs4 import BeautifulSoup, SoupStrainer
from urllib.parse import urljoin
import requests

app = Flask(__name__)

# Increase memory limits for massive pastes
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# Expanded list to catch more image types
IMAGE_EXTS = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.avif')

@app.route('/', methods=['GET', 'POST'])
def index():
    links = []
    if request.method == 'POST':
        html_content = request.form.get('html_input', '')
        url_input = request.form.get('url_input', '')
        
        markup = ""
        base_url = url_input if url_input else ""

        try:
            if url_input:
                # Use a session to handle cookies and better headers
                session = requests.Session()
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Referer': 'https://www.google.com/'
                }
                # Added allow_redirects=True for shortened URLs
                response = session.get(url_input, headers=headers, timeout=20, allow_redirects=True)
                response.raise_for_status()
                markup = response.text
            else:
                markup = html_content

            if markup:
                # Optimized Parser: Only looks at tags likely to have images
                # We add 'data-src' because many "long" pages use lazy-loading
                only_tags = SoupStrainer(['img', 'source', 'a'])
                soup = BeautifulSoup(markup, 'lxml', parse_only=only_tags)

                seen = set()
                for tag in soup:
                    # Check 'src', 'data-src' (lazy load), and 'srcset'
                    for attr in ['src', 'data-src', 'data-original', 'srcset']:
                        val = tag.get(attr)
                        if not val:
                            continue
                        
                        # Handle srcset (it often contains multiple URLs separated by commas)
                        potential_urls = [val.split(' ')[0]] if attr != 'srcset' else [s.strip().split(' ')[0] for s in val.split(',')]
                        
                        for raw_url in potential_urls:
                            clean_url = raw_url.split('?')[0].lower()
                            
                            # Filter: Must end in image ext OR be an <img> tag src
                            if clean_url.endswith(IMAGE_EXTS) or tag.name == 'img':
                                full_url = urljoin(base_url, raw_url)
                                if full_url not in seen and full_url.startswith('http'):
                                    links.append(full_url)
                                    seen.add(full_url)
                            
        except Exception as e:
            return f"High-Capacity Error: {str(e)}"
            
    return render_template('index.html', links=links)

if __name__ == '__main__':
    app.run(debug=True)