"""
TerraQuant — Demo Assets & Input Generator
Populates all required synthetic and sensory demo inputs for TerraQuant:
  1. backend/data/supplier_sla.json (Realistic $155,000 SLA contract)
  2. backend/data/historical_prices.csv (252 trading days GARCH price series)
  3. frontend/public/samples/ (3 high-res macro inspection sample images)
  4. backend/data/sample_inspector_voice.wav (Inspector Garcia dock 4 voice note)

Usage:
  python backend/scripts/generate_demo_inputs.py [--live-images]
"""

import argparse
import json
import logging
import math
import os
import struct
import sys
import wave
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Resolve project directories
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
ROOT_DIR = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
SAMPLES_DIR = ROOT_DIR / "frontend" / "public" / "samples"

DATA_DIR.mkdir(parents=True, exist_ok=True)
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("generate_demo_inputs")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Generate backend/data/supplier_sla.json
# ─────────────────────────────────────────────────────────────────────────────

def generate_supplier_sla() -> Path:
    target = DATA_DIR / "supplier_sla.json"
    sla_data = {
        "contract_id": "SLA-TQ-2026-B408",
        "supplier": {
            "name": "AgroSource Global Ltd.",
            "registration": "AG-2024-77432",
            "country": "Brazil",
            "commodity": "Arabica Coffee (Specialty Grade AA)"
        },
        "buyer": {
            "name": "TerraQuant Commodities Pvt. Ltd.",
            "registration": "TQ-IN-2024-00112",
            "country": "India / Global"
        },
        "contract_terms": {
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "commodity": "Arabica Coffee Beans",
            "quantity_mt": 50.0,
            "unit_price_per_mt_usd": 3100.00,
            "total_contract_value_usd": 155000.00,
            "currency": "USD",
            "payment_terms_days": 30
        },
        "quality_thresholds": {
            "grade_a_max_defect_pct": 2.0,
            "sla_breach_defect_pct": 5.0,
            "max_defect_pct": 5.0,
            "max_moisture_pct": 12.0,
            "min_screen_size": 16,
            "defect_categories": [
                "moisture_clumps",
                "black_beans",
                "discoloration",
                "sour_beans",
                "insect_damage",
                "foreign_debris"
            ]
        },
        "penalty_clauses": {
            "defect_breach_penalty_pct": 15.0,
            "late_delivery_penalty_per_day_usd": 1200.00,
            "quality_breach_action": "debit_note_plus_price_renegotiation",
            "max_penalty_cap_pct": 25.0
        },
        "financial_controls": {
            "working_capital_cap_usd": 250000.00,
            "payment_terms_days": 30,
            "letter_of_credit_required": True,
            "escrow_pct": 10.0
        },
        "hedge_rules": {
            "strategy": "Long Strap",
            "ratio": "2 Calls + 1 Put",
            "rationale": "Defect-driven shipment rejection triggers severe localized supply shortage risk with asymmetric upside price spikes, while maintaining downside floor protection.",
            "allowed_instruments": [
                "futures",
                "options_calls",
                "options_puts",
                "strap"
            ]
        },
        "audit": {
            "inspection_point": "Dock 4 Receiving Bay",
            "third_party_inspector": "SGS Global Agricultural Services",
            "dispute_resolution": "ICC_arbitration_Geneva"
        }
    }

    with target.open("w", encoding="utf-8") as f:
        json.dump(sla_data, f, indent=2)

    logger.info(f"Generated SLA contract: {target} (Value: ${sla_data['contract_terms']['total_contract_value_usd']:,.2f})")
    return target


# ─────────────────────────────────────────────────────────────────────────────
# 2. Generate backend/data/historical_prices.csv
# ─────────────────────────────────────────────────────────────────────────────

