const API_BASE = "https://final-project-w7ms.onrender.com/api/v1";

// Demo gate device API key (created once via POST /devices for the demo gym)
const GATE_API_KEY = "hheE0byUpDUFre06_zVKG_82eiQZvWlkqINP-BaG7Ns";

const loginSection = document.getElementById("login-section");
const app = document.getElementById("app");
const loginStatus = document.getElementById("login-status");
const loginForm = document.getElementById("login-form");
const loginMessage = document.getElementById("login-message");
const logoutBtn = document.getElementById("logout-btn");

let occupancyInterval = null;

function getToken() {
  return localStorage.getItem("access_token");
}

function authHeaders() {
  return { "Authorization": "Bearer " + getToken() };
}

function showApp() {
  loginSection.classList.add("hidden");
  app.classList.remove("hidden");
  logoutBtn.classList.remove("hidden");
  loginStatus.textContent = "Logged in";
  loadMembers();
  loadPlans();
  loadLogs();
  loadOccupancy();
  if (!occupancyInterval) {
    occupancyInterval = setInterval(loadOccupancy, 5000);
  }
}

function showLogin() {
  if (occupancyInterval) {
    clearInterval(occupancyInterval);
    occupancyInterval = null;
  }
  localStorage.removeItem("access_token");
  localStorage.removeItem("gym_id");
  app.classList.add("hidden");
  logoutBtn.classList.add("hidden");
  loginSection.classList.remove("hidden");
  loginStatus.textContent = "";
}

logoutBtn.addEventListener("click", showLogin);

// Register new gym + admin
const registerSection = document.getElementById("register-section");
const registerForm = document.getElementById("register-form");
const registerMessage = document.getElementById("register-message");
const showRegisterLink = document.getElementById("show-register-link");
const showLoginLink = document.getElementById("show-login-link");

showRegisterLink.addEventListener("click", (e) => {
  e.preventDefault();
  loginSection.classList.add("hidden");
  registerSection.classList.remove("hidden");
});

showLoginLink.addEventListener("click", (e) => {
  e.preventDefault();
  registerSection.classList.add("hidden");
  loginSection.classList.remove("hidden");
});

registerForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const body = {
    gym_name: document.getElementById("reg-gym-name").value,
    gym_address: document.getElementById("reg-gym-address").value,
    gym_phone: document.getElementById("reg-gym-phone").value,
    gym_email: document.getElementById("reg-gym-email").value,
    gym_max_capacity: parseInt(document.getElementById("reg-gym-capacity").value, 10),
    admin_full_name: document.getElementById("reg-admin-name").value,
    admin_email: document.getElementById("reg-admin-email").value,
    admin_password: document.getElementById("reg-admin-password").value
  };

  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    const data = await res.json();

    if (!res.ok) {
      registerMessage.textContent = data.detail || "Could not register gym";
      registerMessage.className = "error";
      return;
    }

    registerMessage.textContent = "Gym registered! You can now log in.";
    registerMessage.className = "success";
    registerForm.reset();
    document.getElementById("reg-gym-capacity").value = 100;

    setTimeout(() => {
      registerSection.classList.add("hidden");
      loginSection.classList.remove("hidden");
      registerMessage.textContent = "";
    }, 1500);
  } catch (err) {
    registerMessage.textContent = "Could not connect to server";
    registerMessage.className = "error";
  }
});

// Wrapper around fetch that logs out automatically if the token is rejected
async function apiFetch(url, options = {}) {
  const res = await fetch(url, options);
  if (res.status === 401) {
    showLogin();
    loginMessage.textContent = "Session expired, please log in again";
    loginMessage.className = "error";
  }
  return res;
}

// On page load, check if already logged in
if (getToken()) {
  showApp();
}

// Login
loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();

    if (!res.ok) {
      loginMessage.textContent = data.detail || "Login failed";
      loginMessage.className = "error";
      return;
    }

    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("gym_id", data.gym_id);
    loginMessage.textContent = "";
    showApp();
  } catch (err) {
    loginMessage.textContent = "Could not connect to server";
    loginMessage.className = "error";
  }
});

// Member registration
const memberForm = document.getElementById("member-form");
const memberMessage = document.getElementById("member-message");

memberForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  if (!memberForm.reportValidity()) {
    return;
  }

  // Date of birth must be in the past and within a reasonable age range
  const dob = new Date(document.getElementById("member-dob").value);
  const age = (Date.now() - dob.getTime()) / (1000 * 60 * 60 * 24 * 365.25);
  if (dob > new Date() || age > 120) {
    memberMessage.textContent = "Please enter a valid date of birth";
    memberMessage.className = "error";
    return;
  }

  const body = {
    first_name: document.getElementById("member-first-name").value,
    last_name: document.getElementById("member-last-name").value,
    email: document.getElementById("member-email").value,
    phone: document.getElementById("member-phone").value,
    date_of_birth: document.getElementById("member-dob").value || null,
    emergency_contact: document.getElementById("member-emergency").value
  };

  try {
    const res = await apiFetch(`${API_BASE}/members`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(body)
    });
    const data = await res.json();

    if (!res.ok) {
      memberMessage.textContent = data.detail || "Could not add member";
      memberMessage.className = "error";
      return;
    }

    memberMessage.textContent = "Member added: " + data.first_name + " " + data.last_name;
    memberMessage.className = "success";
    memberForm.reset();
    loadMembers();
  } catch (err) {
    memberMessage.textContent = "Could not connect to server";
    memberMessage.className = "error";
  }
});

