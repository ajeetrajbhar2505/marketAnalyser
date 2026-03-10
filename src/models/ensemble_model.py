import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os


class EnsembleModel:
    def __init__(self, config=None):  # config=None add kiya
      self.config = config or {}  # agar config nahi hai to empty dict
      self.clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
      self.is_trained = False
    def fit(self, X, y):
        """Train the model"""
        # Convert to numpy if needed
        if isinstance(X, pd.DataFrame):
            X = X.values
        if isinstance(y, pd.Series):
            y = y.values
        
        # Split data
        try:
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=False
            )
        except:
            # If not enough data for split
            X_train, y_train = X, y
            X_val, y_val = X, y
        
        # Train
        self.clf.fit(X_train, y_train)
        self.is_trained = True
        
        # Validate
        train_acc = accuracy_score(y_train, self.clf.predict(X_train))
        
        result = {
            "train_accuracy": float(train_acc),
            "n_samples": len(X)
        }
        
        try:
            val_acc = accuracy_score(y_val, self.clf.predict(X_val))
            result["val_accuracy"] = float(val_acc)
        except:
            result["val_accuracy"] = float(train_acc)
        
        return result
    
    def predict(self, X):
        """Make predictions"""
        if not self.is_trained:
            return np.zeros(len(X) if hasattr(X, '__len__') else 1)
        
        if isinstance(X, pd.DataFrame):
            X = X.values
        return self.clf.predict(X)
    
    def predict_proba(self, X):
        """Get prediction probabilities"""
        if not self.is_trained:
            n_samples = len(X) if hasattr(X, '__len__') else 1
            return np.array([[0.5, 0.5]] * n_samples)
        
        if isinstance(X, pd.DataFrame):
            X = X.values
        return self.clf.predict_proba(X)
    
    def save(self, path):
        """Save model to disk"""
        joblib.dump(self.clf, path)
    
    def load(self, path):
        """Load model from disk"""
        if os.path.exists(path):
            self.clf = joblib.load(path)
            self.is_trained = True
            return True
        return False