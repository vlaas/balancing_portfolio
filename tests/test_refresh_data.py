"""DATA_REFRESH_SPEC — the no-overwrite merge of a tview batch into live data/.

Every test builds a throwaway tview folder and a throwaway live root under
tmp_path; nothing here reads or writes the repo's data/.
"""

from pathlib import Path

import pytest

from refresh_data import HEADER, LN_C_SPREAD_MAX, main

DATES = ["2026-10-12", "2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16"]
# After every close of 2026-10-16 (US 16:15 ET = 20:15 UTC), before FX's 22:00 UTC.
AFTER_CLOSE = "2026-10-16T21:00:00Z"


def lines(dates: list[str], closes: list[float]) -> list[str]:
    return [f"{d},{c!r},{c!r},{c!r},{c!r},100.0" for d, c in zip(dates, closes)]


def write(path: Path, rows: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([HEADER, *rows]) + "\n")


def tview(root: Path, listed: list[str], ndiv: list[str], started: str = AFTER_CLOSE) -> Path:
    tv = root / "tview"
    tv.mkdir()
    (tv / "list").write_text("\n".join(listed) + "\n")
    (tv / "ndiv").write_text("\n".join(ndiv) + "\n")
    (tv / "started").write_text(started + "\n")
    return tv


PRICE = [10.0, 11.0, 12.0, 13.0, 14.0]
R = [0.5, 0.5, 1.0, 1.0, 1.0]  # one ex-date, 2026-10-14
ADJUSTED = [p * r for p, r in zip(PRICE, R)]


@pytest.fixture
def batch(tmp_path):
    """A paired AMEX:QQQ (data/ through 10-15, batch through 10-16) and an
    index SP:SPX, both clean."""
    tv = tview(tmp_path, ["AMEX:QQQ", "SP:SPX"], ["SP:SPX"])
    data = tmp_path / "data"
    write(data / "adjusted" / "QQQ.csv", lines(DATES[:4], ADJUSTED[:4]))
    write(data / "unadjusted" / "QQQ.csv", lines(DATES[:4], PRICE[:4]))
    write(data / "index" / "SPX.csv", lines(DATES[:4], PRICE[:4]))
    write(tv / "csv" / "dividends" / "QQQ.csv", lines(DATES, ADJUSTED))
    write(tv / "csv" / "price" / "QQQ.csv", lines(DATES, PRICE))
    write(tv / "csv" / "price" / "SPX.csv", lines(DATES, PRICE))
    return tv, data


def run(tv: Path, data: Path, *extra: str) -> int:
    return main([str(tv), "--data", str(data), *extra])


def text(path: Path) -> str:
    return path.read_text()


def test_a_clean_batch_appends_and_a_dry_run_writes_nothing(batch, capsys):
    tv, data = batch
    before = text(data / "adjusted" / "QQQ.csv")
    assert run(tv, data) == 0
    assert "Dry run" in capsys.readouterr().out
    assert text(data / "adjusted" / "QQQ.csv") == before

    assert run(tv, data, "--write") == 0
    for folder, source in (("adjusted", "dividends"), ("unadjusted", "price")):
        assert text(data / folder / "QQQ.csv") == text(tv / "csv" / source / "QQQ.csv")
    assert text(data / "index" / "SPX.csv") == text(tv / "csv" / "price" / "SPX.csv")


def test_a_new_ex_date_rescales_the_overlap_and_is_not_a_revision(batch):
    tv, data = batch
    # An ex-date on the appended bar rescales every earlier adjusted close by k.
    k = 0.98
    rescaled = [a * k for a in ADJUSTED[:4]] + [PRICE[4]]
    write(tv / "csv" / "dividends" / "QQQ.csv", lines(DATES, rescaled))
    assert run(tv, data, "--write") == 0
    assert text(data / "adjusted" / "QQQ.csv") == text(tv / "csv" / "dividends" / "QQQ.csv")


def test_index_rows_before_the_new_first_bar_are_kept_verbatim(batch):
    tv, data = batch
    old = text(data / "index" / "SPX.csv").splitlines()
    write(tv / "csv" / "price" / "SPX.csv", lines(DATES[2:], PRICE[2:]))
    assert run(tv, data, "--write") == 0
    merged = text(data / "index" / "SPX.csv").splitlines()
    assert merged == old[:3] + lines(DATES[2:], PRICE[2:])


