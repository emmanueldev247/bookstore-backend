// ======================================
// GLOBAL STATE
// ======================================
let socket = null;
let jwtToken = null;

// ======================================
// UTILITY: Append a line to the Log
// ======================================
function log(message, isError = false) {
  const logEl = document.getElementById("log");
  const timeEl = document.createElement("time");
  timeEl.textContent = new Date().toLocaleTimeString();
  const msgEl = document.createElement("div");
  if (isError) {
    msgEl.style.color = "#e74c3c";
    console.error("[LOG ERROR]", message);
  } else {
    console.log("[LOG]", message);
  }
  msgEl.appendChild(timeEl);
  msgEl.insertAdjacentText("beforeend", ` ${message}`);
  logEl.appendChild(msgEl);
  logEl.scrollTop = logEl.scrollHeight;
}

// ======================================
// ON PAGE LOAD: check localStorage for a token
// ======================================
window.addEventListener("DOMContentLoaded", () => {
  const storedToken = localStorage.getItem("jwtToken");
  if (storedToken) {
    console.log("Found token in localStorage:", storedToken);
    jwtToken = storedToken;
    // Hide login card, show order-card immediately
    document.getElementById("login-card").classList.add("hidden");
    document.getElementById("order-card").classList.remove("hidden");
    document.getElementById("logout-button").classList.remove("hidden");
    log("✅ Found existing login token. You can Connect WebSocket.");
  }
});

