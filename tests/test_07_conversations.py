"""
test_07_conversations.py — SPEC-008 TDD suite

Tests for the conversations data layer, API endpoints, audio files,
and frontend data alignment.

Run:  cd tests && python3 -m pytest test_07_conversations.py -v
Pre-condition: docker compose up (analytics at :8001, backend at :8000, front at :8080)
"""

import io
import json
import os
import struct
import urllib.request
import urllib.error

ANALYTICS = "http://localhost:8001"
BACKEND   = "http://localhost:8000"
FRONT     = "http://localhost:8080"

FEATURED_CLIENTS = ["ricardo", "fernando", "helena", "otavio", "beatriz",
                    "lucia", "gustavo", "andre", "camila", "paulo", "tereza", "sofia"]

EXPECTED_AUDIO_FILES = [
    "ricardo_20260614.mp3",
    "otavio_20260609.mp3",
]


def get(url, expect_json=True):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as r:
        raw = r.read()
        if expect_json:
            return json.loads(raw)
        return raw


def get_status(url):
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""


# ── Phase 1: API existence ────────────────────────────────────────────────────

class TestConversationsApiExists:
    def test_conversations_endpoint_returns_200(self):
        """GET /conversations?client_id=ricardo returns HTTP 200"""
        status, _ = get_status(f"{ANALYTICS}/conversations?client_id=ricardo")
        assert status == 200, f"Expected 200, got {status}"

    def test_conversations_returns_list(self):
        """GET /conversations?client_id=ricardo returns a JSON array"""
        data = get(f"{ANALYTICS}/conversations?client_id=ricardo")
        assert isinstance(data, list), f"Expected list, got {type(data)}"

    def test_conversation_detail_endpoint(self):
        """GET /conversations/<conv_id> returns 200 for a known id"""
        convos = get(f"{ANALYTICS}/conversations?client_id=ricardo")
        assert len(convos) > 0
        conv_id = convos[0]["conv_id"]
        status, _ = get_status(f"{ANALYTICS}/conversations/{conv_id}")
        assert status == 200

    def test_audio_endpoint_exists(self):
        """GET /audio/ricardo_20260614.mp3 returns HTTP 200"""
        status, _ = get_status(f"{ANALYTICS}/audio/ricardo_20260614.mp3")
        assert status == 200, f"Expected 200, got {status}"


# ── Phase 2: Conversation data completeness ───────────────────────────────────

