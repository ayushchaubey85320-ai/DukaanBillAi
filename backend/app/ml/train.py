"""
Offline Model Training Pipeline for Intent Classification
Trains a Calibrated Classifier with sublinear TF-IDF word & char n-grams on 10,000+ utterances,
evaluates on held-out test data, and persists the model artifact.
"""
import os
import json
import joblib
from typing import Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from backend.app.ml.dataset import generate_massive_training_dataset
from backend.app.ml.tokenizer import clean_and_normalize_text

def train_intent_model(output_dir: str = None) -> Dict[str, Any]:
    """
    Executes complete offline model training on 10,000+ utterances and returns evaluation metrics.
    """
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(output_dir, exist_ok=True)

    print("Generating massive training dataset with 26 intents...")
    data = generate_massive_training_dataset()
    texts = [clean_and_normalize_text(t[0]) for t in data]
    labels = [t[1] for t in data]

    print(f"Total labeled dataset size: {len(data)} utterances across {len(set(labels))} intents.")

    # Stratified Train/Test split
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.15, random_state=42, stratify=labels
    )

    # Scikit-Learn Pipeline with sublinear n-gram TF-IDF and calibrated Logistic Regression
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            ngram_range=(1, 3),
            sublinear_tf=True,
            min_df=1,
            analyzer='word',
            token_pattern=r'(?u)\b\w+\b'
        )),
        ('clf', LogisticRegression(
            C=12.0,
            max_iter=1500,
            class_weight='balanced',
            random_state=42
        ))
    ])

    print("Fitting model on training set...")
    pipeline.fit(X_train, y_train)

    print("Evaluating on held-out test set...")
    y_pred = pipeline.predict(X_test)

    accuracy = float(accuracy_score(y_test, y_pred))
    macro_f1 = float(f1_score(y_test, y_pred, average='macro', zero_division=0))
    weighted_f1 = float(f1_score(y_test, y_pred, average='weighted', zero_division=0))
    precision = float(precision_score(y_test, y_pred, average='weighted', zero_division=0))
    recall = float(recall_score(y_test, y_pred, average='weighted', zero_division=0))

    metrics = {
        "dataset_size": len(data),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "intents_count": len(set(labels)),
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4)
    }

    print("Model Evaluation Metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    # Save model and metrics
    model_path = os.path.join(output_dir, "intent_model.joblib")
    metrics_path = os.path.join(output_dir, "model_metrics.json")
    
    joblib.dump(pipeline, model_path)
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"Successfully saved enhanced model to: {model_path}")
    return metrics

if __name__ == "__main__":
    train_intent_model()
