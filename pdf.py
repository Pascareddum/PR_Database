"""PDF generation via Playwright (headless Chromium).

Renders the sheet exactly as it appears on screen (not print media), then prints
to PDF. Produces a near-pixel copy of the browser preview.
"""
from __future__ import annotations

import subprocess
import sys

from playwright.sync_api import sync_playwright, Error as PWError


def _install_chromium():
    """Scarica Chromium al primo utilizzo (serve per eseguibile distribuito)."""
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=True,
    )


def build_pdf(url: str) -> bytes:
    try:
        return _render(url)
    except PWError as e:
        msg = str(e)
        if "Executable doesn't exist" in msg or "playwright install" in msg:
            _install_chromium()
            return _render(url)
        raise


def _render(url: str) -> bytes:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=[
            "--no-sandbox",
            "--font-render-hinting=none",
            "--disable-font-subpixel-positioning",
            "--disable-lcd-text",
            "--force-color-profile=srgb",
        ])
        try:
            # Viewport = A4 @ 96dpi (794 x 1123 px)
            ctx = browser.new_context(
                viewport={"width": 794, "height": 1123},
                device_scale_factor=2,
            )
            page = ctx.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            # Attendi scheda e immagini
            page.wait_for_selector("#sheet", state="attached", timeout=30000)
            page.wait_for_function(
                "Array.from(document.images).every(i => i.complete && i.naturalWidth > 0)",
                timeout=20000,
            )
            # Attendi che tutti i font siano effettivamente caricati (await Promise)
            page.evaluate("async () => { if (document.fonts) await document.fonts.ready; }")
            # Piccola pausa per animazioni/layout stabile
            page.wait_for_timeout(400)

            # Emula media "screen" così CSS @media print non si applica
            page.emulate_media(media="screen")

            # Isola la scheda: nascondi UI non-scheda, azzera padding body,
            # rimuovi shadow/radius dalle .page così ogni pagina riempie A4
            # Risolve color-mix e gradient delle card/numeri a colori flat per compat viewer PDF
            page.add_style_tag(content="""
                html, body { background: #ffffff !important; margin: 0 !important; padding: 0 !important; }
                .topbar, .toast, dialog, #toast, #update-badge { display: none !important; }
                main { padding: 0 !important; margin: 0 !important; max-width: none !important; }
                .no-print { display: none !important; }
                .sheet { gap: 0 !important; }
                .page { box-shadow: none !important; border-radius: 0 !important; margin: 0 !important; }
                /* Esercizio card: sostituisci shadow/color-mix con border piatto */
                .sheet-ex {
                    box-shadow: none !important;
                    border: 1px solid var(--brand) !important;
                    background: #ffffff !important;
                }
                /* Badge numero: colore pieno invece di gradient */
                .ex-num {
                    background: var(--brand) !important;
                    background-image: none !important;
                    box-shadow: none !important;
                    color: #ffffff !important;
                }
                /* Pulsante "Guarda l'esecuzione": flat */
                .sheet-video {
                    background: var(--brand) !important;
                    background-image: none !important;
                    box-shadow: none !important;
                    color: #ffffff !important;
                    border: none !important;
                }
                /* Info-card: bordo piatto, no shadow, bg bianco */
                .info-card {
                    background: #ffffff !important;
                    background-image: none !important;
                    box-shadow: none !important;
                    border: 1px solid var(--brand) !important;
                }
                .info-ico {
                    background: var(--brand) !important;
                    background-image: none !important;
                    box-shadow: none !important;
                    color: #ffffff !important;
                }
                /* Eyebrow: background-clip:text non supportato da tutti viewer → colore pieno */
                .eyebrow {
                    background: none !important;
                    background-image: none !important;
                    -webkit-background-clip: border-box !important;
                    background-clip: border-box !important;
                    color: var(--brand) !important;
                }
            """)
            # Riesegui split pagine dopo cambi stile
            page.evaluate("typeof splitOverflowPages === 'function' && splitOverflowPages()")
            # Reflow
            page.wait_for_timeout(200)

            # Misura altezza reale scheda per pagina senza whitespace
            pdf_bytes = page.pdf(
                width="210mm",
                height="297mm",
                print_background=True,
                margin={"top": "0mm", "right": "0mm", "bottom": "0mm", "left": "0mm"},
                prefer_css_page_size=False,
                scale=1.0,
                tagged=True,
            )
        finally:
            browser.close()
    return pdf_bytes
