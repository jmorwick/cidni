from click.testing import CliRunner

from cidni.__main__ import main


def test_cli_no_command_shows_error():
    runner = CliRunner()

    result = runner.invoke(main, [])

    assert result.exit_code == 1
    assert "Missing command" in result.output


def test_know_lists_and_recalls_file(tmp_path):
    runner = CliRunner()
    store_dir = tmp_path / "store"
    store_dir.mkdir()

    input_file = tmp_path / "hello.txt"
    input_file.write_text("hello", encoding="utf-8")

    result = runner.invoke(
        main,
        ["--dataservice", str(store_dir), "know", str(input_file)],
    )

    assert result.exit_code == 0
    assert str(input_file) in result.output
    assert "-->" in result.output

    cid = result.output.split("' --> '")[1].split("'")[0]

    result = runner.invoke(
        main,
        ["--dataservice", str(store_dir), "list"],
    )

    assert result.exit_code == 0
    assert cid in result.output

    result = runner.invoke(
        main,
        ["--dataservice", str(store_dir), "recall", cid],
    )

    assert result.exit_code == 0
    assert "hello" in result.output


def test_confirm_known_file(tmp_path):
    runner = CliRunner()
    store_dir = tmp_path / "store"
    store_dir.mkdir()

    input_file = tmp_path / "hello.txt"
    input_file.write_text("hello", encoding="utf-8")

    know_result = runner.invoke(
        main,
        ["--dataservice", str(store_dir), "know", str(input_file)],
    )

    cid = know_result.output.split("' --> '")[1].split("'")[0]

    result = runner.invoke(
        main,
        ["--dataservice", str(store_dir), "confirm", cid],
    )

    assert result.exit_code == 0
    assert "identity confirmed" in result.output


def test_know_same_file_twice_reports_already_stored(tmp_path):
    runner = CliRunner()
    store_dir = tmp_path / "store"
    store_dir.mkdir()

    input_file = tmp_path / "hello.txt"
    input_file.write_text("hello", encoding="utf-8")

    runner.invoke(main, ["--dataservice", str(store_dir), "know", str(input_file)])
    result = runner.invoke(main, ["--dataservice", str(store_dir), "know", str(input_file)])

    assert result.exit_code == 0
    assert "ALREADY STORED" in result.output


def test_list_by_had_path_uses_persisted_knowledge_service(tmp_path):
    runner = CliRunner()
    store_dir = tmp_path / "store"
    store_dir.mkdir()

    input_file = tmp_path / "hello.txt"
    input_file.write_text("hello", encoding="utf-8")

    know_result = runner.invoke(
        main,
        ["--dataservice", str(store_dir), "know", str(input_file)],
    )

    cid = know_result.output.split("' --> '")[1].split("'")[0]

    result = runner.invoke(
        main,
        ["--dataservice", str(store_dir), "list", "-p", f"had_path={input_file}"],
    )

    assert result.exit_code == 0
    assert cid in result.output
