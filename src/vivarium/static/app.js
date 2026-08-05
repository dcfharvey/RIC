/* Tableau de bord local du Vivarium (Phase 4.1D).
   JavaScript natif uniquement, aucune dépendance externe.
   Sécurité : les données serveur sont affichées via textContent et les
   éléments créés par createElement (jamais par concaténation HTML) ; jeton
   local lu depuis une balise meta puis retirée du DOM ; jeton transmis
   uniquement dans X-Vivarium-Token. */
(function () {
  "use strict";

  // --- jeton local : lu depuis la meta, puis retirée du DOM ---
  var token = null;
  var meta = document.querySelector('meta[name="vivarium-token"]');
  if (meta) {
    token = meta.getAttribute("content");
    meta.remove();
  }

  var state = {
    worlds: [],
    worldId: null,
    characters: [],
    characterKey: null,
    refreshing: false
  };

  // --- références DOM ---
  var worldList = document.getElementById("world-list");
  var charList = document.getElementById("char-list");
  var charDetail = document.getElementById("char-detail");
  var journalList = document.getElementById("journal-list");
  var worldName = document.getElementById("world-name");
  var worldStatus = document.getElementById("world-status");
  var canonicalTime = document.getElementById("canonical-time");
  var globalMessage = document.getElementById("global-message");
  var commandMessage = document.getElementById("command-message");
  var pauseBtn = document.getElementById("pause-btn");
  var resumeBtn = document.getElementById("resume-btn");
  var renameForm = document.getElementById("rename-form");
  var renameInput = document.getElementById("rename-input");
  var moveForm = document.getElementById("move-form");
  var moveInput = document.getElementById("move-input");
  var refreshBtn = document.getElementById("refresh-btn");

  function safeMessage(e) {
    return (e && e.message) ? e.message : "Erreur inconnue.";
  }

  function showGlobal(msg, isError) {
    globalMessage.textContent = msg;
    globalMessage.className = "global-message" + (isError ? " error" : "");
  }

  function showCommand(msg, isError) {
    commandMessage.textContent = msg;
    commandMessage.className = "message" + (isError ? " error" : " success");
  }

  function clear(el) { el.replaceChildren(); }

  // --- Fetch commune ---
  async function apiGet(path) {
    var resp = await fetch(path, { headers: { "Accept": "application/json" } });
    if (!resp.ok) {
      throw new Error(await parseError(resp));
    }
    var ctype = resp.headers.get("Content-Type") || "";
    if (ctype.indexOf("application/json") !== 0) {
      throw new Error("Réponse serveur invalide.");
    }
    var data = await resp.json();
    if (!data || typeof data !== "object" || data.ok !== true) {
      throw new Error("Réponse serveur invalide.");
    }
    return data.data;
  }

  async function parseError(resp) {
    try {
      var data = await resp.json();
      if (data && data.error && data.error.message) return data.error.message;
    } catch (e) { /* ignore */ }
    return "Erreur serveur (" + resp.status + ").";
  }

  async function apiPost(command, params) {
    if (!token) {
      throw new Error("Jeton local manquant.");
    }
    var resp = await fetch("/api/commands/" + encodeURIComponent(command), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Vivarium-Token": token
      },
      body: JSON.stringify(params)
    });
    var data = null;
    try { data = await resp.json(); } catch (e) { data = null; }
    if (!data || typeof data !== "object") {
      throw new Error("Réponse serveur invalide.");
    }
    if (data.ok !== true) {
      var err = new Error(data.error && data.error.message ? data.error.message : "Commande refusée.");
      err.code = data.error && data.error.code;
      throw err;
    }
    return data.data;
  }

  // --- rendu ---
  function renderWorlds() {
    clear(worldList);
    if (!state.worlds.length) {
      var none = document.createElement("li");
      none.textContent = "Aucun monde";
      worldList.appendChild(none);
      return;
    }
    state.worlds.forEach(function (w) {
      var li = document.createElement("li");
      li.textContent = w.name || ("Monde " + w.id);
      if (w.id === state.worldId) li.classList.add("selected");
      li.addEventListener("click", function () { selectWorld(w.id); });
      worldList.appendChild(li);
    });
  }

  function renderCharacters() {
    clear(charList);
    if (!state.characters.length) {
      var none = document.createElement("li");
      none.textContent = "Aucun personnage";
      charList.appendChild(none);
      return;
    }
    state.characters.forEach(function (cv) {
      var c = cv.character;
      var li = document.createElement("li");
      var energy = (cv.energy != null) ? Math.round(cv.energy / 10) + "%" : "—";
      li.textContent = c.key + " · " + c.location + " · énergie " + energy;
      if (c.key === state.characterKey) li.classList.add("selected");
      li.addEventListener("click", function () { selectCharacter(c.key); });
      charList.appendChild(li);
    });
  }

  function addDetail(label, value) {
    var dt = document.createElement("dt");
    dt.textContent = label;
    var dd = document.createElement("dd");
    dd.textContent = value;
    charDetail.appendChild(dt);
    charDetail.appendChild(dd);
  }

  function renderDetail() {
    clear(charDetail);
    if (!state.characterKey) {
      var p = document.createElement("p");
      p.textContent = "Aucun personnage sélectionné.";
      charDetail.appendChild(p);
      return;
    }
    var cv = state.characters.find(function (x) { return x.character.key === state.characterKey; });
    if (!cv) return;
    var c = cv.character;
    addDetail("Nom", c.name);
    addDetail("Clé", c.key);
    addDetail("Lieu", c.location);
    addDetail("Énergie", (cv.energy != null) ? Math.round(cv.energy / 10) + "%" : "—");
    addDetail("Activité", cv.activity ? cv.activity.type : "—");
    addDetail("Blessure", cv.injury && cv.injury.severity != null ? cv.injury.severity : "—");
  }

  function renderJournal(events) {
    clear(journalList);
    if (!events || !events.length) {
      var none = document.createElement("li");
      none.textContent = "Journal vide";
      journalList.appendChild(none);
      return;
    }
    events.forEach(function (ev) {
      var li = document.createElement("li");
      li.textContent = (ev.occurred_at || "") + " — " + (ev.summary || ev.event_type);
      journalList.appendChild(li);
    });
  }

  function renderWorld(dash) {
    worldName.textContent = dash.world.name;
    worldStatus.textContent = dash.world.status === "paused" ? "EN PAUSE" : "ACTIF";
    worldStatus.className = "status " + dash.world.status;
    canonicalTime.textContent = dash.observed_canonical_at || "";
    updateCommandButtons(dash.world.status);
    if (renameForm) renameInput.value = dash.world.name || "";
  }

  function clearWorldView() {
    worldName.textContent = "—";
    worldStatus.textContent = "—";
    worldStatus.className = "status";
    canonicalTime.textContent = "—";
    updateCommandButtons(null);
  }

  function updateCommandButtons(status) {
    var paused = status === "paused";
    var hasWorld = status != null;
    pauseBtn.disabled = !hasWorld || paused;
    resumeBtn.disabled = !hasWorld || !paused;
  }

  // --- chargement / rafraîchissement ---
  async function refresh() {
    if (state.refreshing) return;
    state.refreshing = true;
    refreshBtn.disabled = true;
    try {
      var worlds = await apiGet("/api/worlds");
      var worldId = state.worldId;
      if (!worlds.some(function (w) { return w.id === worldId; })) {
        worldId = worlds.length ? worlds[0].id : null;
      }
      var dash = null, chars = [], events = [], detail = null;
      var charKey = state.characterKey;
      if (worldId != null) {
        dash = await apiGet("/api/worlds/" + encodeURIComponent(worldId));
        chars = await apiGet("/api/worlds/" + encodeURIComponent(worldId) + "/characters");
        events = await apiGet("/api/worlds/" + encodeURIComponent(worldId) + "/events?limit=50&offset=0&include_payload=false");
        if (!chars.some(function (cv) { return cv.character.key === charKey; })) {
          charKey = chars.length ? chars[0].character.key : null;
        }
        if (charKey != null) {
          detail = await apiGet("/api/worlds/" + encodeURIComponent(worldId) + "/characters/" + encodeURIComponent(charKey));
        }
      }
      // commit de l'état puis rendu (état précédent conservé en cas d'échec)
      state.worlds = worlds;
      state.worldId = worldId;
      state.characters = chars;
      state.characterKey = charKey;
      renderWorlds();
      if (worldId == null) {
        clearWorldView();
      } else {
        renderWorld(dash);
        renderCharacters();
        renderJournal(events);
        if (detail) {
          var idx = chars.findIndex(function (x) { return x.character.key === charKey; });
          if (idx >= 0) chars[idx] = detail;
        }
        renderDetail();
      }
      showGlobal("Vue actualisée.");
    } catch (e) {
      showGlobal("Erreur de rafraîchissement : " + safeMessage(e), true);
    } finally {
      state.refreshing = false;
      refreshBtn.disabled = false;
    }
  }

  function selectWorld(id) {
    state.worldId = id;
    state.characterKey = null;
    refresh();
  }

  function selectCharacter(key) {
    state.characterKey = key;
    refresh();
  }

  // --- commandes ---
  async function runCommand(command, params, successMsg) {
    if (state.worldId == null) {
      showCommand("Aucun monde sélectionné.", true);
      return false;
    }
    try {
      await apiPost(command, params);
      showCommand(successMsg, false);
      await refresh();
      return true;
    } catch (e) {
      showCommand(safeMessage(e), true);
      return false;
    }
  }

  pauseBtn.addEventListener("click", function () {
    runCommand("pause", { world_id: state.worldId }, "Monde en pause.");
  });

  resumeBtn.addEventListener("click", function () {
    runCommand("resume", { world_id: state.worldId }, "Monde repris.");
  });

  renameForm.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var name = renameInput.value;
    if (!name || !name.trim()) {
      showCommand("Le nom ne peut pas être vide.", true);
      return;
    }
    runCommand("rename", { world_id: state.worldId, name: name }, "Monde renommé.");
  });

  moveForm.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var dest = moveInput.value.trim();
    if (!dest) {
      showCommand("Indiquez une clé de lieu.", true);
      return;
    }
    var self = this;
    runCommand("move", {
      world_id: state.worldId,
      character_key: state.characterKey,
      destination: dest
    }, "Personnage déplacé.").then(function (ok) {
      if (ok) moveInput.value = "";
    });
  });

  refreshBtn.addEventListener("click", function () { refresh(); });

  // --- initialisation ---
  refresh();
})();
