// skills-router worker — AntiGem custom plugin
// Handles mcp_tool_call messages dispatched via chrome.runtime.onMessage.
// read-only file inspection via chrome.antigem.*; no shell/child_process in VM.

const ROOT_CANDIDATES = [
  "/data/user/0/ai.antigem/files/home/projects",
  "/sdcard",
  "~",
];

function resolveRoot(root) {
  if (!root) return ROOT_CANDIDATES[0];
  if (root === "~") return ROOT_CANDIDATES[2];
  return root;
}

function skillDirs(root) {
  return [
    { path: `${root}/.agents/skills`, scope: "project" },
    { path: `${root}/skills`, scope: "project" },
  ];
}

function parseFrontmatter(text) {
  const lines = text.split("\n");
  if (lines[0] !== "---") return null;
  const end = lines.indexOf("---", 1);
  if (end === -1) return null;
  const fm = {};
  for (let i = 1; i < end; i++) {
    const m = lines[i].match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)$/);
    if (m) fm[m[1]] = m[2].trim();
  }
  return fm;
}

async function readText(path) {
  try {
    const res = await chrome.antigem.readFile({ path, encoding: "utf8" });
    return res.data || res.content || res.text || "";
  } catch (e) {
    return null;
  }
}

async function listFiles(dir) {
  try {
    const res = await chrome.antigem.listFiles({ path: dir, limit: 500 });
    return res.files || res.entries || res.list || [];
  } catch (e) {
    return [];
  }
}

async function handleListSkills({ root }) {
  const r = resolveRoot(root);
  const skills = [];
  for (const d of skillDirs(r)) {
    const entries = await listFiles(d.path);
    for (const e of entries) {
      if (!e.isFile) continue;
      const name = e.name || "";
      if (!name.endsWith(".md")) continue;
      const disabled = name.endsWith(".disabled");
      const base = disabled ? name.replace(/\.disabled$/, "") : name.replace(/\.md$/, "");
      const skillId = base;
      const text = await readText(e.path);
      if (text === null) continue;
      const fm = parseFrontmatter(text) || {};
      skills.push({
        id: skillId,
        name: fm.name || skillId,
        description: fm.description || "",
        scope: d.scope,
        status: disabled ? "Disabled" : "Active",
        path: e.path,
      });
    }
  }
  return { skills, count: skills.length, root: r };
}

async function handleReadSkill({ skill_id, root }) {
  const r = resolveRoot(root);
  for (const d of skillDirs(r)) {
    for (const ext of ["SKILL.md", "SKILL.md.disabled"]) {
      const path = `${d.path}/${skill_id}/${ext}`;
      const text = await readText(path);
      if (text !== null) {
        return {
          skill_id,
          status: ext.endsWith(".disabled") ? "Disabled" : "Active",
          scope: d.scope,
          path,
          content: text,
        };
      }
    }
  }
  throw new Error(`Skill not found: ${skill_id}`);
}

async function handleRoute({ query, root }) {
  const r = resolveRoot(root);
  // The JS VM has no shell/child_process; routing runs on the host via Python.
  return {
    decision: "no_route",
    reason: "router_executes_on_host",
    instruction: `Run on host: python3 ${r}/skills-router-meta-skill/scripts/skills_router.py route "${query}" --root ${r}`,
    root: r,
  };
}

async function handleDormancyCheck({ root }) {
  const r = resolveRoot(root);
  const active = [];
  const dormant = [];
  for (const d of skillDirs(r)) {
    const entries = await listFiles(d.path);
    for (const e of entries) {
      if (!e.isFile || !e.name.endsWith(".md")) continue;
      const disabled = e.name.endsWith(".disabled");
      const item = { id: e.name.replace(/\.md(\.disabled)?$/, ""), path: e.path, scope: d.scope };
      if (disabled) dormant.push(item); else active.push(item);
    }
  }
  return { root: r, active, dormant, active_count: active.length, dormant_count: dormant.length };
}

const HANDLERS = {
  list_skills: handleListSkills,
  read_skill: handleReadSkill,
  route: handleRoute,
  dormancy_check: handleDormancyCheck,
};

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type !== "mcp_tool_call") return false;
  const { tool, args } = message;
  const handler = HANDLERS[tool];
  if (!handler) {
    sendResponse({ isError: true, content: [{ type: "text", text: `Unknown tool: ${tool}` }] });
    return true;
  }
  Promise.resolve()
    .then(() => handler(args || {}))
    .then((result) => sendResponse({ content: [{ type: "text", text: JSON.stringify(result, null, 2) }] }))
    .catch((e) => sendResponse({ isError: true, content: [{ type: "text", text: e.message || String(e) }] }));
  return true;
});

console.log("skills-router worker loaded");
