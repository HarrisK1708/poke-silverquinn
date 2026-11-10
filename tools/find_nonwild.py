#!/usr/bin/env python3
"""
Usage: python3 tools/find_nonwild.py [--include-rods]

List the 151 Pokémon species that never appear in any wild encounter table
(data/wild/maps/*.asm: grass, cave, and surfing tables), for Red, Blue, and
both versions combined.

Species come from constants/pokemon_constants.asm. Non-species ids in that file
(NO_MON, const_skip slots, FOSSIL_* and MON_GHOST sprites) are filtered out by
keeping only names that also have a DEX_<NAME> entry in
constants/pokedex_constants.asm, which also provides the Pokédex sort order.

By default, fishing is NOT counted (rod encounters live outside the per-map
tables). Pass --include-rods to also count:
  - Old Rod:   the `lb bc, <level>, <SPECIES>` in ItemUseOldRod
               (engine/items/item_effects.asm)
  - Good Rod:  GoodRodMons (data/wild/good_rod.asm)
  - Super Rod: SuperRodData map -> group tables (data/wild/super_rod.asm)
and to print file:line evidence for every species that only fishing makes
catchable.
"""

import argparse
import glob
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSIONS = ('RED', 'BLUE')
ANY_WATER = 'any fishable water'

CONST_RE = re.compile(r'^\s*const\s+([A-Z0-9_]+)')
DB_RE = re.compile(r'^\s*db\s+\d+\s*,\s*([A-Z0-9_]+)')
IF_RE = re.compile(r'^\s*IF\s+DEF\(_([A-Z]+)\)')
GLOBAL_LABEL_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)::?')
LOCAL_LABEL_RE = re.compile(r'^\s*(\.[A-Za-z0-9_]+):')
DBW_RE = re.compile(r'^\s*dbw\s+([A-Z0-9_]+)\s*,\s*(\.[A-Za-z0-9_]+)')
LB_BC_RE = re.compile(r'^\s*lb\s+bc\s*,\s*\d+\s*,\s*([A-Z0-9_]+)')


class Evidence:
	def __init__(self, filename, lineno, where):
		self.file = os.path.relpath(filename, ROOT)
		self.line = lineno
		self.where = where  # list of map/location names

	def __str__(self):
		return f'{self.file}:{self.line}  [{", ".join(self.where)}]'


def path(*parts):
	return os.path.join(ROOT, *parts)


def read_lines(filename):
	"""Yield (lineno, line) with comments stripped."""
	with open(filename, encoding='utf-8') as f:
		for lineno, line in enumerate(f, 1):
			yield lineno, line.split(';', 1)[0].rstrip()


def read_species():
	"""Return species names from pokemon_constants.asm, sorted by Pokédex number."""
	dex = [m.group(1)[len('DEX_'):]
		for _, line in read_lines(path('constants', 'pokedex_constants.asm'))
		if (m := CONST_RE.match(line)) and m.group(1).startswith('DEX_')]
	ids = {m.group(1)
		for _, line in read_lines(path('constants', 'pokemon_constants.asm'))
		if (m := CONST_RE.match(line))}
	species = [name for name in dex if name in ids]
	missing = [name for name in dex if name not in ids]
	if missing:
		sys.exit(f'error: DEX_ names without a pokemon constant: {missing}')
	if len(species) != 151:
		sys.exit(f'error: expected 151 species, found {len(species)}')
	return species


def scan(filename):
	"""
	Yield (lineno, line, versions, global_label, local_label) for every line,
	where versions is the set of versions in which that line is assembled.
	Handles IF DEF(_RED) / IF DEF(_BLUE) / ELSE / ENDC blocks.
	"""
	stack = []  # each entry: set of versions active inside that block
	glabel = llabel = None
	for lineno, line in read_lines(filename):
		stripped = line.strip()
		if m := IF_RE.match(line):
			stack.append({m.group(1)} & set(VERSIONS))
			continue
		if stripped.startswith('IF'):
			sys.exit(f'error: unsupported conditional in {filename}:{lineno}: {stripped}')
		if stripped == 'ELSE':
			stack[-1] = set(VERSIONS) - stack[-1]
			continue
		if stripped == 'ENDC':
			stack.pop()
			continue
		if m := GLOBAL_LABEL_RE.match(line):
			glabel, llabel = m.group(1), None
		elif m := LOCAL_LABEL_RE.match(line):
			llabel = m.group(1)
		active = set(VERSIONS)
		for block in stack:
			active &= block
		yield lineno, line, active, glabel, llabel
	if stack:
		sys.exit(f'error: unterminated IF block in {filename}')


