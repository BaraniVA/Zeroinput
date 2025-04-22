import numpy as np
import pandas as pd
import json
import os
import datetime
from collections import Counter
import re
import random
from sklearn.model_selection import train_test_split

# Go up one more directory level to reach the root project folder
MEMORY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "zeroinput_memory.json")

def load_memory_data():
    """Load memory data from JSON file"""
    try:
        with open(MEMORY_FILE, 'r') as f:
            data = json.load(f)
        print(f"Loaded {len(data)} memory entries")
        return data
    except FileNotFoundError:
        print(f"Memory file not found: {MEMORY_FILE}")
        return []
    except json.JSONDecodeError:
        print(f"Error decoding JSON from memory file")
        return []
    
def load_feedback_data():
    """Load feedback data for enhancing training"""
    feedback_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "zeroinput_feedback.json")
    
    if not os.path.exists(feedback_file):
        print("No feedback data found. Using unweighted training.")
        return None
    
    try:
        with open(feedback_file, 'r') as file:
            feedback_data = json.load(file)
            
        print(f"Loaded feedback data: {len(feedback_data['suggestions'])} suggestion records")
        
        # Create a more usable structure: mapping from app transitions to feedback outcomes
        app_transitions = {}
        
        for suggestion in feedback_data['suggestions']:
            # Skip records with missing data
            if not all(k in suggestion for k in ['suggested_app', 'current_app', 'followed']):
                continue
                
            # Create transition key: from_app -> to_app
            transition = (suggestion['current_app'].lower(), suggestion['suggested_app'].lower())
            
            # Initialize if not exists
            if transition not in app_transitions:
                app_transitions[transition] = {'followed': 0, 'ignored': 0}
            
            # Add outcome
            if suggestion['followed']:
                app_transitions[transition]['followed'] += 1
            else:
                app_transitions[transition]['ignored'] += 1
        
        return {
            'raw_data': feedback_data,
            'app_transitions': app_transitions
        }
    except Exception as e:
        print(f"Error loading feedback data: {e}")
        return None

def extract_app_name(window_title):
    """Extract app name from a window title"""

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
        
    words = window_title.split()
    return words[0] if words else window_title  # Fallback to first word if no match found

def extract_app_sequences(data, min_sequence_length=3):
    """Extract Extract sequences of application usage from memory data"""
    if not data:
        return []
    
    try: 
        sorted_data= sorted(data, key=lambda x: x.get('timestamp', ''))
    except:
        print("Error sorting data by timestamp")
        return []
    
    app_sequence = []
    for entry in sorted_data:
        if isinstance(entry, dict) and 'window' in entry:
            window_title = entry.get('window', '')
            app_name = extract_app_name(window_title)

            timestamp = entry.get('timestamp', '')

            if app_name and timestamp:
                app_sequence.append({'app': app_name, 'timestamp': timestamp})

    print(f"Extracted {len(app_sequence)} application entries")
    return app_sequence if len(app_sequence) >= min_sequence_length else []

def filter_training_data(sequences):
    """Filter out ZeroInput development files from training data"""
    filtered = []
    project_files = ["zeroinput", "main.py", "context_tracker.py", "suggestion_engine.py", 
                   "integration.py", "memory_store.py", "ml_predictor", "ml_model"]
    
    for entry in sequences:
        # Skip entries related to ZeroInput development
        if not any(proj_file in entry['app'].lower() for proj_file in project_files):
            filtered.append(entry)
    
    print(f"Filtered out {len(sequences) - len(filtered)} ZeroInput development entries")
    return filtered

def create_time_features(sequences):
    """Create time-based features from timestamps"""
    enhanced_sequences = []
    
    for entry in sequences:
        try:
            # Parse timestamp
            dt = datetime.datetime.strptime(entry['timestamp'], "%Y-%m-%d %H:%M:%S")
            
            # Create enhanced entry with time features
            enhanced_entry = entry.copy()
            enhanced_entry.update({
                'hour': dt.hour,
                'day_of_week': dt.weekday(),  # 0=Monday, 6=Sunday
                # Convert time to cyclical features to handle the circular nature of time
                'hour_sin': np.sin(2 * np.pi * dt.hour / 24),
                'hour_cos': np.cos(2 * np.pi * dt.hour / 24),
                'weekday_sin': np.sin(2 * np.pi * dt.weekday() / 7),
                'weekday_cos': np.cos(2 * np.pi * dt.weekday() / 7)
            })
            
            enhanced_sequences.append(enhanced_entry)
        except (ValueError, KeyError) as e:
            print(f"Error processing timestamp: {e}")
    
    print(f"Created time features for {len(enhanced_sequences)} entries")
    return enhanced_sequences

def encode_categorical_features(sequences):
    """Convert application names to numerical IDs"""
    # Create a mapping of app names to unique IDs
    unique_apps = sorted(set(entry['app'] for entry in sequences))
    app_to_id = {app: idx for idx, app in enumerate(unique_apps)}
    id_to_app = {idx: app for app, idx in app_to_id.items()}
    
    # Add the app_id to each sequence entry
    for entry in sequences:
        entry['app_id'] = app_to_id[entry['app']]
    
    print(f"Encoded {len(unique_apps)} unique applications")
    return sequences, app_to_id, id_to_app

