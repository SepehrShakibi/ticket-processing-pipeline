import logging
from src.llm_engine import get_llm_engine
from src.pipeline import TicketPipeline

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    engine = get_llm_engine()
    pipeline = TicketPipeline(engine)

    sample_ticket = (
        "Hi, I tried to upgrade my subscription yesterday but the payment "
        "failed three times and I was still charged $49! Please refund me."
    )

    try:
        result = pipeline.process(sample_ticket)
        print("\n--- Processed Output ---")
        print(result.model_dump_json(indent=2))

    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
