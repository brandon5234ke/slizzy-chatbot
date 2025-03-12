from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
"from waitress import serve"
import spacy
import json
import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Access the OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("OpenAI API key is not set in the .env file!")


# Load spaCy model with pre-trained word vectors
nlp = spacy.load("en_core_web_lg")

# Load FAQ data from JSON file
try:
    with open("faq_data.json") as f:
        faq_data = json.load(f)
except FileNotFoundError:
    raise RuntimeError("FAQ data file not found. Ensure 'faq_data.json' exists in the working directory.")

# Flask app setup
app = Flask(__name__)
CORS(app, resources={r"/chat": {"origins": "*"}})  # Allow cross-origin requests for '/chat'


def clean_input(text):
    """
    Clean and normalize user input to improve matching.
    """
    return ' '.join(token.text.lower() for token in nlp(text) if not token.is_stop and not token.is_punct)


def find_best_match(user_input):
    """
    Match user input to the closest FAQ using spaCy's similarity scoring.
    If no match exceeds the threshold, use OpenAI API as fallback.
    """
    if not user_input.strip():
        return "Please provide a valid input."
    
    # Clean and normalize user input
    cleaned_input = clean_input(user_input)
    input_doc = nlp(cleaned_input)
    best_match = None
    best_similarity = 0.0

    for faq in faq_data:
        question_doc = nlp(clean_input(faq["question"]))

        # Calculate similarity
        similarity = input_doc.similarity(question_doc)
        
        # Log for debugging purposes
        """print(f"Input: {cleaned_input} | FAQ: {faq['question']} | Similarity: {similarity}")"""

        if similarity > best_similarity:
            best_similarity = similarity
            best_match = faq

    # Define a threshold for acceptable matches
    threshold = 0.85  # Increased for higher precision
    if best_match and best_similarity > threshold:
        return best_match["answer"]
    elif best_match:
        # Handle ambiguous matches below the threshold
        return f"I found a possible match: '{best_match['question']}'. Can you confirm or clarify your question?"
    else:
        # Use OpenAI fallback for unrecognized queries
        return get_openai_response(user_input)


def get_openai_response(user_input):
    """
    Query OpenAI API to generate a fallback response for user input.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful customer support assistant for an e-commerce platform. Respond clearly and concisely based on the user's question."},
                {"role": "user", "content": user_input}
            ],
            max_tokens=450,
            temperature=0.2,  # Low temperature for precise responses
            request_timeout=10.0,
        )
        return response["choices"][0]["message"]["content"].strip()
    except openai.error.OpenAIError as e:
        return f"OpenAI API error: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


@app.route("/")
def home():
    """
    Render the chatbot's home page.
    """
    return render_template("index.html")


@app.route('/chat', methods=['POST'])
def chat():
    """
    Process incoming chat messages and respond with the best match or fallback.
    """
    try:
        # Retrieve the user message from the POST request
        user_input = request.json.get("message", "")
        if user_input.strip():
            response_text = find_best_match(user_input)
            return jsonify({"response": response_text})
        else:
            return jsonify({"response": "Please provide a valid input."}), 400
    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error during processing: {e}")
        return jsonify({"response": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)  # Runs the Flask app using Waitress
