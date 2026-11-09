import os
import pandas as pd
from src.llm_engine import get_llm_engine
from src.pipeline import TicketPipeline
from src.batch_processor import BatchProcessor
from src.evaluation import TicketEvaluator

def main():
    # Load Bitext dataset
    # dataset_path = "data/Bitext_Sample_Customer_Support_Training_Dataset_27K_responses-v11.csv"
    dataset_path = "data/poc_sample_50.csv"
    
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Please place dataset at: {dataset_path}")

    full_df = pd.read_csv(dataset_path)
    
    # Select a representative sample for testing
    sample_size = 50
    test_df = full_df.sample(n=sample_size, random_state=42).reset_index(drop=True)
    print(f"Loaded {len(test_df)} samples for batch run.")

    # Initialize components
    engine = get_llm_engine()
    pipeline = TicketPipeline(llm_engine=engine, max_retries=2)
    processor = BatchProcessor(pipeline=pipeline, delay_between_calls=0.5)

    # Run batch processing
    results_df = processor.process_dataset(test_df, text_column="instruction")
    
    # Save complete run outputs
    output_path = "data/batch_evaluation_results.csv"
    results_df.to_csv(output_path, index=False)
    print(f"Batch inference complete. Results saved to: {output_path}")

    # Run evaluation against Ground Truth
    evaluator = TicketEvaluator(results_df)
    
    # Category evaluation
    if "category" in results_df.columns:
        evaluator.evaluate_task(true_col="category", pred_col="predicted_category", task_name="Category Classification")

    # Intent evaluation (if supported by schema)
    if "intent" in results_df.columns and "predicted_intent" in results_df.columns:
        evaluator.evaluate_task(true_col="intent", pred_col="predicted_intent", task_name="Intent Detection")

if __name__ == "__main__":
    main()
