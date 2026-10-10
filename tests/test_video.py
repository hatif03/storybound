import pytest

from storybound.video import claims, verify
from storybound.video.spec import Block, Claim, Scene, Spec


def _spec(narration="Plain words.", text="Hello", requires=False, src=""):
    blocks = [Block(type="text", text=text)] + ([Block(type="image", src=src)] if src else [])
    return Spec(
        title="t",
        claims=[Claim(id="c1", label="a label", refs=["report:sweep-2-p2#arms.B1.shipped"], fmt="{0}")],
        scenes=[Scene(id="s1", narration=narration, blocks=blocks, covers=[])],
        requires_coverage=requires,
    )


def test_typed_number_is_refused_but_a_claim_placeholder_is_fine():
    assert verify.claims_sourced(_spec(narration="We ran {c1} stories."))[0]["status"] == "pass"
    bad = verify.claims_sourced(_spec(text="We ran 28 stories"))
    assert bad[0]["status"] == "violation" and bad[0]["scene"] == "s1"


def test_tools_covered_needs_all_fifteen():
    assert verify.tools_covered(_spec())["status"] == "pass"  # not required
    v = verify.tools_covered(_spec(requires=True))
    assert v["status"] == "violation" and "neatlogs:architecture" in v["actual"]


def test_images_only_from_assets():
    assert verify.no_child_data(_spec(src="assets/brand/logo/a.png"))["status"] == "pass"
    assert verify.no_child_data(_spec(src="_private/demo-drawings/a.jpg"))["status"] == "violation"


def test_secret_like_text_is_refused():
    s = _spec(text="key sk-abcdefghijklmnopqrstuvwxyz123456")
    assert verify.no_secrets(s, {})["status"] == "violation"


def test_report_claims_rebuild_from_the_ledger():
    s = _spec()
    resolved = claims.resolve(s)
    assert resolved["c1"]["display"] == "28"
    assert resolved["c1"]["sources"][0]["file"].startswith("evidence/reports/")
    assert all(v["status"] == "pass" for v in verify.claims_match_ledger(resolved))


def test_claim_files_cannot_leave_the_repo():
    with pytest.raises(ValueError):
        claims.resolve_claim(Claim(id="x", label="x", refs=["file:_private/x.json#a"]))


def test_overclaiming_words_are_refused():
    assert verify.no_overclaims(_spec(text="a verifiable receipt"))[0]["status"] == "pass"
    assert verify.no_overclaims(_spec(text="cryptographic receipts"))[0]["status"] == "violation"