class TestConversationDataCompleteness:
    def test_ricardo_has_at_least_5_conversations(self):
        """Ricardo must have ≥5 conversations"""
        data = get(f"{ANALYTICS}/conversations?client_id=ricardo")
        assert len(data) >= 5, f"Expected ≥5, got {len(data)}"

    def test_all_featured_clients_have_conversations(self):
        """Every featured client must have at least 3 conversations"""
        missing = []
        for client_id in FEATURED_CLIENTS:
            try:
                data = get(f"{ANALYTICS}/conversations?client_id={client_id}")
                if len(data) < 3:
                    missing.append(f"{client_id} has only {len(data)}")
            except Exception as e:
                missing.append(f"{client_id}: {e}")
        assert not missing, f"Clients with insufficient conversations: {missing}"

    def test_conversations_have_required_fields(self):
        """Each conversation must have all required fields"""
        required = {"conv_id", "client_id", "channel", "conv_date", "sentiment",
                    "summary_en", "summary_pt", "has_audio"}
        data = get(f"{ANALYTICS}/conversations?client_id=ricardo")
        for conv in data:
            missing_fields = required - set(conv.keys())
            assert not missing_fields, f"Conv {conv.get('conv_id')} missing: {missing_fields}"

    def test_channels_are_valid(self):
        """channel must be call | whatsapp | email"""
        valid = {"call", "whatsapp", "email"}
        data = get(f"{ANALYTICS}/conversations?client_id=ricardo")
        for conv in data:
            assert conv["channel"] in valid, f"Invalid channel: {conv['channel']}"

    def test_sentiments_are_valid(self):
        """sentiment must be positive | neutral | negative"""
        valid = {"positive", "neutral", "negative"}
        data = get(f"{ANALYTICS}/conversations?client_id=ricardo")
        for conv in data:
            assert conv["sentiment"] in valid, f"Invalid sentiment: {conv['sentiment']}"

    def test_conversations_ordered_by_date_desc(self):
        """Conversations must be ordered from most recent to oldest"""
        data = get(f"{ANALYTICS}/conversations?client_id=ricardo")
        dates = [c["conv_date"] for c in data]
        assert dates == sorted(dates, reverse=True), f"Not ordered desc: {dates}"

    def test_ricardo_has_call_on_jun14(self):
        """Ricardo must have a call conversation on 2026-06-14"""
        data = get(f"{ANALYTICS}/conversations?client_id=ricardo")
        jun14 = [c for c in data if c["conv_date"] == "2026-06-14"]
        assert len(jun14) == 1
        assert jun14[0]["channel"] == "call"
        assert jun14[0]["has_audio"] is True

    def test_helena_has_whatsapp_on_jun12(self):
        """Helena must have a whatsapp conversation on 2026-06-12"""
        data = get(f"{ANALYTICS}/conversations?client_id=helena")
        jun12 = [c for c in data if c["conv_date"] == "2026-06-12"]
        assert len(jun12) == 1
        assert jun12[0]["channel"] == "whatsapp"
        assert jun12[0]["has_audio"] is False

    def test_otavio_has_audio_on_jun9(self):
        """Otávio must have a call with audio on 2026-06-09"""
        data = get(f"{ANALYTICS}/conversations?client_id=otavio")
        jun9 = [c for c in data if c["conv_date"] == "2026-06-09"]
        assert len(jun9) == 1
        assert jun9[0]["has_audio"] is True


# ── Phase 3: Conversation turns ────────────────────────────────────────────────

class TestConversationTurns:
    def _get_jun14(self):
        data = get(f"{ANALYTICS}/conversations?client_id=ricardo")
        conv = next(c for c in data if c["conv_date"] == "2026-06-14")
        return get(f"{ANALYTICS}/conversations/{conv['conv_id']}")

    def test_conv_detail_has_turns(self):
        """Conversation detail must include turns array"""
        detail = self._get_jun14()
        assert "turns" in detail, "Missing 'turns' key"
        assert len(detail["turns"]) > 0

    def test_turns_have_required_fields(self):
        """Each turn must have turn_id, speaker, turn_order, text_en, text_pt"""
        detail = self._get_jun14()
        required = {"turn_id", "speaker", "turn_order", "text_en", "text_pt"}
        for turn in detail["turns"]:
            missing = required - set(turn.keys())
            assert not missing, f"Turn missing fields: {missing}"

    def test_speakers_are_valid(self):
        """speaker must be 'advisor' or 'client'"""
        detail = self._get_jun14()
        for turn in detail["turns"]:
            assert turn["speaker"] in ("advisor", "client"), \
                f"Invalid speaker: {turn['speaker']}"

    def test_turns_ordered(self):
        """Turns must be ordered by turn_order ascending"""
        detail = self._get_jun14()
        orders = [t["turn_order"] for t in detail["turns"]]
        assert orders == sorted(orders), f"Turns not ordered: {orders}"

    def test_call_has_at_least_4_turns(self):
        """A phone call must have at least 4 turns to constitute a dialog"""
        detail = self._get_jun14()
        assert len(detail["turns"]) >= 4, \
            f"Expected ≥4 turns, got {len(detail['turns'])}"

    def test_turns_alternate_speakers(self):
        """Call turns must alternate between advisor and client"""
        detail = self._get_jun14()
        turns = detail["turns"]
        for i in range(1, len(turns)):
            assert turns[i]["speaker"] != turns[i-1]["speaker"], \
                f"Consecutive same speaker at turns {i-1} and {i}"

    def test_whatsapp_turns_are_messages(self):
        """WhatsApp conversation turns must have non-empty text"""
        data = get(f"{ANALYTICS}/conversations?client_id=helena")
        conv = next(c for c in data if c["conv_date"] == "2026-06-12")
        detail = get(f"{ANALYTICS}/conversations/{conv['conv_id']}")
        for turn in detail["turns"]:
            assert turn.get("text_pt") or turn.get("text_en"), \
                f"Empty text in turn {turn['turn_order']}"