// ======================================
// HANDLE LOGIN
// ======================================
const loginButton = document.getElementById("login-button");
loginButton.addEventListener("click", async () => {
  // Clear previous error
  const loginErrorEl = document.getElementById("login-error");
  loginErrorEl.textContent = "";
  loginErrorEl.classList.add("hidden");

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  if (!email || !password) {
    loginErrorEl.textContent = "Both email and password are required.";
    loginErrorEl.classList.remove("hidden");
    return;
  }

  loginButton.disabled = true;
  loginButton.classList.add("loading");

  try {
    console.log("Attempting login with:", { email });
    const res = await fetch(`http://${location.hostname}:5000/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });

    const data = await res.json();
    console.log("Login response:", data);

    if (!res.ok) {
      const errMsg = data.error || data.msg || "Login failed.";
      loginErrorEl.textContent = errMsg;
      loginErrorEl.classList.remove("hidden");
      return;
    }

    // Successful login: server returns { data: { access_token: "<JWT>" }, ... }
    jwtToken = data.data.access_token;
    console.log("JWT Token received:", jwtToken);

    if (!jwtToken) {
      loginErrorEl.textContent = "No token received from server.";
      loginErrorEl.classList.remove("hidden");
      return;
    }

    // Store token in localStorage for persistence across reloads
    localStorage.setItem("jwtToken", jwtToken);
    console.log("Stored JWT in localStorage");

    // Hide login card and show order notification UI
    document.getElementById("login-card").classList.add("hidden");
    document.getElementById("order-card").classList.remove("hidden");
    document.getElementById("logout-button").classList.remove("hidden");

    log("✅ Login successful. Ready to connect WebSocket.");
  } catch (err) {
    loginErrorEl.textContent = "Network or server error. Please try again.";
    loginErrorEl.classList.remove("hidden");
    console.error(err);
  } finally {
    loginButton.disabled = false;
    loginButton.classList.remove("loading");
  }
});

// ======================================
// HANDLE LOGOUT
// ======================================
document.getElementById("logout-button").addEventListener("click", () => {
  // If WebSocket is connected, disconnect first
  if (socket && socket.connected) {
    socket.io.opts.autoConnect = false; // Prevent auto-reconnect
    socket.disconnect();
    log("🔌 WebSocket disconnected.");
  }

  // Clear token from localStorage & memory
  localStorage.removeItem("jwtToken");
  jwtToken = null;
  console.log("Cleared JWT from localStorage");

  // Reset UI: hide order-card, show login-card
  document.getElementById("order-card").classList.add("hidden");
  document.getElementById("login-card").classList.remove("hidden");
  document.getElementById("logout-button").classList.add("hidden");

  // Reset Subscribe/Unsubscribe buttons
  document.getElementById("subscribe-button").classList.remove("hidden");
  document.getElementById("unsubscribe-button").classList.add("hidden");

  // Clear log contents
  document.getElementById("log").innerHTML = "";
  log("🔒 Logged out successfully.");
});

// ======================================
// CONNECT TO WEBSOCKET
// ======================================
document.getElementById("connect-button").addEventListener("click", () => {
  if (!jwtToken) {
    log("❗ You must log in first.", true);
    return;
  }
  if (socket && socket.connected) {
    log("ℹ️ Already connected to WebSocket.");
    return;
  }

  // Construct URL with query string for JWT
  const wsUrl = `http://${location.hostname}:5000/api/ws/orders?token=${jwtToken}`;
  console.log("Connecting to WebSocket at:", wsUrl);

  socket = io(wsUrl, {
    transports: ["websocket"],
    path: "/socket.io",
  });

  // Show/Hide Connect ↔ Disconnect buttons
  document.getElementById("connect-button").classList.add("hidden");
  document.getElementById("disconnect-button").classList.remove("hidden");

  socket.on("connect", () => {
    log("✅ Connected to server (Socket.IO).");
  });

  socket.on("connect_error", (err) => {
    log("❌ Connection failed: " + err.message, true);
    // Revert buttons if connection fails
    document.getElementById("connect-button").classList.remove("hidden");
    document.getElementById("disconnect-button").classList.add("hidden");
  });

  // Custom events from server
  socket.on("connected", (data) => {
    log("Server: " + (data.msg || JSON.stringify(data)));
  });

  socket.on("subscribed", (data) => {
    log("Subscribed: " + (data.msg || JSON.stringify(data)));
    // Swap Subscribe ↔ Unsubscribe buttons
    document.getElementById("subscribe-button").classList.add("hidden");
    document.getElementById("unsubscribe-button").classList.remove("hidden");
  });

  socket.on("order_status_update", (data) => {
    log("📦 Order Update: " + JSON.stringify(data));
  });

  socket.on("unsubscribed", (data) => {
    log("Unsubscribed: " + (data.msg || JSON.stringify(data)));
    // Swap back buttons
    document.getElementById("subscribe-button").classList.remove("hidden");
    document.getElementById("unsubscribe-button").classList.add("hidden");
  });

  socket.on("disconnect", () => {
    log("🔌 WebSocket disconnected by server, user or network.");
    document.getElementById("connect-button").classList.remove("hidden");
    document.getElementById("disconnect-button").classList.add("hidden");
  });
});

// ======================================
// DISCONNECT FROM WEBSOCKET
// ======================================
document.getElementById("disconnect-button").addEventListener("click", () => {
  if (socket && socket.connected) {
    socket.io.opts.autoConnect = false;
    socket.disconnect();
    log("🔌 WebSocket disconnected by user.");
  }
  document.getElementById("connect-button").classList.remove("hidden");
  document.getElementById("disconnect-button").classList.add("hidden");
});

// ======================================
// SUBSCRIBE TO A SPECIFIC ORDER
// ======================================
document.getElementById("subscribe-button").addEventListener("click", () => {
  const orderId = document.getElementById("order_id").value.trim();
  if (!socket || !socket.connected) {
    log("❗ You must connect the WebSocket first.", true);
    return;
  }

  if (!orderId) {
    log("❗ Please enter a valid Order ID.", true);
    return;
  }

  console.log("Emitting order_status_subscribe for order:", orderId);
  socket.emit("order_status_subscribe", { order_id: orderId });
});

// ======================================
// UNSUBSCRIBE FROM A SPECIFIC ORDER
// ======================================
document.getElementById("unsubscribe-button").addEventListener("click", () => {
  const orderId = document.getElementById("order_id").value.trim();
  if (!socket || !socket.connected) {
    log("❗ You must connect the WebSocket first.", true);
    return;
  }

  if (!orderId) {
    log("❗ Please enter a valid Order ID.", true);
    return;
  }

  console.log("Emitting order_status_unsubscribe for order:", orderId);
  socket.emit("order_status_unsubscribe", { order_id: orderId });
});