// Load members into all member select dropdowns
async function loadMembers() {
  const selectIds = ["qr-member-select", "sub-member-select", "status-member-select"];
  const selects = selectIds.map((id) => document.getElementById(id));
  selects.forEach((s) => (s.innerHTML = ""));

  try {
    const res = await apiFetch(`${API_BASE}/members`, {
      headers: authHeaders()
    });
    const data = await res.json();
    const members = data.items || data;

    members.forEach((m) => {
      selects.forEach((select) => {
        const option = document.createElement("option");
        option.value = m.id;
        option.textContent = `${m.first_name} ${m.last_name} (${m.email})`;
        select.appendChild(option);
      });
    });
  } catch (err) {
    console.error("Could not load members", err);
  }
}

// Plan id -> plan object, used to show plan names in subscription history
let plansById = {};

// Load plans into the subscription plan dropdown
async function loadPlans() {
  const select = document.getElementById("sub-plan-select");
  select.innerHTML = "";

  try {
    const res = await apiFetch(`${API_BASE}/plans`, {
      headers: authHeaders()
    });
    const data = await res.json();
    const plans = data.items || data;

    plansById = {};
    plans.forEach((p) => { plansById[p.id] = p; });

    plans.forEach((p) => {
      const option = document.createElement("option");
      option.value = p.id;
      option.textContent = `${p.name} (${p.duration_days} days, ${p.price})`;
      select.appendChild(option);
    });
  } catch (err) {
    console.error("Could not load plans", err);
  }
}

// Plan creation
const planForm = document.getElementById("plan-form");
const planMessage = document.getElementById("plan-message");

planForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const body = {
    name: document.getElementById("plan-name").value,
    description: document.getElementById("plan-description").value || null,
    duration_days: parseInt(document.getElementById("plan-duration").value, 10),
    price: parseFloat(document.getElementById("plan-price").value)
  };

  try {
    const res = await apiFetch(`${API_BASE}/plans`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(body)
    });
    const data = await res.json();

    if (!res.ok) {
      planMessage.textContent = data.detail || "Could not create plan";
      planMessage.className = "error";
      return;
    }

    planMessage.textContent = `Plan created: ${data.name}`;
    planMessage.className = "success";
    planForm.reset();
    document.getElementById("plan-duration").value = 30;
    document.getElementById("plan-price").value = 500;
    loadPlans();
  } catch (err) {
    planMessage.textContent = "Could not connect to server";
    planMessage.className = "error";
  }
});

// Subscription assignment
const subscriptionForm = document.getElementById("subscription-form");
const subscriptionMessage = document.getElementById("subscription-message");

subscriptionForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const memberId = document.getElementById("sub-member-select").value;
  const body = {
    plan_id: document.getElementById("sub-plan-select").value,
    start_date: document.getElementById("sub-start-date").value
  };

  if (!memberId || !body.plan_id) {
    subscriptionMessage.textContent = "Please select a member and a plan first";
    subscriptionMessage.className = "error";
    return;
  }

  try {
    const res = await apiFetch(`${API_BASE}/members/${memberId}/subscriptions`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(body)
    });
    const data = await res.json();

    if (!res.ok) {
      subscriptionMessage.textContent = data.detail || "Could not assign plan";
      subscriptionMessage.className = "error";
      return;
    }

    subscriptionMessage.textContent = `Plan assigned (ends: ${data.end_date})`;
    subscriptionMessage.className = "success";
  } catch (err) {
    subscriptionMessage.textContent = "Could not connect to server";
    subscriptionMessage.className = "error";
  }
});

// Subscription status check
const statusCheckBtn = document.getElementById("status-check-btn");
const subscriptionStatus = document.getElementById("subscription-status");

statusCheckBtn.addEventListener("click", async () => {
  const memberId = document.getElementById("status-member-select").value;
  if (!memberId) return;

  subscriptionStatus.textContent = "Loading...";

  try {
    const res = await apiFetch(`${API_BASE}/members/${memberId}/subscriptions`, {
      headers: authHeaders()
    });
    const data = await res.json();
    const subs = data.items || data;

    if (!subs.length) {
      subscriptionStatus.textContent = "No plan has been assigned to this member yet";
      return;
    }

    subscriptionStatus.innerHTML = subs.map((sub) => {
      const plan = plansById[sub.plan_id];
      const planName = plan ? plan.name : "Unknown plan";
      return `
        <div class="subscription-record">
          Plan: <strong>${planName}</strong><br>
          Status: <strong>${sub.status}</strong><br>
          Start: ${sub.start_date}<br>
          End: ${sub.end_date}
        </div>
      `;
    }).join("<hr>");
  } catch (err) {
    subscriptionStatus.textContent = "Could not load subscription info";
  }
});

