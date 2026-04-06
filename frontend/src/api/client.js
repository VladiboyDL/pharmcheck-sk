const API_BASE = import.meta.env.VITE_API_URL || "/api";

export async function searchDrugs(query) {
  const res = await fetch(`${API_BASE}/drugs/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error("Search failed");
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
