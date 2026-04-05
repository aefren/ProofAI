import ast
import struct
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parent
ADDON_DIR = ROOT / "corrector"
DIST_DIR = ROOT / "dist"


def _parse_po_string(line):
	return ast.literal_eval(line)


def _read_po_messages(path):
	messages = {}
	msgid = None
	msgstr = None
	state = None
	fuzzy = False

	def finish_entry():
		nonlocal msgid, msgstr, state, fuzzy
		if msgid is not None and msgstr is not None and not fuzzy:
			messages[msgid] = msgstr
		msgid = None
		msgstr = None
		state = None
		fuzzy = False

	for raw_line in path.read_text(encoding="utf-8").splitlines():
		line = raw_line.strip()
		if not line:
			finish_entry()
			continue
		if line.startswith("#,"):
			fuzzy = "fuzzy" in line
			continue
		if line.startswith("#"):
			continue
		if line.startswith("msgid "):
			finish_entry()
			msgid = _parse_po_string(line[6:])
			state = "msgid"
			continue
		if line.startswith("msgstr "):
			msgstr = _parse_po_string(line[7:])
			state = "msgstr"
			continue
		if line.startswith('"'):
			if state == "msgid":
				msgid += _parse_po_string(line)
			elif state == "msgstr":
				msgstr += _parse_po_string(line)
			continue
	finish_entry()
	return messages


def _write_mo(messages, path):
	keys = sorted(messages)
	ids = b""
	strs = b""
	offsets = []
	for key in keys:
		key_bytes = key.encode("utf-8")
		value_bytes = messages[key].encode("utf-8")
		offsets.append((len(key_bytes), len(ids), len(value_bytes), len(strs)))
		ids += key_bytes + b"\0"
		strs += value_bytes + b"\0"

	keystart = 7 * 4
	orig_table_offset = keystart
	trans_table_offset = orig_table_offset + len(keys) * 8
	ids_offset = trans_table_offset + len(keys) * 8
	strs_offset = ids_offset + len(ids)

	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("wb") as mo_file:
		mo_file.write(struct.pack("<Iiiiiii", 0x950412DE, 0, len(keys), orig_table_offset, trans_table_offset, 0, 0))
		for key_length, key_offset, _value_length, _value_offset in offsets:
			mo_file.write(struct.pack("<II", key_length, ids_offset + key_offset))
		for _key_length, _key_offset, value_length, value_offset in offsets:
			mo_file.write(struct.pack("<II", value_length, strs_offset + value_offset))
		mo_file.write(ids)
		mo_file.write(strs)


def compile_translations():
	for po_path in ADDON_DIR.glob("locale/*/LC_MESSAGES/*.po"):
		mo_path = po_path.with_suffix(".mo")
		_write_mo(_read_po_messages(po_path), mo_path)


def read_manifest_value(name):
	for line in (ADDON_DIR / "manifest.ini").read_text(encoding="utf-8").splitlines():
		if line.startswith(f"{name} = "):
			return line.split("=", 1)[1].strip().strip('"')
	raise RuntimeError(f"Could not find {name} in manifest.ini")


def build():
	compile_translations()
	name = read_manifest_value("name")
	version = read_manifest_value("version")
	output = DIST_DIR / f"{name}-{version}.nvda-addon"
	DIST_DIR.mkdir(exist_ok=True)
	with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
		for path in ADDON_DIR.rglob("*"):
			if path.is_dir():
				continue
			if "__pycache__" in path.parts or path.suffix == ".pyc":
				continue
			archive.write(path, path.relative_to(ADDON_DIR))
	return output


if __name__ == "__main__":
	result = build()
	print(result)