def generate_historical_prices() -> Path:
    target = DATA_DIR / "historical_prices.csv"
    np.random.seed(42)

    n_days = 252
    start_price = 2850.0
    end_price_target = 3100.0

    # Geometric drift to bridge from ~$2,850 to ~$3,100
    total_drift = math.log(end_price_target / start_price)
    mu = total_drift / n_days

    # Stable GARCH(1,1) model parameters (omega, alpha, beta with alpha + beta = 0.96 < 1)
    omega = 0.000006
    alpha = 0.08
    beta = 0.88
    sigma2 = np.zeros(n_days)
    sigma2[0] = 0.00015  # ~1.2% daily baseline volatility

    eps = np.random.standard_normal(n_days)
    log_returns = np.zeros(n_days)
    log_returns[0] = mu + math.sqrt(sigma2[0]) * eps[0]

    for t in range(1, n_days):
        sigma2[t] = omega + alpha * (log_returns[t - 1] ** 2) + beta * sigma2[t - 1]
        # Realistic commodity supply & frost shocks (GARCH volatility clusters)
        if t in (45, 98, 142, 185, 230) or np.random.rand() < 0.035:
            sigma2[t] *= np.random.uniform(1.8, 2.6)
        log_returns[t] = math.sqrt(sigma2[t]) * eps[t]

    # Brownian bridge to ensure clean start at ~$2,850 and terminal price near ~$3,100
    cum_returns = np.cumsum(log_returns)
    linear_drift = np.linspace(0, total_drift - cum_returns[-1], n_days)
    adj_returns = np.diff(cum_returns + linear_drift, prepend=0)
    prices = start_price * np.exp(cum_returns + linear_drift)

    # Date range for 252 trading days ending today
    end_date = pd.Timestamp("2026-10-29")
    dates = pd.bdate_range(end=end_date, periods=n_days)

    # Realistic volume correlated with volatility shocks
    base_volume = 24000
    volumes = []
    for t in range(n_days):
        vol_mult = 1.0 + (abs(log_returns[t]) / math.sqrt(sigma2[t])) * 0.4
        day_vol = int(base_volume * vol_mult * np.random.uniform(0.85, 1.25))
        volumes.append(day_vol)

    df = pd.DataFrame({
        "Date": dates.strftime("%Y-%m-%d"),
        "Close": np.round(prices, 2),
        "Return": np.round(adj_returns, 6),
        "Volume": volumes
    })

    df.to_csv(target, index=False)
    logger.info(
        f"Generated 252 days price series: {target} "
        f"(Start: ${df['Close'].iloc[0]:,.2f}, End: ${df['Close'].iloc[-1]:,.2f}, "
        f"Min: ${df['Close'].min():,.2f}, Max: ${df['Close'].max():,.2f})"
    )
    return target


# ─────────────────────────────────────────────────────────────────────────────
# 3. Generate Inspection Sample Images
# ─────────────────────────────────────────────────────────────────────────────

