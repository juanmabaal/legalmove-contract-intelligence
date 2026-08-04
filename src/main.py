import argparse
import json
from pathlib import Path

from src.config.settings import OUTPUT_DIR, VISION_PROVIDER
from src.graph.graph_builder import run_image_parsing_graph


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "LegalMove Contract Intelligence - "
            "Image parsing pipeline for original contracts and amendments."
        )
    )

    parser.add_argument(
        "--original",
        required=True,
        help="Path to the original contract image.",
    )

    parser.add_argument(
        "--amendment",
        required=True,
        help="Path to the amendment image.",
    )

    parser.add_argument(
        "--case-id",
        required=True,
        help="Identifier for the analysis case.",
    )

    parser.add_argument(
        "--vision-provider",
        default=VISION_PROVIDER,
        help="Vision provider to use. Supported values: openai, xai.",
    )

    parser.add_argument(
        "--save-output",
        action="store_true",
        help="Save the parsed output JSON under outputs/examples.",
    )

    return parser


def save_output(case_id: str, output: dict) -> Path:
    output_dir = OUTPUT_DIR / "examples"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{case_id}_image_parsing_output.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(output, file, indent=2, ensure_ascii=False)

    return output_path


def main() -> None:
    parser = build_argument_parser()
    args = parser.parse_args()

    output = run_image_parsing_graph(
        case_id=args.case_id,
        original_image_path=args.original,
        amendment_image_path=args.amendment,
        vision_provider=args.vision_provider,
    )

    print("=" * 100)
    print("LegalMove Contract Intelligence - Image Parsing Output")
    print("=" * 100)
    print(json.dumps(output, indent=2, ensure_ascii=False))

    if args.save_output:
        output_path = save_output(
            case_id=args.case_id,
            output=output,
        )

        print("-" * 100)
        print(f"Output saved to: {output_path}")


if __name__ == "__main__":
    main()