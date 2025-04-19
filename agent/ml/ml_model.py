import numpy as np
import json
import os
import keras
from keras import layers
import matplotlib.pyplot as plt

# Directory setup - save where numpy files are
model_dir = os.path.dirname(__file__)

# Function to build model
def build_model(num_apps, sequence_length, feature_dim):
    """
    Build an LSTM model for app prediction
    
    Parameters:
    - num_apps: Number of unique applications
    - sequence_length: Length of input sequences
    - feature_dim: Number of features per timestep
    """
    # Create a sequential model
    model = keras.Sequential()
    
    # Add LSTM layer to process sequences
    # 64 units = size of internal state, return_sequences=True means return full sequence
    model.add(layers.LSTM(64, input_shape=(sequence_length, feature_dim), return_sequences=True))
    
    # Second LSTM layer for deeper pattern recognition
    model.add(layers.LSTM(32))
    
    # Dense layer for feature extraction from LSTM output
    model.add(layers.Dense(32, activation='relu'))
    
    # Dropout to prevent overfitting (randomly disables 20% of neurons during training)
    model.add(layers.Dropout(0.2))
    
    # Output layer with softmax activation (predicts probability for each app)
    model.add(layers.Dense(num_apps, activation='softmax'))
    
    # Compile model
    model.compile(
        optimizer='adam',  # Adaptive learning rate optimization
        loss='sparse_categorical_crossentropy',  # Loss function for classification
        metrics=['accuracy']  # Track accuracy during training
    )
    
    model.summary()  # Print model architecture
    return model
    # Model architecture will go here
    
# Function to train model
def train_model(model, X_train, y_train, X_val, y_val, batch_size=16, epochs=50):
    """Train the model with early stopping"""
    
    # Define callbacks for training
    callbacks = [
        # Early stopping: stop training when validation loss doesn't improve
        keras.callbacks.EarlyStopping(
            monitor='val_loss',  # Watch validation loss
            patience=5,          # Wait 5 epochs before stopping if no improvement
            restore_best_weights=True  # Keep the best weights, not the final ones
        ),
        
        # ModelCheckpoint: save model when validation accuracy improves
        keras.callbacks.ModelCheckpoint(
            filepath=os.path.join(model_dir, 'best_model.h5'),
            monitor='val_accuracy',
            save_best_only=True,  # Only save when there's improvement
            verbose=1
        )
    ]
    
    # Train the model
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        batch_size=batch_size,
        epochs=epochs,
        callbacks=callbacks,
        verbose=1  # Show progress bar
    )
    
    return history, model

# Function to evaluate model
def evaluate_model(model, X_val, y_val, id_to_app):
    """Evaluate model performance"""
    
    # Get overall evaluation metrics
    loss, accuracy = model.evaluate(X_val, y_val, verbose=0)
    print(f"\nModel evaluation on validation data:")
    print(f"Loss: {loss:.4f}")
    print(f"Accuracy: {accuracy:.4f}")
    
    # Get predictions for specific examples
    predictions = model.predict(X_val)
    
    # Convert predictions to app indices
    pred_indices = np.argmax(predictions, axis=1)
    
    # Count correct predictions
    correct = np.sum(pred_indices == y_val)
    print(f"Correct predictions: {correct}/{len(y_val)} ({correct/len(y_val)*100:.2f}%)")
    
    # Display some example predictions
    print("\nSample predictions:")
    for i in range(min(5, len(y_val))):
        actual_app = id_to_app[str(y_val[i])]
        pred_app = id_to_app[str(pred_indices[i])]
        confidence = predictions[i][pred_indices[i]] * 100
        
        result = "✓" if pred_indices[i] == y_val[i] else "✗"
        print(f"{result} Actual: {actual_app}")
        print(f"   Predicted: {pred_app} (confidence: {confidence:.2f}%)")
        print()
        
    return loss, accuracy
# Function to save model and encodings
def save_model_and_encodings(model, app_to_id, id_to_app):
    """Save the model and encodings"""
    
    # Create models directory if it doesn't exist
    os.makedirs(os.path.join(model_dir, 'models'), exist_ok=True)
    
    # Save the model in TF format
    model_path = os.path.join(model_dir, 'models', 'app_predictor_model.keras')
    model.save(model_path)
    print(f"Model saved to: {model_path}")
    
    # Save the encodings as JSON
    encodings = {
        'app_to_id': app_to_id,
        'id_to_app': id_to_app
    }
    
    encodings_path = os.path.join(model_dir, 'models', 'app_encodings.json')
    with open(encodings_path, 'w') as f:
        json.dump(encodings, f, indent=2)
    
    print(f"Encodings saved to: {encodings_path}")

# Main execution
# Main execution
if __name__ == "__main__":
    # Load training data
    try:
        print("Loading training data...")
        X_train = np.load(os.path.join(model_dir, 'X_train.npy'))
        y_train = np.load(os.path.join(model_dir, 'y_train.npy'))
        X_val = np.load(os.path.join(model_dir, 'X_val.npy'))
        y_val = np.load(os.path.join(model_dir, 'y_val.npy'))
        
        print(f"Loaded training data with {len(X_train)} examples")
        print(f"Loaded validation data with {len(X_val)} examples")
        
        # Load encodings
        with open(os.path.join(model_dir, 'app_encodings.json'), 'r') as f:
            encodings = json.load(f)
            app_to_id = encodings['app_to_id']
            id_to_app = encodings['id_to_app']
        
        print(f"Loaded encodings for {len(app_to_id)} unique applications")
        
        # Get dimensions for model
        num_apps = len(app_to_id)
        sequence_length = X_train.shape[1]
        feature_dim = X_train.shape[2]
        
        print(f"Building model with: {num_apps} apps, {sequence_length} steps, {feature_dim} features")
        
        # Build model
        model = build_model(num_apps, sequence_length, feature_dim)
        
        # Train model
        print("\nStarting model training...")
        history, model = train_model(model, X_train, y_train, X_val, y_val)
        
        # Plot training history
        plt.figure(figsize=(12, 4))
        plt.subplot(1, 2, 1)
        plt.plot(history.history['accuracy'])
        plt.plot(history.history['val_accuracy'])
        plt.title('Model Accuracy')
        plt.ylabel('Accuracy')
        plt.xlabel('Epoch')
        plt.legend(['Train', 'Validation'], loc='upper left')
        
        plt.subplot(1, 2, 2)
        plt.plot(history.history['loss'])
        plt.plot(history.history['val_loss'])
        plt.title('Model Loss')
        plt.ylabel('Loss')
        plt.xlabel('Epoch')
        plt.legend(['Train', 'Validation'], loc='upper left')
        
        plt.tight_layout()
        plt.savefig(os.path.join(model_dir, 'training_history.png'))
        print(f"Training history saved to {os.path.join(model_dir, 'training_history.png')}")
        
        # Evaluate model
        evaluate_model(model, X_val, y_val, id_to_app)
        
        # Save model and encodings
        save_model_and_encodings(model, app_to_id, id_to_app)
        
        print("\nModel training and evaluation complete!")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nPlease run ml_data_prep.py first to generate the training data files.")