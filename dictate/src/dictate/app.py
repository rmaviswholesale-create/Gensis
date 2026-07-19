"""CLI entry point. `--simulate <wav>` runs the full pipeline headlessly;
the tray app wiring lives here too (slice 6).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Sequence, TextIO

from dictate.chunker import SilenceChunker
from dictate.interfaces import TranscriptionEngine
from dictate.pipeline import DictationPipeline, Transform
from dictate.transcribe import read_wav_pcm16

log = logging.getLogger(__name__)


class _WriterInjector:
    def __init__(self, out: TextIO) -> None:
        self._out = out

    def inject(self, text: str) -> None:
        self._out.write(text + "\n")


def run_simulate(
    wav_path: str | Path,
    engine: TranscriptionEngine,
    transforms: Sequence[Transform],
    out: TextIO = sys.stdout,
) -> int:
    """Feed a WAV through chunker → engine → transforms, printing injected text."""
    data, sample_rate = read_wav_pcm16(wav_path)
    chunker = SilenceChunker(sample_rate=sample_rate)
    pipeline = DictationPipeline(engine, list(transforms), _WriterInjector(out))
    pipeline.start_utterance()
    step = sample_rate * 2 // 10  # 100ms of PCM16, mimicking live capture
    for i in range(0, len(data), step):
        for chunk in chunker.push(data[i : i + step]):
            pipeline.feed(chunk)
    tail = chunker.flush()
    if tail is not None:
        pipeline.feed(tail)
    pipeline.end_utterance()
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dictate", description=__doc__)
    parser.add_argument("--simulate", metavar="WAV", help="run the pipeline on a WAV file")
    parser.add_argument("--config", metavar="PATH", default=None, help="path to config.json")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    from dictate.config import load_config
    from dictate.dictionary import Dictionary
    from dictate.polish.rules import RulePolisher

    config = load_config(args.config)
    dictionary = Dictionary.load(config.dictionary_path)
    transforms: list[Transform] = [dictionary.apply, build_polisher(config).polish]

    if args.simulate:
        try:
            from dictate.transcribe import FasterWhisperEngine

            engine: TranscriptionEngine = FasterWhisperEngine(
                model=config.stt.model,
                device=config.stt.device,
                compute_type=config.stt.compute_type,
                language=config.stt.language,
            )
        except ImportError:
            print(
                "faster-whisper is not installed; install with: pip install 'dictate[stt]'",
                file=sys.stderr,
            )
            return 1
        return run_simulate(args.simulate, engine, transforms)

    from dictate.tray import run_tray_app

    return run_tray_app(config, transforms)


def build_polisher(config):  # type: ignore[no-untyped-def]
    from dictate.polish.rules import RulePolisher

    rules = RulePolisher()
    if config.polish.mode == "ollama":
        from dictate.polish.ollama import OllamaPolisher

        return OllamaPolisher(
            host=config.polish.ollama_host,
            model=config.polish.ollama_model,
            timeout_seconds=config.polish.timeout_seconds,
            fallback=rules,
        )
    return rules


if __name__ == "__main__":
    sys.exit(main())
