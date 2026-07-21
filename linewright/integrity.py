"""File-inventory capture + verification (Part 4).

SHA-256 is authoritative; size and mtime are supporting signals only.
"""
import hashlib
import json
import os
import subprocess


def hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def capture_inventory(root):
    """Inventory every file under `root`: relpath -> {size, sha256, mtime, symlink}."""
    root = os.path.abspath(root)
    files = {}
    for dirpath, _dirs, names in os.walk(root):
        for n in sorted(names):
            full = os.path.join(dirpath, n)
            rel = os.path.relpath(full, root).replace("\\", "/")
            entry = {"symlink": os.path.islink(full)}
            if entry["symlink"]:
                entry["target"] = os.readlink(full)
                entry["sha256"] = None
                entry["size"] = None
            else:
                st = os.stat(full)
                entry["size"] = st.st_size
                entry["sha256"] = hash_file(full)
                entry["mtime"] = int(st.st_mtime)
            files[rel] = entry
    return {"root": root, "file_count": len(files), "files": files,
            "root_hash": hash_directory(files)}


def hash_directory(files):
    """A single root hash over the {relpath: sha256/target} map (order-stable)."""
    h = hashlib.sha256()
    for rel in sorted(files):
        e = files[rel]
        marker = e.get("sha256") or ("symlink:" + str(e.get("target")))
        h.update((rel + "\0" + str(marker) + "\n").encode("utf-8"))
    return h.hexdigest()


def verify_inventory(before, after):
    """Compare two inventories. SHA-256 authoritative."""
    bf, af = before["files"], after["files"]
    changed, missing, new, symlink_changed, ts_only = [], [], [], [], []
    for rel, be in bf.items():
        if rel not in af:
            missing.append(rel)
            continue
        ae = af[rel]
        if be.get("symlink") or ae.get("symlink"):
            if be.get("target") != ae.get("target") or be.get("symlink") != ae.get("symlink"):
                symlink_changed.append(rel)
            continue
        if be["sha256"] != ae["sha256"]:
            changed.append(rel)               # bytes differ -> authoritative failure
        elif be.get("mtime") != ae.get("mtime"):
            ts_only.append(rel)               # timestamp only, bytes identical -> benign
    for rel in af:
        if rel not in bf:
            new.append(rel)
    ok = not (changed or missing or new or symlink_changed)
    return {
        "ok": ok,
        "changed_bytes": sorted(changed),
        "missing": sorted(missing),
        "new_files": sorted(new),
        "symlink_changed": sorted(symlink_changed),
        "timestamp_only_bytes_identical": sorted(ts_only),
        "root_hash_before": before["root_hash"],
        "root_hash_after": after["root_hash"],
    }


def _git(args, repo_root):
    return subprocess.run(["git", "-C", repo_root] + args, capture_output=True,
                          text=True).stdout.strip()


def capture_repository(repo_root, protected_globs=None):
    """Capture git HEAD/branch/status + hashes of protected tracked files."""
    import glob
    head = _git(["rev-parse", "HEAD"], repo_root)
    branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], repo_root)
    status = _git(["status", "--porcelain"], repo_root)
    tracked = [l for l in status.splitlines() if not l.startswith("??")]
    untracked = [l[3:] for l in status.splitlines() if l.startswith("??")]
    protected = {}
    for pattern in (protected_globs or []):
        for f in glob.glob(os.path.join(repo_root, pattern), recursive=True):
            if os.path.isfile(f):
                rel = os.path.relpath(f, repo_root).replace("\\", "/")
                if "__pycache__" in rel or rel.endswith(".pyc"):
                    continue                       # bytecode caches are not source
                protected[rel] = hash_file(f)
    return {"head": head, "branch": branch, "modified_tracked": tracked,
            "untracked": untracked, "protected_hashes": protected}


def verify_repository(before, after, authorized_prefixes):
    """Report unexpected modified tracked files / files outside authorized paths."""
    def authorized(path):
        return any(path.startswith(p) for p in authorized_prefixes)

    new_untracked = [u for u in after["untracked"] if u not in before["untracked"]]
    unexpected_new = [u for u in new_untracked if not authorized(u)]
    expected_new = [u for u in new_untracked if authorized(u)]
    prot_changed = [rel for rel, h in before["protected_hashes"].items()
                    if after["protected_hashes"].get(rel) != h]
    new_modified = [m for m in after["modified_tracked"] if m not in before["modified_tracked"]]
    unexpected_modified = [m for m in new_modified if not authorized(m[3:].strip())]
    ok = not (unexpected_new or prot_changed or unexpected_modified
              or after["head"] != before["head"])
    return {
        "ok": ok,
        "head_before": before["head"],
        "head_after": after["head"],
        "expected_new_files_in_run_paths": sorted(expected_new),
        "unexpected_new_files_outside_run_paths": sorted(unexpected_new),
        "protected_tracked_files_changed": sorted(prot_changed),
        "unexpected_modified_tracked": sorted(unexpected_modified),
    }


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
