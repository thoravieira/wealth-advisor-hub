"""
Baseline tests — current frontend state.

NOTE: The Docker container was built with the OLD filename (Cockpit B.dc.html).
      test_cockpit_html_loads will FAIL until the container is rebuilt.
      This is intentional — it documents what needs fixing.

Run:  pytest tests/test_02_frontend_current.py -v
"""
import httpx
import pytest

from conftest import FRONTEND_URL


class TestFrontendIndex:
    def test_index_returns_200(self, frontend):
        r = frontend.get("/")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"

    def test_index_is_html(self, frontend):
        r = frontend.get("/")
        ct = r.headers.get("content-type", "")
        assert "html" in ct, f"Expected HTML, got: {ct}"

    def test_index_redirects_to_cockpit(self, frontend):
        """index.html meta-refresh must point to cockpit.html.
        Note: meta http-equiv=refresh is browser-only; httpx doesn't follow it.
        We verify the HTML content references cockpit.html instead."""
        r = httpx.get(f"{FRONTEND_URL}/index.html", follow_redirects=False)
        assert "cockpit.html" in r.text, (
            f"index.html doesn't reference cockpit.html. Content: {r.text}"
        )

    def test_no_reference_to_old_filename(self, frontend):
        """index.html must not reference the old space-encoded filename."""
        r = httpx.get(f"{FRONTEND_URL}/index.html", follow_redirects=False)
        assert "Cockpit%20B" not in r.text, (
            "index.html still references old filename 'Cockpit%20B.dc.html'"
        )


class TestCockpitPage:
    def test_cockpit_html_loads(self, frontend):
        """cockpit.html must return 200. FAILS if container not rebuilt after rename."""
        r = frontend.get("/cockpit.html")
        assert r.status_code == 200, (
            f"cockpit.html returned {r.status_code}. "
            "Container likely needs rebuild: docker build -t 11labs-front ./front && "
            "docker run -d -p 8080:80 11labs-front"
        )

    def test_cockpit_contains_dc_template(self, frontend):
        r = frontend.get("/cockpit.html")
        assert r.status_code == 200
        assert "dc-app" in r.text or "DCLogic" in r.text, (
            "cockpit.html doesn't look like a dc template app"
        )

    def test_cockpit_contains_elevenlabs_sdk(self, frontend):
        r = frontend.get("/cockpit.html")
        assert r.status_code == 200
        assert "@11labs/client" in r.text or "ElevenLabs" in r.text or "elevenlabs" in r.text.lower(), (
            "cockpit.html doesn't reference the ElevenLabs SDK"
        )

    def test_cockpit_references_sofia(self, frontend):
        r = frontend.get("/cockpit.html")
        assert r.status_code == 200
        assert "Sofia" in r.text or "sofia" in r.text, (
            "cockpit.html doesn't mention Sofia"
        )

    def test_support_js_loads(self, frontend):
        """dc template runtime must be served."""
        r = frontend.get("/support.js")
        assert r.status_code == 200, f"support.js returned {r.status_code}"
        assert len(r.content) > 1000, "support.js is suspiciously small"


class TestOldFilenameGone:
    def test_old_cockpit_b_returns_404(self, frontend):
        """The old filename must NOT be served after rename."""
        r = httpx.get(
            f"{FRONTEND_URL}/Cockpit%20B.dc.html",
            follow_redirects=False,
        )
        assert r.status_code == 404, (
            f"Old filename 'Cockpit B.dc.html' still served (got {r.status_code}). "
            "Rebuild and redeploy the frontend container."
        )

    def test_assessor_file_not_served(self, frontend):
        """Cockpit Assessor.dc.html was deleted — must return 404."""
        r = httpx.get(
            f"{FRONTEND_URL}/Cockpit%20Assessor.dc.html",
            follow_redirects=False,
        )
        assert r.status_code == 404, (
            f"Deleted file 'Cockpit Assessor.dc.html' is still being served (got {r.status_code})"
        )
