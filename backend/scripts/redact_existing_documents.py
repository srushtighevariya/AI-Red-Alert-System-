"""Mask personal data in documents saved before masking was added.

Older analyses stored the raw text preview, summary and keyword excerpts.
This re-runs the personal-data detectors on those stored strings and masks
what they find, and removes the old `saved_path` field.

    python scripts/redact_existing_documents.py           # preview only, changes nothing
    python scripts/redact_existing_documents.py --apply   # write the masked values
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from pymongo import AsyncMongoClient  # noqa: E402

from app.ai.indian_compliance_detector import detect_indian_compliance_data  # noqa: E402
from app.ai.redaction import redact_text  # noqa: E402
from app.ai.sensitive_info_detector import detect_sensitive_information  # noqa: E402
from app.core.config import settings  # noqa: E402


def mask_personal_data(text: str) -> str:
    if not text:
        return text

    sensitive = detect_sensitive_information(text)["findings"]
    compliance = detect_indian_compliance_data(
        text,
        exclude_spans=[(finding["start_index"], finding["end_index"]) for finding in sensitive],
    )["findings"]

    return redact_text(text, sensitive + compliance)


def build_update(document: dict) -> dict:
    changes = {}

    preview = document.get("text_preview")
    if preview and mask_personal_data(preview) != preview:
        changes["text_preview"] = mask_personal_data(preview)

    summary_text = (document.get("summary") or {}).get("summary_text")
    if summary_text and mask_personal_data(summary_text) != summary_text:
        changes["summary.summary_text"] = mask_personal_data(summary_text)

    sections = (document.get("keyword_analysis") or {}).get("highlighted_sections") or []
    masked_sections = [{**section, "excerpt": mask_personal_data(section.get("excerpt", ""))} for section in sections]
    if masked_sections != sections:
        changes["keyword_analysis.highlighted_sections"] = masked_sections

    update = {}
    if changes:
        update["$set"] = changes
    if "saved_path" in document:
        update["$unset"] = {"saved_path": ""}

    return update


async def main(apply: bool) -> None:
    client = AsyncMongoClient(settings.MONGODB_URL)
    collection = client[settings.MONGODB_DB_NAME]["documents"]

    total = changed = 0

    async for document in collection.find({}):
        total += 1
        update = build_update(document)

        if not update:
            continue

        changed += 1
        fields = list(update.get("$set", {})) + [f"remove {name}" for name in update.get("$unset", {})]
        print(f"{document.get('filename', document['_id'])}: {', '.join(fields)}")

        if apply:
            await collection.update_one({"_id": document["_id"]}, update)

    await client.close()

    action = "Updated" if apply else "Would update"
    print(f"\n{action} {changed} of {total} documents.")

    if changed and not apply:
        print("Nothing was changed. Run again with --apply to write the masked values.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="write changes (default: preview only)")
    asyncio.run(main(parser.parse_args().apply))