def test_adjusted_rows_before_the_new_first_bar_are_rescaled(batch):
    tv, data = batch
    k = 0.98
    write(tv / "csv" / "dividends" / "QQQ.csv", lines(DATES[1:], [a * k for a in ADJUSTED[1:4]] + [PRICE[4]]))
    write(tv / "csv" / "price" / "QQQ.csv", lines(DATES[1:], PRICE[1:]))
    assert run(tv, data, "--write") == 0
    adjusted = text(data / "adjusted" / "QQQ.csv").splitlines()
    unadjusted = text(data / "unadjusted" / "QQQ.csv").splitlines()
    assert unadjusted[1] == lines(DATES[:1], PRICE[:1])[0]
    close = float(adjusted[1].split(",")[4])
    assert close == pytest.approx(ADJUSTED[0] * k, rel=1e-15)
    assert adjusted[1].endswith(",100.0")
    assert adjusted[2:] == text(tv / "csv" / "dividends" / "QQQ.csv").splitlines()[1:]


def test_rows_before_the_first_bar_of_data_are_taken_only_when_accepted(batch, capsys):
    tv, data = batch
    old = text(data / "index" / "SPX.csv")
    write(data / "index" / "SPX.csv", lines(DATES[1:4], PRICE[1:4]))
    assert run(tv, data, "--write") == 0
    assert "skipped 1 rows before data/'s first bar 2026-10-13 (--accept SPX takes them)" in capsys.readouterr().out
    assert text(data / "index" / "SPX.csv").splitlines()[1:] == lines(DATES[1:], PRICE[1:])

    assert run(tv, data, "--write", "--accept", "SPX") == 0
    assert "took 1 rows before data/'s first bar 2026-10-13" in capsys.readouterr().out
    assert text(data / "index" / "SPX.csv") == text(tv / "csv" / "price" / "SPX.csv")
    assert old != text(data / "index" / "SPX.csv")


def test_an_unclosed_bar_is_trimmed_from_every_pass(batch, capsys):
    tv, data = batch
    (tv / "started").write_text("2026-10-16T18:00:00Z\n")  # 14:00 ET
    assert run(tv, data, "--write") == 0
    assert "trimmed unclosed ['2026-10-16']" in capsys.readouterr().out
    for folder in ("adjusted", "unadjusted", "index"):
        symbol = "SPX" if folder == "index" else "QQQ"
        assert text(data / folder / f"{symbol}.csv").splitlines()[-1].startswith("2026-10-15")


@pytest.mark.parametrize("started,kept", [("2026-10-16T21:59:59Z", False), ("2026-10-16T22:00:00Z", True)])
def test_an_fx_bar_is_final_at_22_utc_the_day_after_its_label(tmp_path, started, kept):
    tv = tview(tmp_path, ["FX_IDC:EURUSD"], ["FX_IDC:EURUSD"], started)
    data = tmp_path / "data"
    write(data / "index" / "EURUSD.csv", lines(DATES[:3], PRICE[:3]))
    write(tv / "csv" / "price" / "EURUSD.csv", lines(DATES[:4], PRICE[:4]))
    assert run(tv, data, "--write") == 0
    last = text(data / "index" / "EURUSD.csv").splitlines()[-1]
    assert last.startswith(DATES[3] if kept else DATES[2])


def test_a_calendar_change_inside_the_old_range_stops_until_accepted(batch, capsys):
    tv, data = batch
    dates = DATES[:2] + DATES[3:]  # 10-14 removed
    write(tv / "csv" / "price" / "SPX.csv", lines(dates, PRICE[:2] + PRICE[3:]))
    before = text(data / "index" / "SPX.csv")
    assert run(tv, data, "--write") == 1
    out = capsys.readouterr().out
    assert "calendar +[] -['2026-10-14']" in out and "Refused" in out
    assert text(data / "index" / "SPX.csv") == before

    assert run(tv, data, "--write", "--accept", "SPX") == 0
    assert "accepted" in capsys.readouterr().out
    assert text(data / "index" / "SPX.csv") == text(tv / "csv" / "price" / "SPX.csv")


