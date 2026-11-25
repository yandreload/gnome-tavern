# 🍺 Gnome Tavern

**An on-chain tavern on Gno.land — built for the [Gnome Tavern Hackathon](https://dorahacks.io/hackathon/gnome-tavern/detail) (DoraHacks, 23 Nov – 18 Dec 2026).**

Patrons claim free **Tavern Ale (ALE)**, a GRC20 token, buy drinks from the menu, and every tab lives on-chain forever. The realm's `Render()` page *is* the tavern: token info, menu, top patrons, and per-address balance / tab lookups.

## What it is

One Gno realm: `gno.land/r/g1x7gechxs30vum6u5mwsg4xkv2m7g2kkas7vzj6/tavern`

| Piece | What it does |
|---|---|
| `realm/tavern.gno` | GRC20 token **Tavern Ale (ALE)**, 6 decimals, 1,000,000 ALE minted to the keeper at deploy |
| `Faucet()` | 100 ALE per claim, max once every 24h per address, 100,000 ALE total cap (block-time enforced) |
| `BuyDrink(name)` | Pays ALE from the caller to the tavern till and adds the drink to their on-chain tab |
| `Menu()` / `TabOf()` / `TopPatrons()` | Read-only views: 5-drink menu, a patron's tab, top 5 patrons by ALE spent |
| `Transfer` / `Approve` / `TransferFrom` | Standard GRC20, proxied from `gno.land/p/nt/grc20/v0` |
| `Mint` / `Burn` | Keeper-only (owner-gated via `ownable`) |
| `Render(path)` | Markdown tavern page; `/balance/<addr>` and `/tab/<addr>` sub-pages (user input sanitized) |

Menu: Gnome Stout 50 ALE · Fairy Fizz 30 ALE · Dragon's Breath Ale 120 ALE · Mushroom Mead 80 ALE · Tavern Water 5 ALE.

## Status (honest)

- ✅ Realm written, `gno fmt` / `gno lint` clean, **6/6 `gno test` passing** (`realm/tavern_test.gno`).
- ✅ **Verified end-to-end on a local Gno chain** (`gnodev`): real `Faucet()` and `BuyDrink()` transactions, real balances and tabs — see `demo/tx-faucet.txt`, `demo/tx-buydrink.txt`, and the demo video.
- ⏳ **Onyx testnet deployment is pending faucet funding.** The deployer key (`g1x7gechxs30vum6u5mwsg4xkv2m7g2kkas7vzj6`) holds 0 ugnot. The Onyx faucet at https://faucet.gno.land needs a GitHub login + hCaptcha solve in a browser — see [`DEPLOY.md`](DEPLOY.md) for the exact one-time step. Once funded, deployment is a single `addpkg` (commands in `DEPLOY.md`).

## Demo video

`demo/gnome-tavern-demo.mp4` (1280×720, 42s, English narration) — title, the live tavern page, the real Faucet transaction, the real BuyDrink transaction, and the live tab page. Built from real screenshots and real tx logs by `demo/build_video.py`.

## Try it (CLI, no key needed for reads)

```bash
node cli/tavern.mjs status    # chain height + tavern page
node cli/tavern.mjs menu
node cli/tavern.mjs balance <g1-address>
node cli/tavern.mjs tab <g1-address>
node cli/tavern.mjs top
```

Writes print the exact `gnokey` command; add `--exec --key <name>` to run it (key must hold test GNOT):

```bash
node cli/tavern.mjs faucet --exec --key mykey
node cli/tavern.mjs buy "Gnome Stout" --exec --key mykey
```

Flags: `--remote <rpc-url>` (default Onyx `https://rpc.latest.testnets.gno.land:443`), `--realm <pkgpath>`, `--chainid <id>` (default `onyx-1`; use `dev` for a local `gnodev`).

## Run it locally

```bash
# toolchain (Go 1.23+): clone gnolang/gno and `make install` for gno, gnokey, gnodev
gnodev local realm/            # boots a devnet, serves the tavern at :8888
gno test -root-dir <gno-clone> realm/   # unit tests
```

## Deploy it (testnet)

See [`DEPLOY.md`](DEPLOY.md) — one `gnokey maketx addpkg` after the faucet step.

## Security notes

- Faucet and tab state are keyed by `cur.Previous().Address()` inside crossing functions (caller identity per `docs/resources/gno-interrealm.md`).
- `Render()` echoes only `sanitize.InlineText`-cleaned path segments (per the Gno security guide).
- The realm never returns pointers to `/p/`-type state; only scalar values and strings leave the realm.
- `Mint`/`Burn` are owner-gated; the faucet cannot mint past its cap.

## License

MIT — see [LICENSE](LICENSE).
