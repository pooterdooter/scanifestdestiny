"""Main CLI entry point for Scanifest Destiny."""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from . import __version__
from .config import settings, LOG_FILE, ModelType, SpeedMode
from .pdf_extractor import extract_text, get_pdf_info
from .claude_namer import suggest_name, check_claude_available
from .ledger import get_ledger
from .learning import get_learning_system
from .pdf_splitter import interactive_split, analyze_pdf_for_split
from .metadata_extractor import extract_to_csv, load_template, create_template


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO

    # File handler
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def find_pdfs(path: Path, recursive: bool = False) -> List[Path]:
    """Find PDF files at the given path."""
    path = Path(path)

    if path.is_file():
        if path.suffix.lower() == '.pdf':
            return [path]
        else:
            return []

    if path.is_dir():
        pattern = '**/*.pdf' if recursive else '*.pdf'
        return sorted(path.glob(pattern))

    return []


def process_single_pdf(
    pdf_path: Path,
    dry_run: bool = False,
    force: bool = False,
    no_patterns: bool = False,
) -> Optional[Path]:
    """
    Process a single PDF file: extract text, get name suggestion, rename.

    Returns the new path if renamed, None otherwise.
    """
    logger = logging.getLogger(__name__)

    logger.info(f"\n{'='*60}")
    logger.info(f"Processing: {pdf_path.name}")
    logger.info(f"{'='*60}")

    ledger = get_ledger()
    learning = get_learning_system()

    # Check if already processed (by looking at ledger)
    existing = ledger.find_by_original_name(pdf_path.name)
    if existing and not force:
        logger.info(f"[SKIP] Already processed on {existing[0].timestamp[:10]}")
        logger.info(f"       Renamed to: {existing[0].new_name}")
        return None

    # Step 1: Extract text
    logger.info(f"[1/3] Extracting text (mode: {settings.speed_mode})...")
    try:
        extraction = extract_text(pdf_path)
    except Exception as e:
        logger.error(f"[ERROR] Failed to extract text: {e}")
        return None

    if extraction.is_empty:
        logger.warning("[WARN] No text could be extracted from this PDF")
        return None

    logger.info(f"      Extracted {len(extraction.text)} chars via {extraction.method}")
    logger.info(f"      Pages: {extraction.pages_processed}/{extraction.total_pages}")

    # Step 2: Check learning system for known patterns/corrections
    correction = None
    pattern_match = None

    if not no_patterns:
        correction = learning.get_correction_suggestion(extraction.content_hash)
        pattern_match = learning.find_matching_pattern(extraction.text, extraction.content_hash)

    new_name = None
    confidence = 0.0
    model_used = "learned"
    pattern_id = None
    reasoning = None

    if correction:
        # Use corrected name from previous user correction
        new_name = correction
        confidence = 1.0
        reasoning = "Applied from user correction"
        logger.info(f"[2/3] Using learned correction: {new_name}")

    elif pattern_match:
        # Use pattern-based naming
        pattern, score = pattern_match
        new_name = pattern.description_template
        confidence = score * pattern.confidence_avg
        pattern_id = pattern.pattern_id
        reasoning = f"Matched pattern {pattern_id}"
        logger.info(f"[2/3] Using learned pattern (score: {score:.2f}): {new_name}")

    else:
        # Call Claude for naming suggestion
        logger.info(f"[2/3] Requesting name from Claude ({settings.model})...")
        try:
            result = suggest_name(extraction.text, settings.model)
            new_name = result.get_filename()
            confidence = result.confidence
            model_used = result.model_used
            reasoning = result.reasoning
            logger.info(f"      Suggested: {new_name}")
            logger.info(f"      Confidence: {confidence:.0%}")
            logger.info(f"      Reasoning: {reasoning}")
        except Exception as e:
            logger.error(f"[ERROR] Claude naming failed: {e}")
            return None

    # Ensure unique filename
    new_path = pdf_path.parent / new_name
    counter = 1
    base_name = new_path.stem
    while new_path.exists() and new_path != pdf_path:
        new_path = pdf_path.parent / f"{base_name}_{counter}.pdf"
        counter += 1

    # Step 3: Rename (or simulate)
    logger.info(f"[3/3] {'[DRY RUN] Would rename' if dry_run else 'Renaming'}:")
    logger.info(f"      {pdf_path.name}")
    logger.info(f"   -> {new_path.name}")

    if not dry_run:
        try:
            pdf_path.rename(new_path)
            logger.info("      [OK] Renamed successfully")

            # Record in ledger
            ledger.add_entry(
                original_path=pdf_path,
                new_path=new_path,
                model_used=model_used,
                confidence=confidence,
                content_hash=extraction.content_hash,
                extraction_method=extraction.method,
                pattern_id=pattern_id,
                reasoning=reasoning,
            )

            # Learn from this success (if Claude was used)
            if model_used != "learned":
                learning.learn_from_success(
                    text=extraction.text,
                    suggested_name=new_path.name,
                    confidence=confidence,
                    content_hash=extraction.content_hash,
                )

            return new_path

        except Exception as e:
            logger.error(f"[ERROR] Failed to rename: {e}")
            return None

    return new_path  # Return path even in dry-run for reporting


