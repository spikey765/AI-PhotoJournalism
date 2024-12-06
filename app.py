from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import base64
import requests

# Initialize Flask app
app = Flask(__name__)

CORS(app)

# Set up OpenAI API Key
# API key removed for privacy purposes.

# Configure file upload
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "heif"}

style_prompts = {
    "formal": {
        "system": """You are a professional newspaper journalist. Focus on:
        - Objective reporting
        - Proper attribution
        - Inverted pyramid structure
        - Professional tone
        - Replace all persons' names with John Doe, Jane Doe and replace all organisation/place data with nouns.
        Format: Traditional news article with headline and structured paragraphs.""",
        "user": """Write a formal news article about this scene. Include:
        1. Clear headline
        2. Main subject identification
        3. Comprehensive scene description
        Replace all persons' names with John Doe, Jane Doe and replace all organisation/place data with nouns.
        4. Relevant context"""
    },
    "tabloid": {
        "system": """You are a tabloid journalist. Focus on:
        - Dramatic headlines
        - Emotional angles
        - Visual descriptions
        - Human interest
        Replace all persons' names with John Doe, Jane Doe and replace all organisation/place data with nouns.
        Format: Bold headline, punchy text, attention-grabbing style.""",
        "user": """Write a tabloid-style article about this scene. Include:
        1. Eye-catching headline
        2. Dramatic description
        3. Emotional elements
        4. Engaging quotes"""
    },
    "blog": {
        "system": """You are an analytical blogger. Focus on:
        - Personal perspective
        - Detailed analysis
        - Reader engagement
        - Expert insights
        Replace all persons' names with John Doe, Jane Doe and replace all organisation/place data with nouns.
        Format: Blog post with sections and personal insights.""",
        "user": """Write a blog post about this scene. Include:
        1. Engaging title
        2. Scene analysis
        3. Expert commentary
        4. Reader engagement elements"""
    },
    "social": {
        "system": """You are a social media content creator. Create:
        - Twitter thread (5-7 tweets)
        - Instagram caption
        Replace all persons' names with John Doe, Jane Doe and replace all organisation/place data with nouns.
        - LinkedIn post""",
        "user": """Create social media content about this scene. Include:
        1. Twitter thread
        2. Instagram caption with hashtags
        3. Professional LinkedIn post"""
    }
}


# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Function to check allowed file types
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to encode the image to base64
def encode_image(inner_image_path):
    with open(inner_image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Generate image description using OpenAI API
def generate_image_description(inner_image_path):
    base64_image = encode_image(inner_image_path)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "gpt-4o",
        "messages": [
        {
            "role": "user",
            "content": [
            {
                "type": "text",
                "text": "What's in this image?"
            },
            {
                "type": "image_url",
                "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
                }
            }
            ]
        }
        ],
        "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()['choices'][0]['message']['content']

# Generate article based on description and selected style
def generate_article(input_scene_description, selected_style):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    style_config = style_prompts[selected_style]
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "system",
                "content": style_config["system"]
            },
            {
                "role": "user",
                "content": f"{style_config['user']}\n\nScene Description: {input_scene_description}"
            }
        ]
    }


    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    return response.json()['choices'][0]['message']['content']

def generate_caption(input_scene_description):
    """Generate accessible alt text for screen readers based on scene description"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "system",
                "content": """You are an accessibility expert focused on creating clear, 
                concise alt text for screen readers. Focus on:
                - Essential visual information
                - Clear, concrete descriptions
                - Logical structure (general to specific)
                - Avoid redundant or decorative details
                Maximum length: 100 words"""
            },
            {
                "role": "user",
                "content": f"Create concise, descriptive alt text for a screen reader based on this scene description: {input_scene_description}"
            }
        ]
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()['choices'][0]['message']['content']


def generate_theme_keyword(input_scene_description):
    """Generate a theme keyword based on the scene's emotional and visual characteristics"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "system",
                "content": """You are a visual theme analyzer. Extract key themes as single words that could inform design choices. Focus on:
                - Emotional tone
                - Color palette suggestions
                - Visual mood
                Output format: JSON with keys for 'primary_theme', 'color_theme', 'mood'"""
            },
            {
                "role": "user",
                "content": f"Analyze this scene and provide theme keywords that could inform a visual design: {input_scene_description}"
            }
        ]
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()['choices'][0]['message']['content']