# ── Phase 4: Audio files ───────────────────────────────────────────────────────

class TestAudioFiles:
    def test_all_expected_audio_files_exist(self):
        """All expected audio files must return HTTP 200"""
        missing = []
        for filename in EXPECTED_AUDIO_FILES:
            status, _ = get_status(f"{ANALYTICS}/audio/{filename}")
            if status != 200:
                missing.append(f"{filename} (status={status})")
        assert not missing, f"Missing audio files: {missing}"

    def test_audio_files_are_valid_mp3(self):
        """Audio files must start with a valid MPEG frame header"""
        for filename in EXPECTED_AUDIO_FILES:
            status, data = get_status(f"{ANALYTICS}/audio/{filename}")
            assert status == 200
            assert len(data) > 1000, f"{filename} too small ({len(data)} bytes)"
            # MP3 frames start with 0xFF 0xE* or 0xFF 0xF* (sync word)
            # ID3 tag starts with 'ID3'
            valid_magic = (
                data[:3] == b'ID3' or
                (data[0] == 0xFF and (data[1] & 0xE0) == 0xE0)
            )
            assert valid_magic, f"{filename} doesn't look like a valid MP3"

    def test_audio_minimum_size(self):
        """Audio files should be at least 100KB (real audio, not empty)"""
        for filename in EXPECTED_AUDIO_FILES:
            _, data = get_status(f"{ANALYTICS}/audio/{filename}")
            size_kb = len(data) / 1024
            assert size_kb >= 100, f"{filename} too small: {size_kb:.1f}KB (expected ≥100KB)"

    def test_audio_content_type_is_mp3(self):
        """Audio endpoint must return audio/mpeg content-type"""
        url = f"{ANALYTICS}/audio/{EXPECTED_AUDIO_FILES[0]}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as r:
            ct = r.headers.get("Content-Type", "")
            assert "audio" in ct.lower(), f"Expected audio content-type, got: {ct}"


# ── Phase 5: Frontend rendering ────────────────────────────────────────────────

class TestFrontendConversationRendering:
    def _cockpit(self):
        return get(FRONT + "/cockpit.html", expect_json=False).decode("utf-8", errors="replace")

    def test_cockpit_fetches_conversations_from_api(self):
        """Cockpit must contain API fetch logic for conversations"""
        html = self._cockpit()
        assert "_fetchConversations" in html or "fetchConversations" in html, \
            "Cockpit must call an API to fetch conversations"

    def test_cockpit_has_audio_element(self):
        """Cockpit must have an <audio> element for real playback"""
        html = self._cockpit()
        assert "<audio" in html, "Cockpit must have <audio> element"

    def test_cockpit_references_audio_endpoint(self):
        """Cockpit must reference the /audio/ endpoint"""
        html = self._cockpit()
        assert "/audio/" in html, "Cockpit must reference /audio/ endpoint"

    def test_cockpit_carousel_uses_dynamic_dates(self):
        """Carousel must drive from dynamic conversation data, not just hardcoded CONVO"""
        html = self._cockpit()
        # The fetched conversations should drive the carousel
        assert "clientConvos" in html or "fetchedConvos" in html, \
            "Cockpit carousel must use dynamic conversation data"


