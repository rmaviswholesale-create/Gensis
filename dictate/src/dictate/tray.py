"""System tray app: wires every component together and shows recording state.

All heavy/OS imports happen inside run_tray_app so the rest of the package
stays importable headlessly.
"""

from __future__ import annotations

import logging
import sys
from typing import Sequence

from dictate.config import Config
from dictate.pipeline import Transform

log = logging.getLogger(__name__)


def run_tray_app(config: Config, transforms: Sequence[Transform]) -> int:
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError:
        print(
            "tray dependencies missing; install with: pip install 'dictate[windows]'",
            file=sys.stderr,
        )
        return 1

    from dictate.audio import MicrophoneCapture
    from dictate.chunker import SilenceChunker
    from dictate.hotkey import HotkeyController
    from dictate.inject import TypingInjector
    from dictate.pipeline import DictationPipeline, PipelineRunner
    from dictate.session import CaptureSession

    try:
        from dictate.transcribe import FasterWhisperEngine

        # Load the model up front so the first utterance isn't slow.
        log.info("loading whisper model '%s'...", config.stt.model)
        engine = FasterWhisperEngine(
            model=config.stt.model,
            device=config.stt.device,
            compute_type=config.stt.compute_type,
            language=config.stt.language,
        )
    except ImportError:
        print(
            "faster-whisper missing; install with: pip install 'dictate[stt]'",
            file=sys.stderr,
        )
        return 1

    injector = TypingInjector(
        clipboard_threshold_chars=config.inject.clipboard_threshold_chars,
        pre_inject_delay_ms=config.inject.pre_inject_delay_ms,
    )
    pipeline = DictationPipeline(engine, list(transforms), injector)
    runner = PipelineRunner(pipeline)
    runner.start()
    capture = MicrophoneCapture(sample_rate=config.audio.sample_rate, device=config.audio.device)
    session = CaptureSession(
        runner=runner,
        capture=capture,
        chunker_factory=lambda: SilenceChunker(sample_rate=config.audio.sample_rate),
    )

    def make_icon_image(recording: bool) -> "Image.Image":
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        color = (220, 50, 50, 255) if recording else (130, 130, 130, 255)
        draw.ellipse((8, 8, 56, 56), fill=color)
        return image

    icon = pystray.Icon(
        "dictate", make_icon_image(False), "dictate — press hotkey to talk"
    )

    def on_start() -> None:
        session.begin()
        icon.icon = make_icon_image(True)

    def on_stop() -> None:
        session.end()
        icon.icon = make_icon_image(False)

    hotkey = HotkeyController(
        combo=config.hotkey.combo,
        mode=config.hotkey.mode,
        on_start=on_start,
        on_stop=on_stop,
    )
    hotkey.start()

    def quit_app(icon: "pystray.Icon", item: object) -> None:
        icon.stop()

    icon.menu = pystray.Menu(pystray.MenuItem("Quit", quit_app))
    log.info("ready — %s (%s mode)", config.hotkey.combo, config.hotkey.mode)
    try:
        icon.run()  # blocks until Quit
    finally:
        hotkey.stop()
        session.end()
        runner.close()
    return 0
