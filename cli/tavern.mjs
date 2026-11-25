#!/usr/bin/env node
// Gnome Tavern CLI — talk to the tavern realm from your terminal.
//
// Reads (menu, balance, tab, render) hit the chain RPC directly, no key
// needed. Writes (faucet, buy) print the exact `gnokey` command; pass
// --exec --key <name> to run it (gnokey must be installed and the key
// funded with test GNOT).
//
// Usage:
//   node cli/tavern.mjs status                       # chain + realm render
//   node cli/tavern.mjs menu                         # drink menu
//   node cli/tavern.mjs balance <g1address>          # ALE balance
//   node cli/tavern.mjs tab <g1address>              # patron's tab
//   node cli/tavern.mjs top                          # top 5 patrons
//   node cli/tavern.mjs faucet [--exec --key NAME]   # claim 100 ALE
//   node cli/tavern.mjs buy "Gnome Stout" [--exec --key NAME]
//
// Flags: --remote <rpc-url>  (default: Onyx testnet latest endpoint)
//        --realm <pkgpath>   (default: the deployed tavern realm)
//        --exec --key NAME   run the write via gnokey instead of printing it

const DEFAULT_REMOTE = "https://rpc.latest.testnets.gno.land:443";
const DEFAULT_REALM =
  "gno.land/r/g1x7gechxs30vum6u5mwsg4xkv2m7g2kkas7vzj6/tavern";
const DEFAULT_CHAIN_ID = "onyx-1";

const args = process.argv.slice(2);
const flags = {};
for (let i = 0; i < args.length; i++) {
  if (args[i].startsWith("--")) {
    const k = args[i].slice(2);
    flags[k] = args[i + 1] && !args[i + 1].startsWith("--") ? args[++i] : true;
  }
}
const pos = args.filter((a) => !a.startsWith("--"));
const cmd = pos[0];
const remote = flags.remote || DEFAULT_REMOTE;
const realm = flags.realm || DEFAULT_REALM;
const chainId = flags.chainid || DEFAULT_CHAIN_ID;

function usage(code = 0) {
  console.log(`Gnome Tavern CLI — ${realm}\n`);
  console.log("  status | menu | balance <addr> | tab <addr> | top");
  console.log('  faucet [--exec --key NAME] | buy "<drink>" [--exec --key NAME]');
  console.log("\nFlags: --remote <rpc-url>  --realm <pkgpath>  --chainid <id>  --exec --key <name>");
  process.exit(code);
}

// Minimal Tendermint JSON-RPC client (no dependencies).
async function rpc(method, params = {}) {
  const body = { jsonrpc: "2.0", id: 1, method, params };
  const res = await fetch(remote, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`RPC ${res.status}: ${await res.text()}`);
  const json = await res.json();
  if (json.error) throw new Error(`RPC error: ${JSON.stringify(json.error)}`);
  return json.result;
}

async function abciQuery(path, data) {
  const r = await rpc("abci_query", {
    path,
    data: Buffer.from(data, "utf8").toString("base64"),
  });
  const resp = r?.response ?? {};
  const b64 = resp?.ResponseBase?.Data ?? resp?.Data ?? resp?.data ?? "";
  return b64 ? Buffer.from(b64, "base64").toString("utf8") : "";
}

async function qeval(expr) {
  let out = (await abciQuery("vm/qeval", expr)).trim();
  // qeval wraps values Go-style: ("..." string) / (123 int64)
  const ms = out.match(/^\("(.*)" string\)$/s);
  if (ms) out = ms[1].replace(/\\n/g, "\n").replace(/\\"/g, '"');
  const mi = out.match(/^\((-?\d+) int64\)$/);
  if (mi) out = mi[1];
  return out;
}
async function qrender(path) {
  return (await abciQuery("vm/qrender", `${realm}:${path}`)).trim();
}

function gnokeyArgv(func, fnArgs, key) {
  const argv = [
    "maketx", "call",
    "-pkgpath", realm,
    "-func", func,
    ...fnArgs.flatMap((a) => ["-args", a]),
    "-gas-fee", "15000ugnot",
    "-gas-wanted", "15000000",
    "-chainid", chainId,
    "-remote", remote,
  ];
  // When stdin is piped (scripted use), gnokey cannot prompt on a TTY, so
  // it must read the key password from stdin instead. Interactive use
  // (real terminal) keeps the normal password prompt.
  if (!process.stdin.isTTY) argv.push("-insecure-password-stdin");
  argv.push(key);
  return argv;
}

function shellQuote(s) {
  return /[\s"]/.test(s) ? `"${s.replace(/"/g, '\\"')}"` : s;
}

async function runWrite(func, fnArgs) {
  const argv = gnokeyArgv(func, fnArgs, flags.key || "<key-name>");
  if (!flags.exec) {
    console.log("Run this (needs a funded key):\n");
    console.log("  gnokey " + argv.map(shellQuote).join(" "));
    return;
  }
  if (!flags.key) {
    console.error("--exec needs --key <name>");
    process.exit(2);
  }
  // Run gnokey attached to this terminal (like running it directly):
  // password prompt works on a TTY; piped passwords work because we add
  // -insecure-password-stdin when stdin is not a TTY (see gnokeyArgv).
  const { spawn } = await import("node:child_process");
  const child = spawn("gnokey", argv, { stdio: "inherit" });
  const code = await new Promise((resolve) => child.on("close", resolve));
  process.exit(code ?? 1);
}

const MENU = [
  "Gnome Stout",
  "Fairy Fizz",
  "Dragon's Breath Ale",
  "Mushroom Mead",
  "Tavern Water",
];

switch (cmd) {
  case "status": {
    const s = await rpc("status", {});
    console.log(`chain: ${s.node_info.network}  height: ${s.sync_info.latest_block_height}`);
    console.log("\n" + (await qrender("")));
    break;
  }
  case "menu":
    console.log(await qeval(`${realm}.Menu()`));
    break;
  case "balance": {
    if (!pos[1]) usage(2);
    console.log(await qeval(`${realm}.BalanceOf(address("${pos[1]}"))`));
    break;
  }
  case "tab": {
    if (!pos[1]) usage(2);
    console.log(await qeval(`${realm}.TabOf(address("${pos[1]}"))`));
    break;
  }
  case "top":
    console.log(await qeval(`${realm}.TopPatrons()`));
    break;
  case "faucet":
    await runWrite("Faucet", []);
    break;
  case "buy": {
    const drink = pos[1];
    if (!drink || !MENU.includes(drink)) {
      console.error(`Unknown drink. Menu: ${MENU.join(", ")}`);
      process.exit(2);
    }
    await runWrite("BuyDrink", [drink]);
    break;
  }
  default:
    usage(1);
}