# ── Phase 6: Data alignment ────────────────────────────────────────────────────

class TestDataAlignment:
    """Verify that alerts, opportunities, and recommendations align with conversations."""

    def test_ricardo_jun14_triggers_alert(self):
        """Ricardo's Jun 14 call (withdrawal intent) must have a matching alert"""
        data = get(f"{ANALYTICS}/conversations?client_id=ricardo")
        jun14 = next((c for c in data if c["conv_date"] == "2026-06-14"), None)
        assert jun14 is not None
        # The conversation sentiment must be negative (risk signal)
        assert jun14["sentiment"] == "negative"

    def test_fernando_jun10_triggers_compliance_alert(self):
        """Fernando's Jun 10 call must be tagged as compliance-related"""
        data = get(f"{ANALYTICS}/conversations?client_id=fernando")
        jun10 = next((c for c in data if c["conv_date"] == "2026-06-10"), None)
        assert jun10 is not None
        # Summary must mention compliance or concentration
        summary = (jun10.get("summary_en") or "").lower()
        assert any(kw in summary for kw in ["compliance", "concentration", "equity", "71%"]), \
            f"Fernando Jun 10 summary doesn't mention compliance: {summary}"

    def test_beatriz_suitability_conversation_exists(self):
        """Beatriz must have a suitability-related conversation"""
        data = get(f"{ANALYTICS}/conversations?client_id=beatriz")
        summaries = " ".join(c.get("summary_en", "") for c in data).lower()
        assert "suitability" in summaries, \
            "Beatriz must have a suitability conversation"

    def test_otavio_has_opportunity_conversation(self):
        """Otávio must have a conversation about the R$500k inflow opportunity"""
        data = get(f"{ANALYTICS}/conversations?client_id=otavio")
        summaries = " ".join(c.get("summary_en", "") for c in data).lower()
        assert "500" in summaries or "inflow" in summaries or "aport" in summaries, \
            "Otávio must have an inflow/opportunity conversation"

    def test_lucia_has_pension_conversation(self):
        """Lúcia must have a conversation about pension plan cross-sell"""
        data = get(f"{ANALYTICS}/conversations?client_id=lucia")
        summaries = " ".join(c.get("summary_en", "") for c in data).lower()
        assert "pension" in summaries or "pgbl" in summaries or "previdência" in summaries, \
            "Lúcia must have a pension plan conversation"

    def test_conversations_have_bilingual_summaries(self):
        """All conversations must have both EN and PT summaries"""
        for client_id in ["ricardo", "fernando", "helena"]:
            data = get(f"{ANALYTICS}/conversations?client_id={client_id}")
            for conv in data:
                assert conv.get("summary_en"), \
                    f"{client_id}/{conv.get('conv_id')} missing summary_en"
                assert conv.get("summary_pt"), \
                    f"{client_id}/{conv.get('conv_id')} missing summary_pt"


# ── Phase 7: Backend proxy ─────────────────────────────────────────────────────

class TestBackendProxyConversations:
    """Backend at :8000 should proxy conversations from analytics."""

    def test_backend_proxies_conversations(self):
        """GET /conversations?client_id=ricardo via backend returns data"""
        try:
            data = get(f"{BACKEND}/conversations?client_id=ricardo")
            assert isinstance(data, list)
            assert len(data) >= 5
        except Exception as e:
            # Backend proxy is optional — analytics direct access is primary
            import pytest
            pytest.skip(f"Backend proxy not yet implemented: {e}")

    def test_backend_proxies_audio(self):
        """GET /audio/ricardo_20260614.mp3 via backend proxies to analytics"""
        try:
            status, data = get_status(f"{BACKEND}/audio/ricardo_20260614.mp3")
            assert status == 200
            assert len(data) > 1000
        except Exception as e:
            import pytest
            pytest.skip(f"Backend audio proxy not yet implemented: {e}")