def _call_meta_image_api(prompt: str, out_path: Path, api_key: str):
    """Optional live Meta API call when --live-images is passed."""
    import base64
    import httpx

    logger.info(f"Calling Meta Image API (muse-image-1.0) for {out_path.name}...")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "muse-image-1.0",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "response_format": "b64_json"
    }
    with httpx.Client(timeout=90.0) as client:
        resp = client.post("https://api.meta.ai/v1/images/generations", headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        b64 = data["data"][0]["b64_json"]
        out_path.write_bytes(base64.b64decode(b64))
    logger.info(f"Saved live Meta AI image: {out_path}")


def generate_procedural_inspection_image(
    filename: str,
    defect_level: str,  # 'grade_a' | 'moderate' | 'critical'
    width: int = 1280,
    height: int = 720
) -> tuple[Path, dict]:
    """
    Generates instant photorealistic high-contrast macro inspection images
    of coffee seed trays with dark moisture clumps & defects at exact coordinates.
    """
    target = SAMPLES_DIR / filename
    np.random.seed(101 if defect_level == "grade_a" else 202 if defect_level == "moderate" else 303)

    # 1. Base Stainless Steel Inspection Tray
    img = Image.new("RGB", (width, height), (38, 43, 54))
    draw = ImageDraw.Draw(img)

    # Tray metallic lighting gradient
    for y in range(height):
        grad = int(35 + 25 * math.sin(y / height * math.pi))
        draw.line([(0, y), (width, y)], fill=(grad, grad + 4, grad + 10))

    # Measurement grid lines & borders
    for x in range(60, width - 60, 100):
        draw.line([(x, 40), (x, height - 40)], fill=(50, 58, 72), width=1)
    for y in range(60, height - 60, 100):
        draw.line([(40, y), (width - 40, y)], fill=(50, 58, 72), width=1)

    # Tray rim
    draw.rectangle([30, 30, width - 30, height - 30], outline=(100, 116, 139), width=3)
    draw.rectangle([34, 34, width - 34, height - 34], outline=(30, 41, 59), width=2)

    # 2. Defect Zones setup
    # Coordinates of defect clusters [x1, y1, x2, y2]
    defect_boxes = []
    if defect_level == "moderate":
        # ~4.5% area localized moisture clump in middle-left
        defect_boxes.append({"x1": 340, "y1": 260, "x2": 560, "y2": 460, "type": "moisture_clump"})
    elif defect_level == "critical":
        # ~14.0% area severe moisture clumping + dark black bean necrosis (two large clusters)
        defect_boxes.append({"x1": 240, "y1": 200, "x2": 580, "y2": 500, "type": "severe_moisture_clump"})
        defect_boxes.append({"x1": 720, "y1": 320, "x2": 1040, "y2": 580, "type": "black_bean_necrosis"})

    def is_in_defect(px, py):
        for box in defect_boxes:
            if box["x1"] <= px <= box["x2"] and box["y1"] <= py <= box["y2"]:
                return box
        return None

    # 3. Dense Seed Bed Generation
    # Create ~1,400 realistic individual seeds/beans across the tray
    grid_step_x = 26
    grid_step_y = 24
    for gx in range(50, width - 50, grid_step_x):
        for gy in range(50, height - 50, grid_step_y):
            # Jitter position
            bx = gx + int(np.random.uniform(-9, 9))
            by = gy + int(np.random.uniform(-9, 9))
            defect_match = is_in_defect(bx, by)

            bw = int(np.random.uniform(16, 24))
            bh = int(np.random.uniform(12, 17))
            angle = np.random.uniform(0, math.pi)

            # Color palette
            if defect_match:
                if defect_match["type"] == "black_bean_necrosis":
                    # Pitch black / charred defect with rotting edge
                    base_color = (int(np.random.uniform(15, 30)), int(np.random.uniform(12, 24)), int(np.random.uniform(15, 26)))
                    center_crease = (8, 6, 8)
                else:
                    # Dark moisture soaked clumping (deep soggy brownish-black with mold tint)
                    base_color = (int(np.random.uniform(40, 65)), int(np.random.uniform(30, 48)), int(np.random.uniform(22, 35)))
                    center_crease = (25, 18, 14)
            else:
                # Grade-A healthy specialty bean: rich golden amber olive-brown
                base_color = (int(np.random.uniform(145, 185)), int(np.random.uniform(105, 135)), int(np.random.uniform(65, 90)))
                center_crease = (90, 60, 40)

            # Bean shadow
            draw.ellipse([bx - bw // 2 + 3, by - bh // 2 + 4, bx + bw // 2 + 3, by + bh // 2 + 4], fill=(20, 24, 32))

            # Bean body
            draw.ellipse([bx - bw // 2, by - bh // 2, bx + bw // 2, by + bh // 2], fill=base_color, outline=center_crease, width=1)

            # Center crease / fissure of coffee bean
            cx1 = bx - int(math.cos(angle) * (bw // 3))
            cy1 = by - int(math.sin(angle) * (bh // 3))
            cx2 = bx + int(math.cos(angle) * (bw // 3))
            cy2 = by + int(math.sin(angle) * (bh // 3))
            draw.line([(cx1, cy1), (cx2, cy2)], fill=center_crease, width=2)

            # Specular highlight on healthy beans
            if not defect_match and np.random.rand() > 0.4:
                hx = bx - int(bw * 0.2)
                hy = by - int(bh * 0.25)
                draw.point((hx, hy), fill=(230, 210, 180))

    # 4. Moisture Clumping & Spoilage Overlays
    for box in defect_boxes:
        # Dark moisture aggregation stain
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        ol_draw = ImageDraw.Draw(overlay)
        stain_color = (15, 12, 10, 140) if "severe" in box["type"] else (30, 22, 15, 100)
        ol_draw.ellipse([box["x1"] - 15, box["y1"] - 15, box["x2"] + 15, box["y2"] + 15], fill=stain_color)
        overlay = overlay.filter(ImageFilter.GaussianBlur(radius=18))
        img.paste(overlay, (0, 0), overlay)

        # High-contrast inspection bounding box overlay for visual verification
        draw.rectangle([box["x1"], box["y1"], box["x2"], box["y2"]], outline=(239, 68, 68, 220), width=3)
        draw.rectangle([box["x1"], box["y1"] - 22, box["x1"] + 190, box["y1"]], fill=(185, 28, 28))
        draw.text((box["x1"] + 6, box["y1"] - 18), f"SAM 3.1: {box['type'].upper()}", fill=(255, 255, 255))

    # Header dock tag on tray
    draw.rectangle([45, 45, 340, 75], fill=(15, 23, 42, 230), outline=(51, 65, 85))
    grade_tag = "GRADE-A CERTIFIED (0.8% DEFECT)" if defect_level == "grade_a" else (
        "MODERATE CLUMP (4.4% DEFECT)" if defect_level == "moderate" else
        "CRITICAL SPOILAGE (14.2% DEFECT)"
    )
    tag_color = (52, 211, 153) if defect_level == "grade_a" else (
        (251, 191, 36) if defect_level == "moderate" else (248, 113, 113)
    )
    draw.text((55, 52), f"TRAY 408 | {grade_tag}", fill=tag_color)

    img.save(target, "PNG", quality=95)
    logger.info(f"Generated inspection sample: {target} ({defect_level}, {len(defect_boxes)} defect regions)")
    return target, {"file": str(target), "defect_boxes": defect_boxes}


def generate_all_samples(live_images: bool = False) -> list[Path]:
    api_key = os.getenv("MODEL_API_KEY", "")
    samples = [
        ("batch_grade_a.png", "grade_a", "Macro photographic inspection tray of specialty Grade-A coffee beans, perfectly uniform olive-amber color, zero mold, food grade tray"),
        ("batch_moderate_clump.png", "moderate", "Inspection tray of coffee beans with a localized moderate dark damp moisture clump on the left side, visible humidity discoloration"),
        ("batch_critical_spoilage.png", "critical", "Inspection tray of coffee beans with severe black bean fungal necrosis and dark water-damaged clumps covering fourteen percent of tray")
    ]

    generated = []
    for filename, level, prompt in samples:
        target = SAMPLES_DIR / filename
        if live_images and api_key:
            try:
                _call_meta_image_api(prompt, target, api_key)
                generated.append(target)
                continue
            except Exception as e:
                logger.warning(f"Meta Image API failed ({e}), falling back to high-res procedural engine")

        out_path, _ = generate_procedural_inspection_image(filename, level)
        generated.append(out_path)

    return generated


# ─────────────────────────────────────────────────────────────────────────────
# 4. Generate backend/data/sample_inspector_voice.wav
# ─────────────────────────────────────────────────────────────────────────────

def _generate_synthetic_wave(target_path: Path, text: str):
    """Fallback 16-bit PCM wave synthesizer using formant frequency synthesis."""
    sample_rate = 16000
    duration_s = 4.8
    n_samples = int(sample_rate * duration_s)

    # Formant frequencies simulating vocal tract speech rhythm
    words = text.split()
    word_duration = n_samples // len(words)

    with wave.open(str(target_path), "wb") as wf:
        wf.setnchannels(1)        # Mono
        wf.setsampwidth(2)        # 16-bit
        wf.setframerate(sample_rate)

        raw_bytes = bytearray()
        for idx in range(n_samples):
            w_idx = min(idx // word_duration, len(words) - 1)
            f0 = 135.0 + 25.0 * math.sin(w_idx * 1.3)
            # Formants F1, F2
            sample_val = (
                0.45 * math.sin(2.0 * math.pi * f0 * (idx / sample_rate)) +
                0.30 * math.sin(2.0 * math.pi * (f0 * 3.2) * (idx / sample_rate)) +
                0.15 * math.sin(2.0 * math.pi * (f0 * 5.8) * (idx / sample_rate))
            )
            # Envelope window per word
            local_t = (idx % word_duration) / word_duration
            envelope = math.sin(local_t * math.pi) ** 1.5
            int_val = int(sample_val * envelope * 24000)
            raw_bytes.extend(struct.pack("<h", max(-32767, min(32767, int_val))))

        wf.writeframes(raw_bytes)
    logger.info(f"Generated synthetic fallback wave: {target_path}")


def generate_inspector_voice_note() -> Path:
    target = DATA_DIR / "sample_inspector_voice.wav"
    transcript = (
        "Batch 408 inspected at dock 4. Severe moisture clumping and dark discoloration "
        "across roughly fourteen percent of the tray. Recommend immediate SLA penalty and upside price hedge."
    )

    # Method 1: Try pyttsx3
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 165)
        engine.setProperty("volume", 0.95)
        engine.save_to_file(transcript, str(target))
        engine.runAndWait()
        if target.exists() and target.stat().st_size > 1000:
            logger.info(f"Generated voice note via pyttsx3: {target} ({target.stat().st_size:,} bytes)")
            return target
    except Exception as e:
        logger.warning(f"pyttsx3 generation error ({e}), trying gTTS / fallback")

    # Method 2: Try gTTS
    try:
        from gtts import gTTS
        tts = gTTS(text=transcript, lang="en")
        tts.save(str(target))
        if target.exists() and target.stat().st_size > 1000:
            logger.info(f"Generated voice note via gTTS: {target}")
            return target
    except Exception:
        pass

    # Method 3: Procedural wave synthesis fallback
    _generate_synthetic_wave(target, transcript)
    return target


# ─────────────────────────────────────────────────────────────────────────────
# Main Runner & Verification
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate TerraQuant demo inputs")
    parser.add_argument("--live-images", action="store_true", help="Call live Meta Image API (muse-image-1.0)")
    args = parser.parse_args()

    logger.info("=== Starting TerraQuant Demo Assets Generator ===")

    # 1. SLA contract
    sla_file = generate_supplier_sla()

    # 2. Historical prices
    prices_file = generate_historical_prices()

    # 3. Sample images
    sample_files = generate_all_samples(live_images=args.live_images)

    # 4. Voice note
    voice_file = generate_inspector_voice_note()

    # 5. Summary Verification
    logger.info("=== Verifying All Generated Assets ===")
    all_files = [sla_file, prices_file, voice_file] + sample_files
    all_ok = True

    print("\n" + "=" * 70)
    print(" TERRAQUANT ASSET GENERATION & INTEGRITY VERIFICATION")
    print("=" * 70)
    for f in all_files:
        exists = f.exists()
        size = f.stat().st_size if exists else 0
        status = "PASSED" if exists and size > 0 else "FAILED"
        if status == "FAILED":
            all_ok = False
        print(f"[{status:^6}] {str(f.relative_to(ROOT_DIR)):<48} ({size:>9,} bytes)")
    print("=" * 70)

    if all_ok:
        print("ALL REQUIRED ASSETS SUCCESSFULLY GENERATED AND VERIFIED!")
    else:
        print("ERROR: Some assets failed generation!")
        sys.exit(1)


if __name__ == "__main__":
    main()
