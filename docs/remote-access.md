# Private remote access (Phase 16)

**Status: Implemented.** The posture is decided, enforced in code, documented,
and checkable. A working tailnet attachment has **not** been verified - there
is no Tailscale node in this environment - so this phase is not Complete.

Decision: **ADR-010** in `docs/architecture-decision-record.md`.

---

## The decision

1. **SabiRoute listens on loopback.** `127.0.0.1` is the default and the
   supported value. Anything else is refused at startup unless the operator
   sets `SABIROUTE_ALLOW_NON_LOOPBACK_BIND=1` deliberately.
2. **Remote access is a private tailnet, never the public internet.** The
   supported path is `tailscale serve`, which terminates TLS on the tailnet and
   proxies to `http://127.0.0.1:8000`.
3. **Funnel is forbidden.** Tailscale Funnel publishes a service to the open
   internet. Public exposure is gated behind the Phase 20 review, and a phase
   gate is not something to route around with a CLI flag.
4. **Tailscale authenticates the network. SabiRoute authenticates the caller.**
   Administrative endpoints still require the admin key. The console asks for
   it and holds it in session storage. No `Tailscale-User-*` header is trusted
   for authorisation, because headers are trivially forgeable by anything that
   can reach the listener.

## Why this shape

**Why Serve and not a reverse proxy on a LAN address.** A LAN bind is reachable
by every device on the network, including guests and IoT hardware, with no
identity attached. Serve adds a device identity and a per-tailnet ACL in front
of a listener that does not change. The application surface stays identical to
the local case, so there is no second code path to keep secure.

**Why loopback and not `0.0.0.0` behind the proxy.** If the app binds wide, the
proxy is optional: anyone who reaches the port skips it. Binding loopback makes
the proxy the only path, which is the property that makes the proxy worth
having.

**Why not put auth in Tailscale.** Tailscale gives identity at the network
layer. Mapping that into SabiRoute's permission model would mean trusting an
inbound header, and it would couple the gateway's access control to a third
party's client version. Two independent gates - tailnet reachability and the
admin key - fail independently, which is the point.

**Why an opt-in variable instead of hard-failing forever.** Containers
legitimately bind a bridge address inside a private network. Refusing that
outright would force operators to patch the image. The variable is an
acknowledgement that the bind is already private; it is named so that it reads
as a warning in any config review.

## Threat model

| Threat | Covered by |
|---|---|
| Another device on the same Wi-Fi reaching the gateway | loopback bind |
| A tailnet member who is not the owner reaching the console | tailnet ACL, then the admin key |
| The console leaking the key into history or disk | session storage only, `autocomplete="off"`, no URL parameters |
| Accidental public exposure | Funnel refused by the posture check; no Funnel command anywhere in the repo |
| A forged identity header | headers are never trusted for authorisation |
| Provider credentials leaking through the console | the console reads only the five read-only admin endpoints; no provider key is in any payload |

**Not covered:** a compromised device that is a legitimate tailnet member. That
device has the owner's reach, and the answer is revoking it in the tailnet, not
in SabiRoute.

## Runbook

Prerequisites: Tailscale installed and logged in on the host running SabiRoute,
MagicDNS and HTTPS certificates enabled for the tailnet.

1. Start the gateway as usual. It listens on `127.0.0.1:8000`:

   ```
   SABIROUTE_ADMIN_KEY=<your-admin-key> uv run sabiroute
   ```

2. Publish the console on the tailnet only:

   ```
   tailscale serve --bg --https=443 http://127.0.0.1:8000
   ```

3. Verify the posture:

   ```
   ./.venv/bin/python scripts/phase16_remote_access_check.py
   ```

   Expect `bind PASS`, `identity PASS`, `serve PASS`, `funnel PASS`. The console
   is then at `https://<node>.<tailnet>.ts.net/admin/dashboard/`.

4. Open the console from another device on the tailnet and paste the admin key.

## Rollback

```
tailscale serve reset
```

That removes the proxy and leaves the gateway running on loopback. Nothing in
SabiRoute needs to change, because the tailnet was never part of its
configuration. To stop the gateway, stop the process as usual.

## Access control

Restrict the node to the owner's devices. An illustrative ACL fragment:

```jsonc
{
  "tagOwners": { "tag:sabiroute": ["autogroup:admin"] },
  "grants": [
    { "src": ["autogroup:admin"], "dst": ["tag:sabiroute"], "ip": ["443"] }
  ],
  "ssh": []
}
```

No shared users, no `autogroup:member` grant, no Funnel. If the node is shared
with anyone, the admin key is the only thing between them and the console, and
that is a weaker posture than the decision intends.

## Configuration

| Variable | Default | Effect |
|---|---|---|
| `SABIROUTE_HOST` | `127.0.0.1` | Listener address. Non-loopback values are refused. |
| `SABIROUTE_ALLOW_NON_LOOPBACK_BIND` | unset | Opt-in that permits a non-loopback bind. Set it only for a container network that is already private. |
| `SABIROUTE_API_PORT` | `8000` | Listener port; the Serve target must match. |

## Trade-offs accepted

- **No SSO.** A tailnet member still types an admin key. Accepted: it keeps
  SabiRoute's authorisation model self-contained and independent of a third
  party.
- **One node, one key.** There is no per-user admin identity yet. That is
  Phase 17 territory (permissions and role separation), deliberately not
  invented here.
- **Serve pins a port mapping.** Changing `SABIROUTE_API_PORT` means re-running
  the Serve command; the posture check fails if the target no longer matches,
  which is the intended failure mode.
- **No mobile push or public share links.** Out of scope until Phase 20.

## What is not built

- No Tailscale SDK, no device-code flow, no OAuth callback in SabiRoute. The
  integration is intentionally the network, not the application.
- No automatic Serve configuration at startup. A server that publishes itself
  is a server that can publish itself by accident.
- No Funnel path, not even behind a flag.