def create_training_examples(app_sequences, app_to_id, sequence_length=5):
    """Create sequence-based training examples with feedback weighting"""
    X = []
    y = []
    sample_weights = []
    
    # Load feedback data for weighting
    feedback_data = load_feedback_data()
    
    print("Creating training examples with feedback integration...")
    
    for sequence in app_sequences:
        # Skip sequences shorter than sequence_length + 1
        if len(sequence) < sequence_length + 1:
            continue
            
        # Create examples from this sequence
        for i in range(len(sequence) - sequence_length):
            # Input: sequence of app IDs and time features
            input_sequence = sequence[i:i+sequence_length]
            
            # Output: next app ID
            next_app = sequence[i+sequence_length]
            next_app_id = app_to_id.get(next_app['app_name'], -1)
            
            # Skip if we don't know the ID of the next app
            if next_app_id == -1:
                continue
                
            # Calculate weight based on feedback
            if feedback_data:
                from_app = input_sequence[-1]['app_name']
                to_app = next_app['app_name']
                weight = calculate_sample_weight(from_app, to_app, feedback_data)
            else:
                weight = 1.0
                
            # Format input: for each timestep, extract features
            formatted_input = []
            for app_data in input_sequence:
                app_id = app_to_id.get(app_data['app_name'], 0)
                hour = app_data['hour']
                day_of_week = app_data['day_of_week']
                hour_sin = app_data['hour_sin']
                hour_cos = app_data['hour_cos']
                
                # Create feature vector [app_id, hour_sin, hour_cos, weekday_sin, weekday_cos]
                features = [app_id, hour_sin, hour_cos, app_data['weekday_sin'], app_data['weekday_cos']]
                formatted_input.append(features)
                
            X.append(formatted_input)
            y.append(next_app_id)
            sample_weights.append(weight)
    
    # Convert to numpy arrays
    X = np.array(X)
    y = np.array(y)
    sample_weights = np.array(sample_weights)
    
    print(f"Created {len(X)} training examples with feedback weighting")
    print(f"Weight range: min={sample_weights.min():.2f}, max={sample_weights.max():.2f}, "
          f"mean={sample_weights.mean():.2f}")
    
    return X, y, sample_weights

def prepare_data_for_training(X, y, sample_weights=None, test_size=0.2):
    """Prepare data for training with validation split and weights"""
    
    # Use sample_weights if provided, otherwise use equal weights
    if sample_weights is None:
        sample_weights = np.ones(len(X))
    
    # Split into training and validation sets
    X_train, X_val, y_train, y_val, weights_train, weights_val = train_test_split(
        X, y, sample_weights, test_size=test_size, random_state=42
    )
    
    print(f"Training examples: {len(X_train)}")
    print(f"Validation examples: {len(X_val)}")
    
    # Save the arrays for model training
    np.save(os.path.join(os.path.dirname(__file__), 'X_train.npy'), X_train)
    np.save(os.path.join(os.path.dirname(__file__), 'y_train.npy'), y_train)
    np.save(os.path.join(os.path.dirname(__file__), 'X_val.npy'), X_val)
    np.save(os.path.join(os.path.dirname(__file__), 'y_val.npy'), y_val)
    np.save(os.path.join(os.path.dirname(__file__), 'weights_train.npy'), weights_train)
    
    return X_train, X_val, y_train, y_val, weights_train

def calculate_sample_weight(from_app, to_app, feedback_data):
    """Calculate a weight for a training example based on feedback"""
    if not feedback_data or 'app_transitions' not in feedback_data:
        return 1.0  # Default weight if no feedback data
        
    transitions = feedback_data['app_transitions']
    
    # Normalize app names for comparison
    from_app = from_app.lower()
    to_app = to_app.lower()
    
    # Check exact transition
    transition = (from_app, to_app)
    if transition in transitions:
        stats = transitions[transition]
        total = stats['followed'] + stats['ignored']
        if total > 0:
            # Calculate success rate with a minimum weight of 0.5
            # This prevents completely ignoring transitions that might become useful
            success_rate = stats['followed'] / total
            return max(0.5, success_rate * 2.0)  # Scale 0-1 to 0.5-2.0 range
    
    # Check if the target app has good feedback in general
    app_success = {'followed': 0, 'ignored': 0}
    for (source, target), stats in transitions.items():
        if target == to_app:
            app_success['followed'] += stats['followed']
            app_success['ignored'] += stats['ignored']
    
    total = app_success['followed'] + app_success['ignored']
    if total > 0:
        success_rate = app_success['followed'] / total
        return max(0.7, success_rate * 1.5)  # Scale 0-1 to 0.7-1.5 range
        
    return 1.0  # Default weight

if __name__ == "__main__":
    print("Testing data preparation module...")
    
    # Load the memory data
    memory_data = load_memory_data()
    
    # Extract app sequences
    app_sequences = extract_app_sequences(memory_data)

    # Filter out ZeroInput development entries
    app_sequences = filter_training_data(app_sequences)
    
    # Create time features
    app_sequences = create_time_features(app_sequences)
    
    # Convert app names to IDs
    app_sequences, app_to_id, id_to_app = encode_categorical_features(app_sequences)
    
    # Create training examples with weights
    X, y, sample_weights = create_training_examples(app_sequences, app_to_id)
    
    # Prepare data for training
    X_train, X_val, y_train, y_val, weights_train = prepare_data_for_training(X, y, sample_weights)
    
    print("\nData preparation complete! Ready for model training.")
    print(f"Sample input shape: {X_train[0].shape}")
    print(f"Number of features per timestep: {X_train.shape[2]}")