def cmd_process(args: argparse.Namespace) -> int:
    """Handle the 'process' command."""
    logger = logging.getLogger(__name__)

    # Apply settings from args
    settings.model = args.model
    settings.speed_mode = args.speed
    settings.dry_run = args.dry_run
    settings.verbose = args.verbose

    # Check Claude availability
    if not check_claude_available():
        logger.error("Claude Code CLI is not available.")
        logger.error("Please ensure 'claude' command is in your PATH.")
        return 1

    # Find PDFs to process
    pdfs = find_pdfs(args.path, args.recursive)

    if not pdfs:
        logger.warning(f"No PDF files found at: {args.path}")
        return 0

    logger.info(f"Found {len(pdfs)} PDF(s) to process")
    if args.dry_run:
        logger.info("[DRY RUN MODE - No files will be renamed]")
    if args.no_patterns:
        logger.info("[NO PATTERNS MODE - Always using Claude AI]")
    if args.split:
        logger.info("[SPLIT MODE - Will check for multi-document PDFs]")

    # Process each PDF
    processed = 0
    failed = 0
    skipped = 0
    split_count = 0

    for pdf in pdfs:
        files_to_process = [pdf]

        # Check for multi-document PDFs if --split is enabled
        if args.split:
            pages, segments = analyze_pdf_for_split(pdf, args.model)
            if segments and len(segments) > 1:
                logger.info(f"\n[SPLIT] {pdf.name} contains {len(segments)} documents:")
                for seg in segments:
                    logger.info(f"         - {seg}")

                if args.dry_run:
                    logger.info("[DRY RUN] Would split into separate files")
                else:
                    # Interactive prompt with full options
                    print(f"\nSplit '{pdf.name}' into {len(segments)} documents?")
                    print("  [Y] Yes, split as shown")
                    print("  [N] No, keep as single document")
                    print("  [P] Split by individual pages")
                    print("  [S] Skip this file")

                    while True:
                        choice = input("\nChoice [Y/N/P/S]: ").strip().upper()

                        if choice in ('', 'Y'):
                            from .pdf_splitter import split_pdf, DocumentSegment
                            new_files = split_pdf(pdf, segments)
                            split_count += len(new_files)
                            files_to_process = new_files
                            print(f"Delete original '{pdf.name}'? [y/N]: ", end="")
                            if input().strip().lower() == 'y':
                                pdf.unlink()
                                logger.info(f"Deleted: {pdf.name}")
                            break

                        elif choice == 'N':
                            logger.info("Keeping as single document.")
                            break

                        elif choice == 'P':
                            from .pdf_splitter import split_pdf, DocumentSegment
                            page_segments = [
                                DocumentSegment(
                                    start_page=i,
                                    end_page=i,
                                    doc_type="Page",
                                    suggested_name=f"page_{i+1}",
                                    confidence=1.0
                                )
                                for i in range(len(pages))
                            ]
                            new_files = split_pdf(pdf, page_segments)
                            split_count += len(new_files)
                            files_to_process = new_files
                            print(f"Delete original '{pdf.name}'? [y/N]: ", end="")
                            if input().strip().lower() == 'y':
                                pdf.unlink()
                                logger.info(f"Deleted: {pdf.name}")
                            break

                        elif choice == 'S':
                            logger.info(f"Skipping: {pdf.name}")
                            skipped += 1
                            files_to_process = []
                            break

                        else:
                            print("Invalid choice. Please enter Y, N, P, or S.")

                    if not files_to_process:
                        continue

        # Process each file (original or split results)
        for file_to_process in files_to_process:
            result = process_single_pdf(
                file_to_process,
                dry_run=args.dry_run,
                force=args.force,
                no_patterns=args.no_patterns
            )
            if result:
                processed += 1
            elif result is None:
                skipped += 1
            else:
                failed += 1

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total PDFs found: {len(pdfs)}")
    if args.split and split_count > 0:
        logger.info(f"Files created from splits: {split_count}")
    logger.info(f"Processed: {processed}")
    logger.info(f"Skipped: {skipped}")
    logger.info(f"Failed: {failed}")

    return 0 if failed == 0 else 1


