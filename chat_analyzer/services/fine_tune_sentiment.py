import pandas as pd
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer
)
import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from pathlib import Path
import torch
import logging
from datetime import datetime

def fine_tune_sentiment_model():
    """
    ok now we gotta fine-tune the sentiment model on our custom data.
    for mac we gotta use MPS (apple silicon) acceleration if available
    """
    print("\n" + "=" * 80)
    print("FINE-TUNING THE SENTIMENT MODEL")
    print("\n" + "=" * 80)
    
    # check if MPS available and support
    if torch.backends.mps.is_available():
        device = torch.device('mps')
        print(" ✅ MPS silicon acceleration enabled - Training will be faster ")
    elif torch.cuda.is_available():
        device = torch.device('cuda')
        print(" ✅ Using CUDA")
    else:
        device = torch.device('cpu')
        print(" No GPU detected, using CPU and this will make training slow")

    # load our labeled data
    data_path = Path(__file__).parent.parent / 'data' / 'labeled_data' / 'labeledsentimentdatatwo_balanced.csv'

    if not data_path.exists():
        print("❌ Data file not found: {data_path}")
        print(" expeced path chat_analyzer/data/labeled_data/labeledsentimentdatatwo_balanced.csv")
        return

    print (f"📊 Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"    Total examples: {len(df)}")

    # check label distribution 
    print("checking label distribution")
    label_counts = df['label'].value_counts().sort_index()
    for label, count in label_counts.items():
        label_name = {0: 'Negative', 1: 'Neutral', 2: 'Positive'}.get(label, 'Unknown')
        print(f" {label} ({label_name}): {count}")

    # check balance
    min_count = label_counts.min()
    max_count = label_counts.max()
    if max_count - min_count > 100:
        print(f"\n Dataset is imbalanced! Min: {min_count}, Max: {max_count}")
        print(f"consider adding more examples to the underpresented class.")

    # 2. Clean text (remove empty or null)
    df = df.dropna(subset=['text'])
    df = df[df['text'].str.strip() != '']
    print(f"\n After cleaning: {len(df)} examples")

    # 3. Convert to Hugging Face Dataset
    dataset = Dataset.from_pandas(df)
    dataset = dataset.train_test_split(test_size=0.2, seed=42)

    # 4. we need to setup the tokenizer and model
    model_name = "xlm-roberta-base"
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            padding="max_length",
            truncation=True,
            max_length=128
        )

    print("\n Tokenizing data... ")
    tokenized_datasets = dataset.map(tokenize_function, batched=True)

    # 5. Load model 
    print(f" loading the base model: {model_name}")
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=3
    )

    # moce model to MPS if available
    if torch.backends.mps.is_available():
        model = model.to('mps')
        print(f"   Model moved to MPS")

    # 6. Define metrics
    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)
        return {
            "accuracy": accuracy_score(labels, predictions),
            "f1_macro": f1_score(labels, predictions, average="macro"),
            "f1_weighted": f1_score(labels, predictions, average="weighted")
        }

    # 7. here is Training TrainingArguments
    training_args = TrainingArguments(
        output_dir="./xlm_roberta_malay_finetuned_17_Aug",
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=3,
        weight_decay=0.01,
        logging_dir="./logs",
        logging_steps=50,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        report_to="none",
        
        
        # save progress every epoch
      
    )

    # creating the trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["test"],
        compute_metrics=compute_metrics,
       
    )

    trainer.train()

    # 9. evaluating the model
    print(" evaluating the model...  ")
    eval_results = trainer.evaluate()
    print(f"   🔑 Accuracy: {eval_results['eval_accuracy']:.4f}")
    print(f"   🧲 F1 Macro: {eval_results.get('eval_f1_macro', 'N/A')}")

    # 10. Save the fine-tuned model
    model_path = Path(__file__).parent.parent / 'ml_models' / 'xlm_roberta_malay'
    model_path.mkdir(parents=True, exist_ok=True)

    trainer.save_model(str(model_path))
    tokenizer.save_pretrained(str(model_path))

    print(f"\n✅ Model saved to: {model_path}")
    print(f"✅ Training complete! wuhuuuuuuuu ")
    print(f" Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 11. test the model with sample messages
    print("\n Testing the model with sample messages... ")
    test_messages = [
        "saya sangat kecewa dan sedih hari ini",
        "alhamdulillah, anak saya semakin baik",
        "saya ada janji temu esok pukul 3",
    ]

    from chat_analyzer.services.sentiment_analyzer import analyze_sentiment

    for msg in test_messages:
        result = analyze_sentiment(msg)
        emoji = {0: '❌', 1: '😑', 2: '✅'}
        print(f"\n📑 {msg}")
        print(f"    Label: {result['label']}{emoji}")
        print(f"    Score: {result['score']:.2f}")
        print(f"    Confidence: {result['confidence']:.2f}")

    return model_path

# ====================================================
# FOR TESTING SECTION 
# ====================================================
if __name__ == "__main__":
    fine_tune_sentiment_model()







