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
        if text_column not in df.columns:
            raise ValueError(
                f"Input DataFrame is missing text column: {text_column!r}"
            )

        if (
            isinstance(checkpoint_every, bool)
            or not isinstance(checkpoint_every, int)
            or checkpoint_every <= 0
        ):
            raise ValueError("checkpoint_every must be a positive integer.")

        processed_records = []
        checkpoint_dir = "data/checkpoints"
        os.makedirs(checkpoint_dir, exist_ok=True)

        print(f"Starting batch processing for {len(df)} samples...")

        rows = tqdm(
            df.iterrows(),
            total=len(df),
            desc="Processing Tickets",
        )

        for processed_count, (_, row) in enumerate(rows, start=1):
            record = row.to_dict()

            try:
                # Validate input before calling the pipeline.
                ticket_text = row[text_column]

                if not isinstance(ticket_text, str):
                    raise ValueError(
                        f"{text_column!r} must contain a non-empty string."
                    )

                ticket_text = ticket_text.strip()

                if not ticket_text:
                    raise ValueError(
                        f"{text_column!r} must not be empty or whitespace."
                    )

                result = self.pipeline.process(ticket_text)

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
                record["predicted_category"] = None
                record["predicted_intent"] = None
                record["predicted_priority"] = None
                record["predicted_sentiment"] = None
                record["suggested_action"] = None
                record["processing_success"] = False
                record["processing_error"] = str(e)

            processed_records.append(record)
            time.sleep(self.delay)

            # Count processed rows independently of DataFrame index labels.
            if processed_count % checkpoint_every == 0:
                checkpoint_path = os.path.join(
                    checkpoint_dir,
                    f"checkpoint_step_{processed_count}.csv",
                )
                pd.DataFrame(processed_records).to_csv(
                    checkpoint_path,
                    index=False,
                )

        return pd.DataFrame(processed_records)