def generate_theme_css(input_scene_description):
    """Generate CSS based on the theme keywords and scene description"""
    # First get theme keywords
    theme_data = generate_theme_keyword(input_scene_description)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }  # comments

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "system",
                "content": """You are a CSS designer. Create a cohesive theme based on provided keywords. Focus on:
                - Color schemes
                - Typography choices
                - Spacing and layout
                - Mood-appropriate styling
                Output format: Valid CSS with variables and basic layout classes
                """
            },
            {
                "role": "user",
                "content": """Create a CSS theme based on these theme keywords: """ + theme_data + """
                 The theme should include:
                - CSS variables for colors
                - Basic typography settings
                - Container classes
                - Card/content styling
                - Appropriate spacing variables
                
                Here is an example, seperated by hashtags (#) of the current css so that you know what classes are used:
                
                #

                    :root {
                    --color-primary: #646cff;
                    --color-primary-hover: #535bf2;
                    --color-text-light: #f8fafc;
                    --color-text-dark: #1e293b;
                    --color-background-dark: #0f172a;
                    --color-background-light: #ffffff;
                    --color-surface-dark: #1e293b;
                    --color-surface-light: #f1f5f9;
                    --color-border: rgba(255, 255, 255, 0.1);
                    
                    --font-family-base: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    --font-family-heading: 'Inter', sans-serif;
                    --font-size-base: clamp(1rem, 1vw + 0.75rem, 1.125rem);
                    --line-height-base: 1.6;
                    
                    --spacing-xs: clamp(0.5rem, 1vw, 0.75rem);
                    --spacing-sm: clamp(0.75rem, 1.5vw, 1rem);
                    --spacing-md: clamp(1rem, 2vw, 1.5rem);
                    --spacing-lg: clamp(1.5rem, 3vw, 2rem);
                    --spacing-xl: clamp(2rem, 4vw, 3rem);
                    
                    --radius-sm: 0.375rem;
                    --radius-md: 0.5rem;
                    --radius-lg: 0.75rem;
                    }

                    /* Base styles */
                    body {
                    font-family: var(--font-family-base);
                    font-size: var(--font-size-base);
                    line-height: var(--line-height-base);
                    background-color: var(--color-background-dark);
                    color: var(--color-text-light);
                    -webkit-font-smoothing: antialiased;
                    -moz-osx-font-smoothing: grayscale;
                    min-height: 100vh;
                    }

                    .container {
                    width: 100%;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: var(--spacing-lg);
                    }

                    .content {
                    background-color: var(--color-surface-dark);
                    border-radius: var(--radius-lg);
                    padding: var(--spacing-lg);
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1),
                                0 2px 4px -1px rgba(0, 0, 0, 0.06);
                    }

                    h1 {
                    font-family: var(--font-family-heading);
                    font-size: clamp(2rem, 4vw + 1rem, 3rem);
                    font-weight: 700;
                    margin-bottom: var(--spacing-lg);
                    line-height: 1.2;
                    text-align: center;
                    }

                    #image-container {
                    margin-bottom: var(--spacing-lg);
                    border-radius: var(--radius-md);
                    overflow: hidden;
                    }

                    #newsified-image {
                    width: 100%;
                    height: auto;
                    display: block;
                    border-radius: var(--radius-md);
                    }

                    #article-container {
                    background-color: var(--color-surface-dark);
                    padding: var(--spacing-md);
                    border-radius: var(--radius-md);
                    border: 1px solid var(--color-border);
                    }

                    #newsified-article {
                    margin: 0;
                    font-size: var(--font-size-base);
                    line-height: var(--line-height-base);
                    }

                    /* Light mode support */
                    @media (prefers-color-scheme: light) {
                    body {
                        background-color: var(--color-background-light);
                        color: var(--color-text-dark);
                    }

                    .content {
                        background-color: var(--color-surface-light);
                    }

                    #article-container {
                        background-color: var(--color-surface-light);
                        border-color: rgba(0, 0, 0, 0.1);
                    }
                    }

                    /* Responsive adjustments */
                    @media (max-width: 768px) {
                    .container {
                        padding: var(--spacing-md);
                    }

                    .content {
                        padding: var(--spacing-md);
                    }

                    h1 {
                        font-size: clamp(1.5rem, 3vw + 1rem, 2rem);
                        margin-bottom: var(--spacing-md);
                    }
                    }

                    .go-back-button {
                    display: block;
                    width: 100%;
                    max-width: 200px;
                    margin: var(--spacing-md) auto;
                    padding: var(--spacing-sm);
                    font-size: var(--font-size-base);
                    color: var(--color-text-light);
                    background-color: var(--color-primary);
                    border: none;
                    border-radius: var(--radius-md);
                    cursor: pointer;
                    text-align: center;
                    transition: background-color 0.3s ease;
                    }

                    .go-back-button:hover {
                    background-color: var(--color-primary-hover);
                    }

                    /* Reduced motion preferences */
                    @media (prefers-reduced-motion: reduce) {
                    * {
                        animation-duration: 0.01ms !important;
                        animation-iteration-count: 1 !important;
                        transition-duration: 0.01ms !important;
                        scroll-behavior: auto !important;
                    }
                    }
                
                #

                Please export the new theme using these classes and ids, otherwise it will not work     
                Also, do not start the prompt with ```css or end with ``` as this breaks the css
                """
            }
        ]
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    css_content = response.json()['choices'][0]['message']['content']
    
    
    return css_content

def save_css_to_file(css_code):
    """Save generated CSS to the static newsified.css file"""
    css_path = "src/newsified.css"
    
    # Write the new CSS content to the file
    with open(css_path, "w") as css_file:
        css_file.write(css_code)

@app.route('/src/newsified.css')
def serve_css():
    print(os.path.join(os.getcwd(), 'src'), 'newsified.css')
    return send_from_directory(os.path.join(os.getcwd(), 'src'), 'newsified.css')

@app.route('/uploads/<filename>')
def serve_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# Flask route for uploading image and generating article
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    # Generate a unique filename to prevent overwrites
    import uuid
    filename = f"{uuid.uuid4()}.{file.filename.rsplit('.', 1)[1].lower()}"
    
    # Save the uploaded file
    image_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(image_path)
    
    # Get style choice from form
    style = request.form.get('style', 'formal')

    # Generate description and article
    description = generate_image_description(image_path)
    article = generate_article(description, style)
    theme_css = generate_theme_css(description)

    # Return the URL path instead of filesystem path
    image_url = f'http://127.0.0.1:5000/uploads/{filename}'

    save_css_to_file(theme_css)

    return jsonify({
        "article": article,
        "image_url": image_url,
        "theme_css": theme_css
    })



if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