def add(found, versions, species, evidence):
	for v in versions:
		found[v][species].append(evidence)


def collect_map_tables(found):
	files = sorted(glob.glob(path('data', 'wild', 'maps', '*.asm')))
	for filename in files:
		for lineno, line, versions, glabel, _ in scan(filename):
			if m := DB_RE.match(line):
				where = glabel.removesuffix('WildMons') if glabel else os.path.basename(filename)
				add(found, versions, m.group(1), Evidence(filename, lineno, [where]))
	return files


def collect_old_rod(found):
	filename = path('engine', 'items', 'item_effects.asm')
	hits = 0
	for lineno, line, versions, glabel, _ in scan(filename):
		if glabel == 'ItemUseOldRod' and (m := LB_BC_RE.match(line)):
			add(found, versions, m.group(1), Evidence(filename, lineno, ['Old Rod', ANY_WATER]))
			hits += 1
	if hits != 1:
		sys.exit(f'error: expected 1 `lb bc, <level>, <SPECIES>` in ItemUseOldRod, found {hits}')
	return filename


def collect_good_rod(found):
	filename = path('data', 'wild', 'good_rod.asm')
	for lineno, line, versions, glabel, _ in scan(filename):
		if glabel == 'GoodRodMons' and (m := DB_RE.match(line)):
			add(found, versions, m.group(1), Evidence(filename, lineno, ['Good Rod', ANY_WATER]))
	return filename


def collect_super_rod(found):
	filename = path('data', 'wild', 'super_rod.asm')
	group_maps = defaultdict(list)  # (versions, group) -> maps
	group_mons = []  # (lineno, versions, group, species)
	for lineno, line, versions, glabel, llabel in scan(filename):
		if glabel != 'SuperRodData':
			continue
		if m := DBW_RE.match(line):
			for v in versions:
				group_maps[(v, m.group(2))].append(m.group(1))
		elif llabel and (m := DB_RE.match(line)):
			group_mons.append((lineno, versions, llabel, m.group(1)))
	for lineno, versions, group, species in group_mons:
		for v in versions:
			maps = group_maps.get((v, group))
			if maps:  # a group no map points to is unreachable
				add(found, {v}, species, Evidence(filename, lineno, [f'Super Rod {group}'] + maps))
	return filename


def print_list(title, names):
	print(f'{title} ({len(names)}):')
	for name in names:
		print(f'  {name}')
	print()


def main():
	parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[1])
	parser.add_argument('--include-rods', action='store_true',
		help='also count Old/Good/Super Rod encounters as wild, and show evidence')
	args = parser.parse_args()

	species = read_species()
	map_found = {v: defaultdict(list) for v in VERSIONS}
	files = collect_map_tables(map_found)

	rod_found = {v: defaultdict(list) for v in VERSIONS}
	if args.include_rods:
		files += [collect_old_rod(rod_found), collect_good_rod(rod_found), collect_super_rod(rod_found)]

	found = {v: set(map_found[v]) | set(rod_found[v]) for v in VERSIONS}
	unknown = (found['RED'] | found['BLUE']) - set(species)
	if unknown:
		sys.exit(f'error: wild tables reference non-species names: {sorted(unknown)}')

	source = 'map tables + fishing rods' if args.include_rods else 'map tables only (no fishing)'
	print(f'Scanned {len(files)} files; {source}.\n')

	red_missing = [s for s in species if s not in found['RED']]
	blue_missing = [s for s in species if s not in found['BLUE']]
	both_missing = [s for s in red_missing if s not in found['BLUE']]

	print_list('Never wild in Red or Blue', both_missing)
	print_list('Not wild in Red (total)', red_missing)
	print_list('  ...of which wild only in Blue (Blue exclusives)',
		[s for s in red_missing if s in found['BLUE']])
	print_list('Wild only in Red (Red exclusives)',
		[s for s in blue_missing if s in found['RED']])

	if args.include_rods:
		newly = [s for s in species
			if any(s in rod_found[v] and s not in map_found[v] for v in VERSIONS)]
		print(f'Catchable only by fishing in at least one version ({len(newly)}):')
		for s in newly:
			vers = [v for v in VERSIONS if s in rod_found[v] and s not in map_found[v]]
			print(f'  {s}  (rod-only in: {", ".join(vers)})')
			seen = set()
			for v in vers:
				for ev in rod_found[v][s]:
					if str(ev) not in seen:
						seen.add(str(ev))
						print(f'    {ev}')
		print()


if __name__ == '__main__':
	main()