def cmd_history(args: argparse.Namespace) -> int:
    """Handle the 'history' command."""
    logger = logging.getLogger(__name__)
    ledger = get_ledger()

    if args.summary:
        # Show summary statistics
        stats = ledger.get_summary()
        logger.info("\nLedger Summary")
        logger.info("=" * 40)
        logger.info(f"Total processed: {stats['total_processed']}")
        logger.info(f"Average confidence: {stats['average_confidence']}")
        logger.info(f"Patterns applied: {stats['patterns_applied']}")
        logger.info(f"\nModels used:")
        for model, count in stats.get('models_used', {}).items():
            logger.info(f"  {model}: {count}")
        logger.info(f"\nExtraction methods:")
        for method, count in stats.get('extraction_methods', {}).items():
            logger.info(f"  {method}: {count}")
        if stats.get('first_entry'):
            logger.info(f"\nFirst entry: {stats['first_entry'][:10]}")
            logger.info(f"Last entry: {stats['last_entry'][:10]}")
    else:
        # Show recent entries
        entries = ledger.get_entries(limit=args.last)
        if not entries:
            logger.info("No entries in ledger yet.")
            return 0

        logger.info(f"\nLast {len(entries)} rename(s):")
        logger.info("=" * 60)
        for entry in entries:
            logger.info(f"\n{entry.timestamp[:19]}")
            logger.info(f"  {entry.original_name}")
            logger.info(f"  -> {entry.new_name}")
            logger.info(f"  Model: {entry.model_used}, Confidence: {entry.confidence:.0%}")

    return 0


def cmd_learn(args: argparse.Namespace) -> int:
    """Handle the 'learn' command."""
    logger = logging.getLogger(__name__)
    learning = get_learning_system()
    ledger = get_ledger()

    if args.scan_corrections:
        # Scan for manual renames
        logger.info("Scanning for manual corrections...")
        corrections = ledger.detect_manual_renames()

        if not corrections:
            logger.info("No manual corrections detected.")
            return 0

        logger.info(f"Found {len(corrections)} potential correction(s):")
        for cor in corrections:
            logger.info(f"\n  Original: {cor['original_entry']['new_name']}")
            logger.info(f"  Possibly renamed to: {cor['potential_new_name']}")

            # Prompt user to confirm
            response = input("  Apply this correction? (y/N): ").strip().lower()
            if response == 'y':
                # Would need to re-extract text or use stored hash
                logger.info("  [TODO] Correction recording requires implementation")

    elif args.stats:
        # Show learning stats
        stats = learning.get_stats()
        logger.info("\nLearning System Stats")
        logger.info("=" * 40)
        logger.info(f"Total patterns: {stats['total_patterns']}")
        logger.info(f"Total corrections: {stats['total_corrections']}")
        if stats['most_used_patterns']:
            logger.info("\nMost used patterns:")
            for pat_id, count in stats['most_used_patterns']:
                logger.info(f"  {pat_id}: {count} times")

    return 0


