const API_BASE = import.meta.env.VITE_API_URL || "/api";

export async function searchDrugs(query, limit = 15) {
  const res = await fetch(`${API_BASE}/drugs/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  if (!res.ok) throw new Error("Search failed");
  return res.json();
}

export async function getDrugDetail(drugId) {
  const res = await fetch(`${API_BASE}/drugs/${drugId}`);
  if (!res.ok) throw new Error("Drug not found");
  return res.json();
}

export async function checkInteractions(drugIds) {
  const res = await fetch(`${API_BASE}/interactions/check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ drug_ids: drugIds }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Interaction check failed");
  }
  return res.json();
}

export async function getAlternatives(drugId, contextIds = []) {
  const params = contextIds.length ? `?context_ids=${contextIds.join(",")}` : "";
  const res = await fetch(`${API_BASE}/drugs/${drugId}/alternatives${params}`);
  if (!res.ok) throw new Error("Failed to load alternatives");
  return res.json();
}

export async function getStats() {
  const res = await fetch(`${API_BASE}/drugs/stats`);
  if (!res.ok) throw new Error("Failed to load stats");
  return res.json();
}

export async function browseATC(code = "") {
  const params = code ? `?code=${encodeURIComponent(code)}` : "";
  const res = await fetch(`${API_BASE}/drugs/atc${params}`);
  if (!res.ok) throw new Error("Failed to browse ATC");
  return res.json();
}