// QR code generation
const qrGenerateBtn = document.getElementById("qr-generate-btn");
const qrResult = document.getElementById("qr-result");

qrGenerateBtn.addEventListener("click", async () => {
  const memberId = document.getElementById("qr-member-select").value;
  if (!memberId) return;

  qrResult.innerHTML = "Generating...";

  try {
    const res = await apiFetch(`${API_BASE}/members/${memberId}/credentials/qr`, {
      method: "POST",
      headers: authHeaders()
    });
    const data = await res.json();

    if (!res.ok) {
      qrResult.innerHTML = `<p class="error">${data.detail || "Could not generate QR code"}</p>`;
      return;
    }

    qrResult.innerHTML = `<img src="data:image/png;base64,${data.qr_base64}" alt="QR Code">`;
  } catch (err) {
    qrResult.innerHTML = `<p class="error">Could not connect to server</p>`;
  }
});

// Access logs
const refreshLogsBtn = document.getElementById("refresh-logs-btn");
refreshLogsBtn.addEventListener("click", loadLogs);

async function loadLogs() {
  const tbody = document.querySelector("#logs-table tbody");
  tbody.innerHTML = "";

  try {
    const res = await apiFetch(`${API_BASE}/access-logs`, {
      headers: authHeaders()
    });
    const data = await res.json();
    const logs = data.items || data;

    logs.forEach((log) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${new Date(log.scanned_at).toLocaleString()}</td>
        <td>${log.gate_id}</td>
        <td>${log.credential_type}</td>
        <td>${log.action}</td>
        <td>${log.decision}</td>
      `;
      tbody.appendChild(row);
    });
  } catch (err) {
    console.error("Could not load logs", err);
  }
}

// Occupancy
async function loadOccupancy() {
  const text = document.getElementById("occupancy-text");

  try {
    const res = await apiFetch(`${API_BASE}/occupancy`, {
      headers: authHeaders()
    });
    const data = await res.json();

    if (!res.ok) {
      text.textContent = "Could not load occupancy info";
      return;
    }

    text.textContent = `${data.current_occupancy} / ${data.max_capacity} (${data.utilization_percentage}%)`;
  } catch (err) {
    text.textContent = "Could not load occupancy info";
  }
}

// Gate / turnstile QR scanner
const gateStartBtn = document.getElementById("gate-start-btn");
const gateStopBtn = document.getElementById("gate-stop-btn");
const gateResult = document.getElementById("gate-result");
let qrScanner = null;

gateStartBtn.addEventListener("click", async () => {
  gateResult.textContent = "";
  gateResult.className = "";
  qrScanner = new Html5Qrcode("qr-reader");

  try {
    await qrScanner.start(
      { facingMode: "environment" },
      { fps: 10, qrbox: 200 },
      onQrScanned,
      (errorMessage) => console.log("scan error:", errorMessage) // debug
    );
    gateStartBtn.classList.add("hidden");
    gateStopBtn.classList.remove("hidden");
  } catch (err) {
    gateResult.textContent = "Could not open camera: " + err;
    gateResult.className = "denied";
  }
});

gateStopBtn.addEventListener("click", stopScanner);

async function stopScanner() {
  if (qrScanner) {
    await qrScanner.stop();
    qrScanner.clear();
    qrScanner = null;
  }
  gateStartBtn.classList.remove("hidden");
  gateStopBtn.classList.add("hidden");
}

async function onQrScanned(decodedText) {
  await stopScanner();

  const gateId = document.getElementById("gate-id").value || "Main Entrance";
  const action = document.getElementById("gate-action").value;

  try {
    const res = await fetch(`${API_BASE}/verify`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": GATE_API_KEY
      },
      body: JSON.stringify({
        credential_type: "qr",
        credential_value: decodedText,
        gate_id: gateId,
        action: action
      })
    });
    const data = await res.json();
    showGateResult(data);
    loadLogs();
    loadOccupancy();
  } catch (err) {
    gateResult.textContent = "Verification request failed";
    gateResult.className = "denied";
  }
}

function showGateResult(data) {
  if (data.decision === "GRANTED") {
    gateResult.className = "granted";
    gateResult.innerHTML = `
      <strong>Access Granted ✅</strong><br>
      Member: ${data.member.name}<br>
      Plan: ${data.member.membership_tier}<br>
      Visits this month: ${data.member.visits_this_month}<br>
      Occupancy: ${data.gym_occupancy.current} / ${data.gym_occupancy.max}
    `;
  } else {
    gateResult.className = "denied";
    gateResult.innerHTML = `
      <strong>Access Denied ❌</strong><br>
      Reason: ${data.decision}
      ${data.flag_reason ? `<br>Note: ${data.flag_reason}` : ""}
    `;
  }
}