def cmd_split(args: argparse.Namespace) -> int:
    """Handle the 'split' command - detect and split multi-document PDFs (no renaming)."""
    logger = logging.getLogger(__name__)

    # Apply settings
    settings.model = args.model

    # Check Claude availability
    if not check_claude_available():
        logger.error("Claude Code CLI is not available.")
        return 1

    # Find PDFs to analyze
    pdfs = find_pdfs(args.path, args.recursive)

    if not pdfs:
        logger.warning(f"No PDF files found at: {args.path}")
        return 0

    logger.info(f"Found {len(pdfs)} PDF(s) to analyze for splitting")
    if args.analyze_only:
        logger.info("[ANALYZE ONLY - No files will be modified]")

    all_new_files = []

    for pdf in pdfs:
        if args.analyze_only:
            # Just show what would be split, don't actually split
            pages, segments = analyze_pdf_for_split(pdf, args.model)
            logger.info(f"\n{pdf.name}: {len(pages)} pages")
            if segments and len(segments) > 1:
                logger.info(f"  Would split into {len(segments)} documents:")
                for seg in segments:
                    logger.info(f"    - {seg}")
            else:
                logger.info("  Single document, no split needed")
        else:
            # Interactive split
            new_files = interactive_split(pdf, args.model)
            all_new_files.extend(new_files)

    if not args.analyze_only and all_new_files:
        logger.info(f"\n{'='*60}")
        logger.info(f"Split complete. {len(all_new_files)} file(s) created.")
        logger.info(f"Run 'process' command to rename them.")

    return 0


def cmd_extract(args: argparse.Namespace) -> int:
    """Handle the 'extract' command - extract metadata using CSV template."""
    logger = logging.getLogger(__name__)

    # Check Claude availability
    if not check_claude_available():
        logger.error("Claude Code CLI is not available.")
        return 1

    # Handle template creation
    if args.create_template:
        fields = [f.strip() for f in args.create_template.split(',')]
        output = args.output or Path('template.csv')
        create_template(output, fields)
        logger.info(f"Template created: {output}")
        logger.info(f"Fields: {', '.join(fields)}")
        return 0

    # Validate inputs
    if not args.template:
        logger.error("Template file required. Use --template or --create-template")
        return 1

    if not args.path:
        logger.error("PDF path required.")
        return 1

    template_path = Path(args.template)
    if not template_path.exists():
        logger.error(f"Template not found: {template_path}")
        return 1

    # Find PDFs
    pdfs = find_pdfs(args.path, args.recursive)
    if not pdfs:
        logger.warning(f"No PDF files found at: {args.path}")
        return 0

    logger.info(f"Found {len(pdfs)} PDF(s) to process")

    # Load template to show fields
    try:
        fields = load_template(template_path)
        logger.info(f"Extracting fields: {', '.join(fields)}")
    except Exception as e:
        logger.error(f"Failed to load template: {e}")
        return 1

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"extracted_{timestamp}.csv")

    # Extract metadata
    logger.info(f"Extracting metadata using {args.model} model...")
    try:
        result_path = extract_to_csv(
            pdfs,
            template_path,
            output_path,
            model=args.model,
            include_metadata_columns=not args.no_metadata,
        )
        logger.info(f"\n{'='*60}")
        logger.info(f"Extraction complete!")
        logger.info(f"Output: {result_path}")
        logger.info(f"PDFs processed: {len(pdfs)}")
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return 1

    return 0


