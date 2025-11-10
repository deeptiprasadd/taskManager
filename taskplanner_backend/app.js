// --- Firebase (Web Modular SDK) ---
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.14.0/firebase-app.js";
import { getMessaging, getToken, onMessage, isSupported } from "https://www.gstatic.com/firebasejs/10.14.0/firebase-messaging.js";

// >>> YOUR Firebase web config (from your screenshot)
const firebaseConfig = {
  apiKey: "AIzaSyAdh_iiHbCIDIFG9mpo3-RR6gVYUJGMiYI",
  authDomain: "taskplanner-daily.firebaseapp.com",
  projectId: "taskplanner-daily",
  storageBucket: "taskplanner-daily.firebasestorage.app",
  messagingSenderId: "521965388557",
  appId: "1:521965388557:web:9fc9878603ab27d9366644",
  measurementId: "G-WTSHVWJMCS"
};

const app = initializeApp(firebaseConfig);

// --- CONFIGURE BACKEND API (FastAPI from earlier) ---
const API_BASE = "https://taskmanager.onrender.com"; // change to your deployed backend

// --- UI Elements ---
const form = document.getElementById("taskForm");
const titleEl = document.getElementById("title");
const deadlineEl = document.getElementById("deadline");
const importanceEl = document.getElementById("importance");
const impOut = document.getElementById("impOut");
const listEl = document.getElementById("taskList");
const top3El = document.getElementById("top3");
const estimateEl = document.getElementById("estimate");
const notifyBtn = document.getElementById("notifyBtn");
const notifyStatus = document.getElementById("notifyStatus");
const refreshBtn = document.getElementById("refreshBtn");
const installBtn = document.getElementById("installBtn");

// update slider output
importanceEl.addEventListener("input", () => impOut.textContent = importanceEl.value);

// --- Install prompt (PWA) ---
let deferredPrompt;
window.addEventListener("beforeinstallprompt", (e) => {
  e.preventDefault();
  deferredPrompt = e;
  installBtn.style.display = "inline-flex";
});
installBtn.addEventListener("click", async () => {
  if (!deferredPrompt) return;
  deferredPrompt.prompt();
  await deferredPrompt.userChoice;
  deferredPrompt = null;
  installBtn.style.display = "none";
});

// --- Fetch tasks and render ---
async function fetchTasks() {
  try {
    const r = await fetch(`${API_BASE}/tasks`);
    const data = await r.json();
    renderTasks(data);
  } catch (e) {
    listEl.innerHTML = `<div class="muted">Could not load tasks (check API_BASE)</div>`;
  }
}

function renderTasks(tasks) {
  // empty states
  if (!tasks || tasks.length === 0) {
    listEl.classList.add("empty");
    listEl.textContent = "No tasks yet.";
    top3El.classList.add("empty");
    top3El.textContent = "No tasks yet.";
    return;
  }

  // compute a simple priority score (matches your Phase-3 idea)
  const scored = tasks.map(t => {
    const daysLeft = Math.max(0.5, (new Date(t.deadline) - new Date()) / (1000*60*60*24));
    const importance = t.importance || 1;
    const predictedMinutes = t.predicted_minutes || 60;
    const score = (1/daysLeft) * importance * (1/predictedMinutes);
    return {...t, score};
  }).sort((a,b)=>b.score-a.score);

  // render all
  listEl.classList.remove("empty");
  listEl.innerHTML = scored.map(t => `
    <div class="item">
      <div>
        <div><strong>${t.title}</strong></div>
        <div class="muted">Due ${t.deadline || "—"}</div>
      </div>
      <div class="badge">⭐ ${t.importance}</div>
    </div>
  `).join("");

  // render top3
  const top3 = scored.filter(t=>t.status==='pending' || !t.status).slice(0,3);
  if (top3.length === 0){
    top3El.classList.add("empty");
    top3El.textContent = "No pending tasks.";
  } else {
    top3El.classList.remove("empty");
    top3El.innerHTML = top3.map(t => `
      <div class="item">
        <div>
          <div><strong>${t.title}</strong></div>
          <div class="muted">Est ~${t.predicted_minutes ?? 60} min • Due ${t.deadline || "—"}</div>
        </div>
        <div class="badge">Priority ${(t.score).toFixed(4)}</div>
      </div>
    `).join("");
  }
}

// --- Add task (POST to backend) ---
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    title: titleEl.value.trim(),
    deadline: deadlineEl.value,
    importance: parseInt(importanceEl.value, 10)
  };
  if (!payload.title || !payload.deadline) return;

  try {
    const r = await fetch(`${API_BASE}/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (r.ok) {
      titleEl.value = ""; deadlineEl.value = ""; importanceEl.value = 3; impOut.textContent = "3";
      await fetchTasks();
    } else {
      alert("Failed to add task");
    }
  } catch (e) {
    alert("Backend not reachable. Check API_BASE.");
  }
});

// --- Push notifications: request + register token with backend ---
const messagingSupported = await isSupported();
let messaging, fcmToken;

async function enablePush() {
  try {
    if (!messagingSupported) {
      notifyStatus.textContent = "Push not supported on this browser.";
      return;
    }
    messaging = getMessaging(app);

    // Get your Web Push certificate key from Firebase → Project Settings → Cloud Messaging → Web configuration
    const VAPID_KEY = "PASTE_YOUR_WEB_PUSH_CERTIFICATE_KEY_HERE";

    const perm = await Notification.requestPermission();
    if (perm !== "granted") {
      notifyStatus.textContent = "Permission denied.";
      return;
    }
    fcmToken = await getToken(messaging, { vapidKey: VAPID_KEY, serviceWorkerRegistration: await navigator.serviceWorker.ready });
    if (!fcmToken) {
      notifyStatus.textContent = "No token (permission problem).";
      return;
    }
    // register token to backend
    await fetch(`${API_BASE}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fcm_token: fcmToken })
    });
    notifyStatus.textContent = "Push enabled. Token registered.";
  } catch (e) {
    console.error(e);
    notifyStatus.textContent = "Failed to enable push.";
  }
}

notifyBtn.addEventListener("click", enablePush);

// foreground messages
if (messagingSupported) {
  // lazy init after user enables push; safe guard
  try {
    messaging = getMessaging(app);
    onMessage(messaging, (payload) => {
      // simple toast
      const msg = payload?.notification?.title ? `${payload.notification.title} — ${payload.notification.body || ""}` : "New notification";
      alert(msg);
    });
  } catch {}
}

// refresh button
refreshBtn.addEventListener("click", fetchTasks);

// simple (placeholder) estimate text
importanceEl.addEventListener("input", () => {
  const minutes = 20 + (6 - parseInt(importanceEl.value,10)) * 10; // dummy estimate
  estimateEl.textContent = `Estimated time: ~${minutes} min`;
});

// initial load
fetchTasks();
