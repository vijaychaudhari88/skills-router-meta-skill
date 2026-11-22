---
name: pxpipe
description: Token-saving context proxy for coding agents. Renders bulky context, system prompts, tool docs, and history as compact PNG images, cutting input tokens while streaming responses verbatim. Inspect proxy stats and savings.
version: 0.16.0
category: economy
triggers:
  - pxpipe
  - pxpipe status
  - pxpipe on
  - pxpipe off
  - pxpipe stats
  - pxpipe savings
  - token proxy
  - context image proxy
aliases:
  - pxpipe-proxy
  - /pxpipe
  - /pxpipe-stats
commands:
  - /pxpipe
  - /pxpipe-stats
---

# pxpipe — Token-Saving Context Proxy

`pxpipe` is a local proxy (`http://127.0.0.1:47821`) that cuts agent input tokens by converting dense context (system prompt, tool schemas, and older conversational turns) into compact images.

## Daemon & Status Management

Use the helper functions from `~/.pxpipe-helpers.sh`:

- **Check Status & Dashboard:**
  ```bash
  source ~/.pxpipe-helpers.sh && pxpipe-status
  ```
  Dashboard UI: `http://127.0.0.1:47821/`

- **Start Daemon (if stopped):**
  ```bash
  source ~/.pxpipe-helpers.sh && pxpipe-start
  ```

- **Activate Proxy Routing in Current Shell:**
  ```bash
  source ~/.pxpipe-helpers.sh && pxpipe-on
  ```
  Sets `HTTP_PROXY`, `HTTPS_PROXY` to `http://127.0.0.1:47821` with strict `NO_PROXY` loopback isolation (`localhost,127.0.0.1,::1,127.0.0.0/8,*.local,*.internal`).

- **Deactivate Proxy Routing:**
  ```bash
  source ~/.pxpipe-helpers.sh && pxpipe-off
  ```

- **Inspect Offline Savings & Metrics:**
  ```bash
  pxpipe stats
  ```