def test_a_revised_close_stops(batch, capsys):
    tv, data = batch
    write(tv / "csv" / "price" / "SPX.csv", lines(DATES, PRICE[:3] + [13.00001, PRICE[4]]))
    assert run(tv, data) == 1
    assert "index: close changed on 1 dates (2026-10-15 last)" in capsys.readouterr().out


def test_a_non_constant_adjusted_ratio_stops(batch, capsys):
    tv, data = batch
    # A revised dividend moves the ratio on the rows before its ex-date only.
    revised = [ADJUSTED[0] * 0.999, ADJUSTED[1] * 0.999] + ADJUSTED[2:]
    write(tv / "csv" / "dividends" / "QQQ.csv", lines(DATES, revised))
    assert run(tv, data) == 1
    assert "ratio not constant" in capsys.readouterr().out


def test_ratio_noise_below_the_ceiling_is_not_a_revision(batch):
    tv, data = batch
    noisy = [a * (1 + (LN_C_SPREAD_MAX / 4) * (i % 2)) for i, a in enumerate(ADJUSTED[:4])] + [PRICE[4]]
    write(tv / "csv" / "dividends" / "QQQ.csv", lines(DATES, noisy))
    assert run(tv, data) == 0


def test_passes_that_disagree_stop_even_when_accepted(batch, capsys):
    tv, data = batch
    write(tv / "csv" / "price" / "QQQ.csv", lines(DATES[:4], PRICE[:4]))
    assert run(tv, data, "--accept", "QQQ") == 1
    out = capsys.readouterr().out
    assert "the two passes' calendars differ" in out
    assert "--accept QQQ: nothing to accept" in out

    write(tv / "csv" / "price" / "QQQ.csv", lines(DATES, PRICE[:4] + [14.01]))
    assert run(tv, data) == 1
    assert "the two passes' last closes differ" in capsys.readouterr().out


def test_a_batch_ending_before_data_stops(batch, capsys):
    tv, data = batch
    write(tv / "csv" / "price" / "SPX.csv", lines(DATES[:3], PRICE[:3]))
    assert run(tv, data) == 1
    assert "batch ends 2026-10-14, before data/'s 2026-10-15" in capsys.readouterr().out


def test_a_missing_file_stops(batch, capsys):
    tv, data = batch
    (tv / "csv" / "dividends" / "QQQ.csv").unlink()
    assert run(tv, data) == 1
    assert "adjusted: no csv/dividends/QQQ.csv" in capsys.readouterr().out


def test_the_batch_and_data_must_hold_the_same_symbols(batch, capsys):
    tv, data = batch
    (tv / "list").write_text("AMEX:QQQ\nAMEX:NEW\n")
    write(tv / "csv" / "price" / "NEW.csv", lines(DATES, PRICE))
    assert run(tv, data) == 1
    out = capsys.readouterr().out
    assert "NEW" in out and "not in data/" in out
    assert "SPX: in data/ but not in the batch's list" in out


def test_a_refused_run_writes_nothing_even_with_write(batch):
    tv, data = batch
    write(tv / "csv" / "price" / "SPX.csv", lines(DATES, PRICE[:3] + [13.5, PRICE[4]]))
    before = {p: text(p) for p in data.rglob("*.csv")}
    assert run(tv, data, "--write") == 1
    assert {p: text(p) for p in data.rglob("*.csv")} == before


def test_a_single_pass_pair_writes_two_identical_files(tmp_path):
    tv = tview(tmp_path, ["AMEX:GLD"], ["AMEX:GLD"])
    data = tmp_path / "data"
    for folder in ("adjusted", "unadjusted"):
        write(data / folder / "GLD.csv", lines(DATES[:4], PRICE[:4]))
    write(tv / "csv" / "price" / "GLD.csv", lines(DATES, PRICE))
    assert run(tv, data, "--write") == 0
    assert text(data / "adjusted" / "GLD.csv") == text(data / "unadjusted" / "GLD.csv")
    assert text(data / "adjusted" / "GLD.csv") == text(tv / "csv" / "price" / "GLD.csv")
