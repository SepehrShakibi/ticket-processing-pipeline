import os
import time
import pandas as pd
from tqdm import tqdm
from src.pipeline import TicketPipeline


class BatchProcessor:
    def __init__(self, pipeline: TicketPipeline, delay_between_calls: float = 0.5):
        """
        Initializes the batch processor.
        delay_between_calls: seconds to wait to respect API rate limits.
        """
        self.pipeline = pipeline
        self.delay = delay_between_calls

    @staticmethod
    def _extract_field(obj, *field_names, default=None):
        """
        Safely retrieves attribute values, handling Enums and alternative naming.
        """
        for name in field_names:
            if hasattr(obj, name):
                val = getattr(obj, name)
                # Unpack Enum if needed
                return val.value if hasattr(val, "value") else val
        return default

    def process_dataset(
        self,
        df: pd.DataFrame,
        text_column: str = "instruction",
        checkpoint_every: int = 50,
    ) -> pd.DataFrame:
        processed_records = []
        checkpoint_dir = "data/checkpoints"
        os.makedirs(checkpoint_dir, exist_ok=True)

        print(f"Starting batch processing for {len(df)} samples...")

        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing Tickets"):
            ticket_text = str(row[text_column])
            record = row.to_dict()

            try:
                # Execute pipeline built in Phase 3
                result = self.pipeline.process(ticket_text)

                # Safely extract predictions, supporting both ProcessedTicket fields and legacy naming
                record["predicted_category"] = self._extract_field(
                    result, "category", "predicted_category"
                )
                record["predicted_intent"] = self._extract_field(
                    result, "intent", "predicted_intent"
                )
                record["predicted_priority"] = self._extract_field(
                    result, "priority", "predicted_priority"
                )
                record["predicted_sentiment"] = self._extract_field(
                    result, "sentiment", "predicted_sentiment"
                )
                record["suggested_action"] = self._extract_field(
                    result, "suggested_action", "action", "summary"
                )
                record["processing_success"] = True
                record["processing_error"] = None

            except Exception as e:
                # Catch unexpected failures without interrupting the entire batch
                record["predicted_category"] = None
                record["predicted_intent"] = None
                record["predicted_priority"] = None
                record["predicted_sentiment"] = None
                record["suggested_action"] = None
                record["processing_success"] = False
                record["processing_error"] = str(e)

            processed_records.append(record)
            time.sleep(self.delay)

            # Checkpointing to disk
            if (idx + 1) % checkpoint_every == 0:
                temp_df = pd.DataFrame(processed_records)
                temp_df.to_csv(
                    f"{checkpoint_dir}/checkpoint_step_{idx + 1}.csv",
                    index=False,
                )

        final_df = pd.DataFrame(processed_records)
        return final_df
