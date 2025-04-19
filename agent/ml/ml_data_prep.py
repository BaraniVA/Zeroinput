import numpy as np
import pandas as pd
import json
import os
import datetime
from collections import Counter
import re
import random

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

def create_training_examples(sequences, sequence_length=5):
    """Create input/output pairs for training
    
    For each sequence of length sequence_length, predict the next app
    """
    X = []  # Input sequences
    y = []  # Output (next app)
    
    # We need at least sequence_length + 1 entries
    if len(sequences) <= sequence_length:
        print("Not enough data to create sequences")
        return [], []
    
    # Create sliding windows of sequence_length
    for i in range(len(sequences) - sequence_length):
        # Input: sequence of app_ids and time features
        sequence_input = []
        
        for j in range(i, i + sequence_length):
            # Extract relevant features for this entry
            entry = sequences[j]
            features = [
                entry['app_id'],
                entry['hour_sin'], 
                entry['hour_cos'],
                entry['weekday_sin'], 
                entry['weekday_cos']
            ]
            sequence_input.append(features)
            
        # Output: next app's ID
        next_app_id = sequences[i + sequence_length]['app_id']
        
        X.append(sequence_input)
        y.append(next_app_id)
    
    print(f"Created {len(X)} training examples")

    # Count occurrences of each output app
    from collections import Counter
    output_counts = Counter(y)
    max_samples_per_app = 20  # Limit samples per output app

    # Create balanced datasets
    X_balanced = []
    y_balanced = []

    # Track indices for each output app
    indices_by_app = {}
    for app_id in output_counts:
        indices_by_app[app_id] = []

    # Group indices by output app
    for i, app_id in enumerate(y):
        indices_by_app[app_id].append(i)

    # Sample evenly from each app (up to max_samples_per_app)
    for app_id, indices in indices_by_app.items():
        # Take up to max_samples_per_app random samples
        sample_indices = random.sample(indices, min(max_samples_per_app, len(indices)))
        
        for idx in sample_indices:
            X_balanced.append(X[idx])
            y_balanced.append(y[idx])

    # Use balanced data instead
    X = X_balanced
    y = y_balanced

    return X, y

def prepare_data_for_training(X, y):
    """Convert to numpy arrays and split into train/validation sets"""
    import numpy as np
    from sklearn.model_selection import train_test_split
    
    # Convert to numpy arrays
    X = np.array(X)
    y = np.array(y)
    
    # Print shapes
    print(f"Input shape: {X.shape}")
    print(f"Output shape: {y.shape}")
    
    # Split into train/validation sets (80/20)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"Training examples: {len(X_train)}")
    print(f"Validation examples: {len(X_val)}")
    
    return X_train, X_val, y_train, y_val


if __name__ == "__main__":
    # Test data loading and processing
    print("Testing data preparation module...")
    
    # Load the memory data
    memory_data = load_memory_data()
    
    # Extract app sequences
    app_sequences = extract_app_sequences(memory_data)

     # Filter out ZeroInput development entries
    app_sequences = filter_training_data(app_sequences)
    
    # Create time features
    enhanced_sequences = create_time_features(app_sequences)
    
    # Print some statistics
    if enhanced_sequences:
        # Count unique applications
        apps = [entry['app'] for entry in enhanced_sequences]
        app_counts = Counter(apps)
        
        print("\nTop 10 most frequent applications:")
        for app, count in app_counts.most_common(10):
            print(f"  {app}: {count} occurrences")
        
        print(f"\nTotal unique applications: {len(app_counts)}")
        
        # Show a sample of the enhanced data
        print("\nSample of enhanced data:")
        sample = enhanced_sequences[0]
        for key, value in sample.items():
            print(f"  {key}: {value}")
        
        # Encode categorical features
        encoded_sequences, app_to_id, id_to_app = encode_categorical_features(enhanced_sequences)
        
        # Create training examples
        X, y = create_training_examples(encoded_sequences)
        
        # If we have enough examples, prepare for training
        if X and y:
            # Prepare data for training
            X_train, X_val, y_train, y_val = prepare_data_for_training(X, y)
            
            # Save the encodings for later use
            encodings = {
                'app_to_id': app_to_id,
                'id_to_app': id_to_app
            }
            
            # Define the current directory
            current_dir = os.path.dirname(__file__)
            
            # Save numpy arrays with full paths
            np.save(os.path.join(current_dir, 'X_train.npy'), X_train)
            np.save(os.path.join(current_dir, 'y_train.npy'), y_train)
            np.save(os.path.join(current_dir, 'X_val.npy'), X_val)
            np.save(os.path.join(current_dir, 'y_val.npy'), y_val)
            
            # Save encodings
            encodings_path = os.path.join(current_dir, 'app_encodings.json')
            with open(encodings_path, 'w') as f:
                json.dump(encodings, f, indent=2)
            
            print("\nData files saved to:")
            print(f"- {os.path.join(current_dir, 'X_train.npy')}")
            print(f"- {os.path.join(current_dir, 'app_encodings.json')}")
            
            print("\nData preparation complete! Ready for model training.")
            print(f"Sample input shape: {X_train[0].shape}")
            print(f"Number of features per timestep: {X_train[0].shape[1]}")
    else:
        print("No sequences found or insufficient data")