def cmd_info(args: argparse.Namespace) -> int:
    """Handle the 'info' command - show PDF metadata without processing."""
    logger = logging.getLogger(__name__)

    pdf_path = Path(args.path)
    if not pdf_path.exists():
        logger.error(f"File not found: {pdf_path}")
        return 1

    info = get_pdf_info(pdf_path)

    logger.info(f"\nPDF Info: {info['filename']}")
    logger.info("=" * 40)
    logger.info(f"Pages: {info['pages']}")
    logger.info(f"Path: {info['path']}")

    if info['metadata']:
        logger.info("\nMetadata:")
        for key, value in info['metadata'].items():
            if value:
                logger.info(f"  {key}: {value}")

    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scanifest Destiny - Intelligent PDF renaming tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--version', action='version', version=f'%(prog)s {__version__}'
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Enable verbose output'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Process command
    process_parser = subparsers.add_parser(
        'process', help='Process and rename PDF files'
    )
    process_parser.add_argument(
        'path', type=Path, help='PDF file or directory to process'
    )
    process_parser.add_argument(
        '-r', '--recursive', action='store_true',
        help='Recursively process subdirectories'
    )
    process_parser.add_argument(
        '-m', '--model', type=str, default='sonnet',
        choices=['haiku', 'sonnet', 'opus'],
        help='Claude model to use (default: sonnet)'
    )
    process_parser.add_argument(
        '-s', '--speed', type=str, default='balanced',
        choices=['fast', 'balanced', 'thorough'],
        help='Processing speed/accuracy tradeoff (default: balanced)'
    )
    process_parser.add_argument(
        '-n', '--dry-run', action='store_true',
        help='Preview changes without renaming'
    )
    process_parser.add_argument(
        '-f', '--force', action='store_true',
        help='Re-process files even if already in ledger'
    )
    process_parser.add_argument(
        '--no-patterns', action='store_true',
        help='Skip pattern matching, always use Claude AI'
    )
    process_parser.add_argument(
        '--split', action='store_true',
        help='Check for multi-document PDFs and offer to split before processing'
    )

    # History command
    history_parser = subparsers.add_parser(
        'history', help='View rename history'
    )
    history_parser.add_argument(
        '-l', '--last', type=int, default=10,
        help='Number of recent entries to show (default: 10)'
    )
    history_parser.add_argument(
        '--summary', action='store_true',
        help='Show summary statistics'
    )

    # Learn command
    learn_parser = subparsers.add_parser(
        'learn', help='Manage learning system'
    )
    learn_parser.add_argument(
        '--scan-corrections', action='store_true',
        help='Scan for manual renames and learn from them'
    )
    learn_parser.add_argument(
        '--stats', action='store_true',
        help='Show learning system statistics'
    )

    # Info command
    info_parser = subparsers.add_parser(
        'info', help='Show PDF metadata'
    )
    info_parser.add_argument(
        'path', type=Path, help='PDF file to inspect'
    )

    # Split command
    split_parser = subparsers.add_parser(
        'split', help='Detect and split multi-document PDFs (no renaming)'
    )
    split_parser.add_argument(
        'path', type=Path, help='PDF file or directory to analyze'
    )
    split_parser.add_argument(
        '-r', '--recursive', action='store_true',
        help='Recursively process subdirectories'
    )
    split_parser.add_argument(
        '-m', '--model', type=str, default='sonnet',
        choices=['haiku', 'sonnet', 'opus'],
        help='Claude model for boundary detection (default: sonnet)'
    )
    split_parser.add_argument(
        '-a', '--analyze-only', action='store_true',
        help='Only analyze and show splits, do not modify files'
    )

    # Extract command
    extract_parser = subparsers.add_parser(
        'extract', help='Extract metadata from PDFs using a CSV template'
    )
    extract_parser.add_argument(
        'path', type=Path, nargs='?',
        help='PDF file or directory to process'
    )
    extract_parser.add_argument(
        '-t', '--template', type=Path,
        help='CSV template file with column headers as fields to extract'
    )
    extract_parser.add_argument(
        '-o', '--output', type=Path,
        help='Output CSV file path (default: extracted_TIMESTAMP.csv)'
    )
    extract_parser.add_argument(
        '-r', '--recursive', action='store_true',
        help='Recursively process subdirectories'
    )
    extract_parser.add_argument(
        '-m', '--model', type=str, default='sonnet',
        choices=['haiku', 'sonnet', 'opus'],
        help='Claude model to use (default: sonnet)'
    )
    extract_parser.add_argument(
        '--create-template', type=str, metavar='FIELDS',
        help='Create a blank template with comma-separated field names'
    )
    extract_parser.add_argument(
        '--no-metadata', action='store_true',
        help='Exclude _file_name, _confidence, etc. columns from output'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=getattr(args, 'verbose', False))

    if not args.command:
        parser.print_help()
        return 0

    # Dispatch to command handler
    commands = {
        'process': cmd_process,
        'history': cmd_history,
        'learn': cmd_learn,
        'info': cmd_info,
        'split': cmd_split,
        'extract': cmd_extract,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
