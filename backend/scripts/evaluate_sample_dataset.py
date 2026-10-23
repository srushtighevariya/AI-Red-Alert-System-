import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.ai.pipeline import analyze_document_text


DATASET_PATH = PROJECT_ROOT / "app" / "data" / "sample_dataset.csv"


def evaluate_dataset() -> None:
    total = 0
    correct = 0

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        print("Sample Dataset Evaluation")
        print("-" * 30)

        for row in reader:
            total += 1

            text = row["text"]
            expected_alert = row["expected_alert"]

            analysis = analyze_document_text(text)
            predicted_alert = analysis["risk_analysis"]["alert_level"]
            risk_score = analysis["risk_analysis"]["risk_score"]

            is_correct = predicted_alert == expected_alert

            if is_correct:
                correct += 1

            print(
                f"Document {row['document_id']}: "
                f"expected={expected_alert}, "
                f"predicted={predicted_alert}, "
                f"score={risk_score}, "
                f"correct={is_correct}"
            )

    accuracy = (correct / total) * 100 if total else 0

    print("-" * 30)
    print(f"Total documents: {total}")
    print(f"Correct predictions: {correct}")
    print(f"Accuracy: {accuracy:.2f}%")


if __name__ == "__main__":
    evaluate_dataset()