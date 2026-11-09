import pandas as pd
from sklearn.metrics import classification_report, accuracy_score

class TicketEvaluator:
    def __init__(self, results_df: pd.DataFrame):
        self.df = results_df.copy()

    def evaluate_task(self, true_col: str, pred_col: str, task_name: str = "Classification"):
        print(f"\n{'='*20} Evaluation: {task_name} {'='*20}")

        # Check column existence
        if true_col not in self.df.columns or pred_col not in self.df.columns:
            print(f"[WARN] Skipping {task_name}: Column '{true_col}' or '{pred_col}' does not exist.")
            return None
        # Filter out NaN, None, or string representation of nulls
        mask = (
            self.df[true_col].notna() & 
            self.df[pred_col].notna() & 
            (~self.df[pred_col].astype(str).str.lower().isin(['none', 'nan', '', 'null']))
        )
        valid_df = self.df[mask].copy()

        if len(valid_df) == 0:
            print(f"[INFO] Skipping {task_name}: No valid pairs found to evaluate.")
            return None

        # Normalize strings: lowercase and strip spaces
        y_true = valid_df[true_col].astype(str).str.strip().str.lower()
        y_pred = valid_df[pred_col].astype(str).str.strip().str.lower()

        acc = accuracy_score(y_true, y_pred)
        print(f"Evaluated Samples: {len(valid_df)} / {len(self.df)}")
        print(f"Accuracy: {acc * 100:.2f}%\n")

        print("Detailed Metrics Report:")
        print(classification_report(y_true, y_pred, zero_division=0))

        return {"task": task_name, "accuracy": acc, "samples": len(valid_df)}
