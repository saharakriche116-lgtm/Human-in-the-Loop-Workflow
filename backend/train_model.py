import sqlite3
import pandas as pd
import joblib
import json
import os
import mlflow
import mlflow.sklearn
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold, KFold
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

# To avoid GUI errors on the server
import matplotlib
matplotlib.use('Agg')

# Config
DB_PATH = "hitl.db"
MODEL_PATH = "model_hitl.pkl"

# MLflow Configuration
mlflow.set_tracking_uri("file:./mlruns")
mlflow.set_experiment("HITL_CV_Parser_Advanced")

def train():
    print("📊 LOADING DATA...")
    
    if not os.path.exists(DB_PATH):
        print("⚠️ No database found.")
        return {"status": "error"}

    conn = sqlite3.connect(DB_PATH)
    df_corrections = pd.read_sql("SELECT corrected_data, time_taken FROM corrections", conn)
    conn.close()

    if df_corrections.empty:
        return {"status": "no_data"}

    # --- DATA PREPARATION ---
    data_list = []
    times = []
    
    for index, row in df_corrections.iterrows():
        try:
            data = json.loads(row['corrected_data']) if isinstance(row['corrected_data'], str) else row['corrected_data']
            # Concatenate everything to provide context
            text_features = f"{data.get('skills', '')} {data.get('education', '')} {data.get('experience', '')}"
            role_label = data.get('predicted_role', 'Unknown')
            
            # Ignore unknowns for training
            if role_label and role_label != "Unknown":
                data_list.append({'text': text_features, 'role': role_label})
                if row['time_taken']:
                    times.append(row['time_taken'])
        except:
            continue
    
    df = pd.DataFrame(data_list)
    print(f"🔹 Number of valid examples: {len(df)}")

    # Minimum required to run algorithm without crashing
    if len(df) < 3:
        print("⚠️ Not enough data to train (Min: 3).")
        return {"status": "insufficient_data"}

    # --- MLFLOW TRACKING ---
    with mlflow.start_run():
        
        # 1. Business Metrics
        avg_time = sum(times) / len(times) if times else 0
        mlflow.log_metric("avg_human_time_sec", avg_time)
        mlflow.log_param("dataset_size", len(df))

        X = df['text']
        y = df['role']

        model = make_pipeline(CountVectorizer(), RandomForestClassifier(n_estimators=50, random_state=42))

        # --- SMART SMALL DATASET MANAGEMENT ---
        # Check if we have enough data per class for "Stratified"
        min_class_count = y.value_counts().min()
        
        # Default: Simple split (if rare data)
        stratify_param = None
        cv_strategy = KFold(n_splits=2) 
        
        # If we have at least 2 examples of each role, activate "Pro" mode
        if min_class_count >= 2:
            print("✅ Stratified Mode activated (Sufficient data)")
            stratify_param = y
            cv_strategy = StratifiedKFold(n_splits=min(3, min_class_count))
        else:
            print("⚠️ Simple Mode activated (Some classes have only 1 example)")

        # 2. CROSS-VALIDATION
        try:
            cv_scores = cross_val_score(model, X, y, cv=cv_strategy, scoring='accuracy')
            real_accuracy = cv_scores.mean()
        except Exception as e:
            print(f"⚠️ Cross-Val Error (Ignored): {e}")
            real_accuracy = 0.0
        
        print(f"🎯 Accuracy (Est.): {real_accuracy:.2f}")
        mlflow.log_metric("cv_accuracy_mean", real_accuracy)

        # 3. TRAIN/TEST SPLIT
        # If stratify=None, it splits randomly without worrying about proportions
        # This avoids the "The least populated class..." crash
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=stratify_param
        )
        
        model.fit(X_train, y_train)
        
        # If test set is empty (too little data), skip advanced metrics
        if len(y_test) > 0:
            predictions = model.predict(X_test)
            
            # Metrics
            precision = precision_score(y_test, predictions, average='weighted', zero_division=0)
            recall = recall_score(y_test, predictions, average='weighted', zero_division=0)
            f1 = f1_score(y_test, predictions, average='weighted', zero_division=0)

            print(f"📊 F1-Score: {f1:.2f} | Precision: {precision:.2f}")

            mlflow.log_metric("test_precision", precision)
            mlflow.log_metric("test_recall", recall)
            mlflow.log_metric("test_f1_score", f1)

            # Confusion Matrix
            try:
                labels = model.named_steps['clf'].classes_
                cm = confusion_matrix(y_test, predictions, labels=labels)
                plt.figure(figsize=(8, 6))
                sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
                plt.xlabel('Prediction')
                plt.ylabel('True Label')
                plt.title('Confusion Matrix')
                plt.tight_layout()
                cm_filename = "confusion_matrix.png"
                plt.savefig(cm_filename)
                mlflow.log_artifact(cm_filename)
                os.remove(cm_filename)
            except Exception as e:
                print(f"⚠️ Unable to generate matrix (too few classes tested): {e}")

        # Final save
        joblib.dump(model, MODEL_PATH)
        mlflow.sklearn.log_model(model, "model")
        
        return {
            "status": "success", 
            "cv_accuracy": real_accuracy
        }

if __name__ == "__main__":
    train()