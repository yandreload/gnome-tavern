# Deployment log — Gnome Tavern

## Target

- **Network:** Onyx testnet (`onyx-1`), RPC `https://rpc.onyx.testnets.gno.land:443`
  (alias `https://rpc.latest.testnets.gno.land:443`)
- **Realm path:** `gno.land/r/g1x7gechxs30vum6u5mwsg4xkv2m7g2kkas7vzj6/tavern`
- **Deployer key:** `tavern-deployer`, address `g1x7gechxs30vum6u5mwsg4xkv2m7g2kkas7vzj6`
  (fresh testnet-only dev key; keybase + password live outside this repo)
- **Live page (after deploy):** `https://latest.testnets.gno.land/r/g1x7gechxs30vum6u5mwsg4xkv2m7g2kkas7vzj6/tavern`

## Status: ⏳ BLOCKED on faucet funding (one human step)

The deployer address holds **0 ugnot** (checked 25 Nov 2026 via
`gnokey query bank/balances/...` — empty). Deploying costs gas + a storage
deposit (~300,000 ugnot for a realm this size), and every call needs gas.

### Why it can't be done from the shell

The Onyx faucet (https://faucet.gno.land → backend
https://faucet.onyx.testnets.gno.land) requires, per its own frontend code:

1. **GitHub OAuth login** — the claim sends a GitHub OAuth `code`
   (`localStorage["last-code"]`) with the request.
2. **hCaptcha solve** — site key `85609fa2-6ed6-4fe0-904c-2bae865ab6ec`.
   The backend's `claim` JSON-RPC method rejects requests without a valid
   captcha token (`"invalid captcha request"`).
3. The shared egress IP may also be rate-limited (`"unable to verify IP
   request, invalid number of requests"` seen on one probe).

There is no API key, no CLI, and no captcha-free path. This is a
**one-time browser step for a human**.

### The one-time step (for the person with the browser)

1. Open https://faucet.gno.land
2. Log in with GitHub (any GitHub account works; this funds the *address*,
   it does not link the account to anything).
3. Pick the **Onyx Faucet** (chain `onyx-1`), paste this address:
   `g1x7gechxs30vum6u5mwsg4xkv2m7g2kkas7vzj6`
4. Solve the captcha, submit. Amounts offered: 100 / 200 / 300 GNOT.
   (100 GNOT is plenty: deploy ≈ 0.3 GNOT + gas.)
5. Confirm the funds landed:
   `gnokey query bank/balances/g1x7gechxs30vum6u5mwsg4xkv2m7g2kkas7vzj6 -remote https://rpc.onyx.testnets.gno.land:443`

### Deploy (once funded)

```bash
export PATH=$HOME/workspace/tools/gno-bin:$PATH
cd repo/realm
gnokey maketx addpkg \
  -pkgpath "gno.land/r/g1x7gechxs30vum6u5mwsg4xkv2m7g2kkas7vzj6/tavern" \
  -pkgdir . \
  -gas-fee 5000ugnot -gas-wanted 5000000 \
  -chainid onyx-1 -remote https://rpc.onyx.testnets.gno.land:443 \
  tavern-deployer
```

Then verify (wait ~10s after deploy):

```bash
gnokey query vm/qrender -data "gno.land/r/g1x7gechxs30vum6u5mwsg4xkv2m7g2kkas7vzj6/tavern:" \
  -remote https://rpc.onyx.testnets.gno.land:443
node cli/tavern.mjs status   # from repo/
```

Smoke test on testnet (same as local, see `demo/tx-*.txt`):

```bash
gnokey maketx call -pkgpath "gno.land/r/g1x7gechxs30vum6u5mwsg4xkv2m7g2kkas7vzj6/tavern" \
  -func "Faucet" -gas-fee 15000ugnot -gas-wanted 15000000 \
  -chainid onyx-1 -remote https://rpc.onyx.testnets.gno.land:443 tavern-deployer
```

## Local verification (done 25 Nov 2026)

Full end-to-end run on a local `gnodev` devnet (chain `dev`):

| Step | Result |
|---|---|
| `gno test` | 6/6 PASS |
| `Faucet()` as new patron | `(100000000 int64)`, OK!, height 9, gas 6,739,049 |
| `BuyDrink("Gnome Stout")` | `"Enjoy your Gnome Stout! Tab total: 50.000000 ALE."`, OK!, height 11, gas 10,941,262 |
| `BalanceOf(patron)` after | `50000000` (50 ALE) |
| `TabOf(patron)` | `Tab total: 50.000000 ALE / - Gnome Stout x1` |
| `Render("")` | Full tavern page (menu, top patrons, faucet info) |
| CLI reads + `--exec` write | Verified (`menu`, `balance`, `tab`, `top`, `buy "Tavern Water"`) |

Full logs: `demo/tx-faucet.txt`, `demo/tx-buydrink.txt`, `demo/tx-tab.txt`.
Tx hashes (local devnet): Faucet `FBEigCZCqF922CA1VRcsnIfHSPQ/ZE4RS5AVV5XUO24=`,
BuyDrink `EZ/4EYN+EQlcKDDDNKLBWRsVmHzMwTxKvM/RRM2DpOg=`.

## Toolchain notes (for reproducibility)

- Go 1.27.4 + `gnolang/gno` @ `2162ee2` (25 Nov 2026), built from source.
- The stock `gnokey`/`gno` RPC client dials targets directly and ignores
  `HTTPS_PROXY`, which breaks TLS in this sandboxed VM (egress proxy).
  Local patch applied to the toolchain copy only
  (`tm2/pkg/bft/rpc/lib/client/http/client.go`: use a standard proxy-aware
  transport for http(s) remotes). Not part of this repo.
- Gas notes: `Faucet()` ≈ 6.2–6.7M gas, `BuyDrink()` ≈ 10.3–10.9M gas —
  use `-gas-wanted 15000000` for calls, `5000000` for `addpkg`.
