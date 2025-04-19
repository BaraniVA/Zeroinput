import os
import json
import numpy as np
import datetime
import tensorflow as tf
import re
import random

# Get directory paths
load_model = tf.keras.models.load_model
model_dir = os.path.dirname(__file__)
model_path = os.path.join(model_dir, 'models', 'app_predictor_model.keras')
encodings_path = os.path.join(model_dir, 'models', 'app_encodings.json')

# Global variables to store loaded model and encodings
_model = None
_app_to_id = None
_id_to_app = None
_sequence_length = 5  # Must match the sequence length used during training

def extract_app_name(window_title):
    """Extract the application name from a window title"""
    # Common patterns in window titles
    patterns = [
        r"(.+?) - .+",  # Pattern: "Document - Application"
        r".+ - (.+)",   # Pattern: "Application - Document" 
        r"(.+?)\s*[\[\(].*?[\]\)]",  # Pattern: "Application [status]" or "Application (status)"
        r"(.+?):\s",    # Pattern: "Application: Document"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, window_title)
        if match:
            return match.group(1).strip()
    
    # If no pattern matches, return the first word or the whole title if short
    words = window_title.split()
    return words[0] if words else window_title

def load_predictor():
    """Load the model and encodings if not already loaded"""
    global _model, _app_to_id, _id_to_app
    
    try:
        if _model is None:
            print("Loading app predictor model...")
            _model = load_model(model_path)
            print("Model loaded successfully")
            
        if _app_to_id is None or _id_to_app is None:
            print("Loading app encodings...")
            with open(encodings_path, 'r') as f:
                encodings = json.load(f)
                _app_to_id = encodings['app_to_id']
                _id_to_app = encodings['id_to_app']
            print(f"Loaded encodings for {len(_app_to_id)} applications")
            
        return True
    except Exception as e:
        print(f"Error loading predictor: {e}")
        return False

def prepare_sequence_for_prediction(recent_windows):
    """
    Prepare the recent window titles for prediction
    
    Parameters:
    - recent_windows: List of recent window titles in chronological order
    
    Returns:
    - Feature array ready for model prediction, or None if preparation fails
    """
    global _app_to_id, _sequence_length
    
    try:
        if _app_to_id is None:
            if not load_predictor():
                return None
        
        # Extract app names from window titles
        app_sequence = []
        for window in recent_windows:
            app_name = extract_app_name(window)
            app_sequence.append(app_name)
        
        # We need at least sequence_length recent apps
        if len(app_sequence) < _sequence_length:
            # Pad with the earliest app if we don't have enough history
            padding = [app_sequence[0]] * (_sequence_length - len(app_sequence))
            app_sequence = padding + app_sequence
        
        # Take the most recent sequence_length apps
        app_sequence = app_sequence[-_sequence_length:]
        
        # Create time features for current time
        now = datetime.datetime.now()
        hour_sin = np.sin(2 * np.pi * now.hour / 24)
        hour_cos = np.cos(2 * np.pi * now.hour / 24)
        weekday_sin = np.sin(2 * np.pi * now.weekday() / 7)
        weekday_cos = np.cos(2 * np.pi * now.weekday() / 7)
        
        # Prepare the sequence with features
        sequence = []
        for app in app_sequence:
            # Get app_id or use -1 for unknown apps
            app_id = _app_to_id.get(app, -1)
            if app_id == -1:
                # If app is unknown, try to find the closest match
                for known_app in _app_to_id:
                    if app.lower() in known_app.lower() or known_app.lower() in app.lower():
                        app_id = _app_to_id[known_app]
                        break
            
            # If still unknown, use a default
            if app_id == -1:
                # Use the first app as default
                app_id = 0
            
            # Create feature vector [app_id, hour_sin, hour_cos, weekday_sin, weekday_cos]
            features = [app_id, hour_sin, hour_cos, weekday_sin, weekday_cos]
            sequence.append(features)
        
        # Convert to numpy array and reshape for the model
        sequence_array = np.array([sequence])
        
        return sequence_array
    
    except Exception as e:
        print(f"Error preparing sequence for prediction: {e}")
        return None

def predict_next_app(recent_windows):
    """
    Predict the next application based on recent window titles
    
    Parameters:
    - recent_windows: List of recent window titles in chronological order
    
    Returns:
    - Dictionary with prediction details or None if prediction fails
    """
    global _model, _id_to_app
    
    try:
        if _model is None or _id_to_app is None:
            if not load_predictor():
                return None
        
        # Prepare the sequence
        sequence_array = prepare_sequence_for_prediction(recent_windows)
        if sequence_array is None:
            return None
        
        # Make prediction
        prediction = _model.predict(sequence_array, verbose=0)[0]
        
        # Get top 3 predictions
        top_indices = np.argsort(prediction)[-3:][::-1]
        top_apps = []
        
        for idx in top_indices:
            app_id = str(idx)
            if app_id in _id_to_app:
                confidence = prediction[idx] * 100
                if confidence > 10:  # Only include predictions with >10% confidence
                    top_apps.append({
                        'app_name': _id_to_app[app_id],
                        'confidence': confidence
                    })
        
        if not top_apps:
            return None
            
        return {
            'top_prediction': top_apps[0],
            'all_predictions': top_apps
        }
    
    except Exception as e:
        print(f"Error making prediction: {e}")
        return None
_last_suggestions = []
def generate_suggestion_from_prediction(prediction, current_window):
    global _last_suggestions
    """
    Generate a suggestion based on the model's prediction
    
    Parameters:
    - prediction: The prediction dictionary from predict_next_app
    - current_window: The current window title
    
    Returns:
    - A suggestion string or None if no good suggestion can be made
    """
    if not prediction or 'top_prediction' not in prediction:
        return None
    
    top_app = prediction['top_prediction']['app_name']
    confidence = prediction['top_prediction']['confidence']
    current_app = extract_app_name(current_window)
    
    # Don't suggest the current app
    if top_app in _last_suggestions[-3:]:  # If same app suggested in last 3 cycles
        # Try the second prediction if available
        if len(prediction['all_predictions']) > 1:
            top_app = prediction['all_predictions'][1]['app_name']
            confidence = prediction['all_predictions'][1]['confidence']
        else:
            return None
    _last_suggestions.append(top_app)
    if len(_last_suggestions) > 10:
        _last_suggestions.pop(0) 
    
    # Only make suggestions with reasonable confidence
    if confidence < 20:
        return None
    
    # Generate different suggestion templates based on confidence
    if confidence > 70:
        suggestions = [
            f"You almost always use {top_app} after {current_app}. Would you like to switch to it now?",
            f"Based on your patterns, I'm very confident you'll want to use {top_app} next. Ready to switch?",
            f"Your workflow typically continues with {top_app} (with {confidence:.1f}% confidence). Open it now?"
        ]
    elif confidence > 50:
        suggestions = [
            f"You often use {top_app} after {current_app}. Would you like to open it?",
            f"Based on your patterns, you might want to use {top_app} next. Need it open?",
            f"I notice you frequently switch to {top_app} from here. Would that be helpful now?"
        ]
    else:
        suggestions = [
            f"You sometimes use {top_app} in this context. Would you like to open it?",
            f"Would you like to open {top_app}? You've used it in similar situations before.",
            f"Based on your past activity, {top_app} might be useful now. Want to switch to it?"
        ]
    
    if random.random() < 0.2:  # 20% of the time
        if len(prediction['all_predictions']) > 1:
            # Switch to second-best prediction occasionally
            top_app = prediction['all_predictions'][1]['app_name']
            confidence = prediction['all_predictions'][1]['confidence']
    
    return random.choice(suggestions)

# For testing
if __name__ == "__main__":
    # Test the predictor
    load_predictor()
    
    # Example recent windows
    test_windows = [
        "context_tracker.py - Visual Studio Code",
        "zeroinput_memory.json - Visual Studio Code",
        "main.py - Visual Studio Code",
        "GitHub - Browser",
        "Gmail - Browser"
    ]
    
    prediction = predict_next_app(test_windows)
    if prediction:
        print("\nPrediction results:")
        print(f"Top prediction: {prediction['top_prediction']['app_name']} "
              f"(Confidence: {prediction['top_prediction']['confidence']:.2f}%)")
        
        print("\nAll predictions:")
        for pred in prediction['all_predictions']:
            print(f"- {pred['app_name']}: {pred['confidence']:.2f}%")
        
        suggestion = generate_suggestion_from_prediction(prediction, test_windows[-1])
        print(f"\nSuggestion: {suggestion}")
    else:
        print("Could not make a prediction")