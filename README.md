# Pokémon Red and Blue [![Build Status][ci-badge]][ci]

This is a disassembly of Pokémon Red and Blue.

It builds the following ROMs:

- Pokemon Red (UE) [S][!].gb `sha1: ea9bcae617fdf159b045185467ae58b2e4a48b9a`
- Pokemon Blue (UE) [S][!].gb `sha1: d7037c83e1ae5b39bde3c30787637ba1d4c48ce2`
- BLUEMONS.GB (debug build) `sha1: 5b1456177671b79b263c614ea0e7cc9ac542e9c4`
- dmgapae0.e69.patch `sha1: 0fb5f743696adfe1dbb2e062111f08f9bc5a293a`
- dmgapee0.e68.patch `sha1: ed4be94dc29c64271942c87f2157bca9ca1019c7`

To set up the repository, see [**INSTALL.md**](INSTALL.md).


## Non-wild Pokémon

Which of the 151 species can never be caught in the wild? The source of truth is [**tools/find_nonwild.py**](tools/find_nonwild.py); the lists below are a snapshot of its output, so re-run it after changing any encounter data.

```sh
python3 tools/find_nonwild.py                 # grass, cave and surfing tables only
python3 tools/find_nonwild.py --include-rods  # also count Old, Good and Super Rod
```

The script reads species from `constants/pokemon_constants.asm` (keeping only ids with a `DEX_` entry in `constants/pokedex_constants.asm`) and the `db <level>, <SPECIES>` lines in `data/wild/maps/*.asm`, honoring `IF DEF(_RED)` / `IF DEF(_BLUE)` blocks. `--include-rods` also parses the Old Rod species from `ItemUseOldRod` in `engine/items/item_effects.asm`, `GoodRodMons` in `data/wild/good_rod.asm`, and the map → group tables in `data/wild/super_rod.asm`, and prints file:line evidence for every species that only fishing makes catchable.

### Never wild in either version, fishing included (57)

Bulbasaur, Ivysaur, Venusaur, Charmander, Charmeleon, Charizard, Squirtle, Wartortle, Blastoise, Butterfree, Beedrill, Pidgeot, Nidoqueen, Nidoking, Clefable, Ninetales, Vileplume, Persian, Primeape, Arcanine, Poliwrath, Alakazam, Machamp, Victreebel, Tentacruel, Golem, Rapidash, Farfetch'd, Cloyster, Gengar, Exeggutor, Hitmonlee, Hitmonchan, Lickitung, Starmie, Mr. Mime, Jynx, Gyarados, Lapras, Eevee, Vaporeon, Jolteon, Flareon, Porygon, Omanyte, Omastar, Kabuto, Kabutops, Aerodactyl, Snorlax, Articuno, Zapdos, Moltres, Dragonair, Dragonite, Mewtwo, Mew

These must come from evolution, trades, gifts, fossils, the Game Corner, or static encounters.

### Not in any grass, cave or surfing table (63)

The 57 above, plus 6 species that can **only** be caught by fishing in both versions: Poliwag, Poliwhirl, Goldeen, Seaking, Magikarp, Dratini.

### Version exclusives

| | Grass/cave/surf only | With fishing (`--include-rods`) |
|---|---|---|
| Wild only in **Red** | Ekans, Arbok, Oddish, Gloom, Mankey, Growlithe, Horsea, Seadra, Scyther, Electabuzz (10) | Ekans, Arbok, Oddish, Gloom, Mankey, Growlithe, Scyther, Electabuzz (8) |
| Wild only in **Blue** | Sandshrew, Sandslash, Vulpix, Meowth, Bellsprout, Weepinbell, Krabby, Kingler, Magmar, Pinsir (10) | Sandshrew, Sandslash, Vulpix, Meowth, Bellsprout, Weepinbell, Magmar, Pinsir (8) |
| Not wild in Red at all | 73 (the 63 + 10 Blue exclusives) | 65 (the 57 + 8 Blue exclusives) |

Fishing removes Horsea/Seadra from the Red list (Super Rod in both versions) and Krabby/Kingler from the Blue list (Super Rod in both versions).


## See also

- [**Wiki**][wiki] (includes [tutorials][tutorials])
- [**Symbols**][symbols]
- [**Tools**][tools]

You can find us on [Discord (pret, #pokered)](https://discord.gg/d5dubZ3).

For other pret projects, see [pret.github.io](https://pret.github.io/).

[wiki]: https://github.com/pret/pokered/wiki
[tutorials]: https://github.com/pret/pokered/wiki/Tutorials
[symbols]: https://github.com/pret/pokered/tree/symbols
[tools]: https://github.com/pret/gb-asm-tools
[ci]: https://github.com/pret/pokered/actions
[ci-badge]: https://github.com/pret/pokered/actions/workflows/main.yml/badge.svg
