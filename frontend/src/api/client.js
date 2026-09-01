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

export async function pharmacistChat(message, history = [], contextDrugs = []) {
  const res = await fetch(`${API_BASE}/pharmacist/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      history,
      context_drugs: contextDrugs,
    }),
  });
  if (!res.ok) throw new Error("Pharmacist chat failed");
  return res.json();
}

// ── Dispensing window ──────────────────────────────────────────────────────────

export async function getDemoCards() {
  const res = await fetch(`${API_BASE}/identity/cards`);
  if (!res.ok) throw new Error("Nepodarilo sa načítať zoznam kariet");
  return res.json();
}

export async function readCard(cardId) {
  const res = await fetch(`${API_BASE}/identity/card`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ card_id: cardId }),
  });
  if (!res.ok) throw new Error("Karta poistenca nebola rozpoznaná");
  return res.json();
}

export async function verifyBiometric(cardId, { frameSignature = null, forceMismatch = false } = {}) {
  const res = await fetch(`${API_BASE}/identity/biometric`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      card_id: cardId,
      frame_signature: frameSignature,
      force_mismatch: forceMismatch,
    }),
  });
  if (!res.ok) throw new Error("Biometrické overenie zlyhalo");
  return res.json();
}

export async function getScenario(cardId) {
  const res = await fetch(`${API_BASE}/dispense/scenarios/${cardId}`);
  if (!res.ok) return null;
  return res.json();
}

export async function verifyDispense({ cardId, prescriptionText, identityVerified = true, intake = {} }) {
  const res = await fetch(`${API_BASE}/dispense/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      card_id: cardId,
      prescription_text: prescriptionText,
      identity_verified: identityVerified,
      intake,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Kontrola receptu zlyhala");
  }
  return res.json();
}

export async function getDispenseLog(limit = 50) {
  const res = await fetch(`${API_BASE}/dispense/log?limit=${limit}`);
  if (!res.ok) throw new Error("Nepodarilo sa načítať auditný záznam");
  return res.json();
}

export async function explainInteraction({ substanceA, substanceB, severity }) {
  const res = await fetch(`${API_BASE}/interactions/explain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ substance_a: substanceA, substance_b: substanceB, severity }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Vysvetlenie sa nepodarilo načítať");
  }
  return res.json();
}

export async function getIntakeQuestions(cardId) {
  const params = cardId ? `?card_id=${encodeURIComponent(cardId)}` : "";
  const res = await fetch(`${API_BASE}/dispense/intake${params}`);
  if (!res.ok) throw new Error("Nepodarilo sa načítať otázky");
  return res.json();
}
