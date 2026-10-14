#!/usr/bin/env python3
"""Replace only Codex [projects.*] blocks, preserving CC Switch-managed config."""
from __future__ import annotations
import argparse, datetime, os, re, shutil, tempfile
from pathlib import Path

PROJECT_RE = re.compile(r"(?m)^\[projects\.[^\n]+\]\n")
HEADER_RE = re.compile(r"(?m)^\[")

def blocks(text: str):
    starts = [m.start() for m in HEADER_RE.finditer(text)]
    if not starts:
        return [(0, len(text), text)]
    out=[]
    if starts[0] > 0: out.append((0, starts[0], text[:starts[0]]))
    for i,start in enumerate(starts):
        end = starts[i+1] if i+1 < len(starts) else len(text)
        out.append((start,end,text[start:end]))
    return out

def is_project(block: str) -> bool:
    return bool(re.match(r"\[projects\.[^\n]+\]", block))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--config', default=str(Path.home()/'.codex/config.toml'))
    ap.add_argument('--projects', default=str(Path.home()/'.codex/projects.local.toml'))
    ap.add_argument('--write', action='store_true')
    args=ap.parse_args()
    config=Path(args.config); projects=Path(args.projects)
    old=config.read_text() if config.exists() else ''
    new_projects=projects.read_text() if projects.exists() else ''
    kept=[part for _,_,part in blocks(old) if not is_project(part)]
    candidate=''.join(kept).rstrip()+'\n'
    if new_projects.strip(): candidate += '\n'+new_projects.strip()+'\n'
    if not args.write:
        print({'config':str(config),'project_blocks':len(re.findall(r'(?m)^\[projects\.',new_projects)),'changed':candidate!=old})
        return
    backup=config.parent/'backups'/('projects-'+datetime.datetime.now().strftime('%Y%m%dT%H%M%S'))
    backup.mkdir(parents=True, exist_ok=True)
    if config.exists(): shutil.copy2(config, backup/'config.toml')
    fd,tmp=tempfile.mkstemp(dir=config.parent)
    os.fchmod(fd,0o600)
    with os.fdopen(fd,'w') as f: f.write(candidate)
    os.replace(tmp,config)
    print({'backup':str(backup),'project_blocks':len(re.findall(r'(?m)^\[projects\.',new_projects))})

if __name__ == '__main__': main()
