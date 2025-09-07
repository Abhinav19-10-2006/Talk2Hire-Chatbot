const startBtn = document.getElementById("startBtn");
const sendBtn = document.getElementById("sendBtn");
const userInput = document.getElementById("userInput");
const chatbox = document.getElementById("chatbox");
const splash = document.getElementById("splash");
const chatContainer = document.getElementById("chat-container");

window.addEventListener("load", () => {
  // Show splash, then fade out
  setTimeout(() => {
    splash.style.opacity = "0";
    setTimeout(() => {
      splash.style.display = "none";
      chatContainer.classList.remove("hidden");
      chatContainer.style.opacity = "1";
    }, 1000);
  }, 1500); // splash visible for 1.5s
});

let currentQIndex = 0, currentRole = "", currentMode = "";

function addMessage(text, sender) {
  const msg = document.createElement("div");
  msg.classList.add("message", sender);
  msg.textContent = text;
  chatbox.appendChild(msg);
  chatbox.scrollTop = chatbox.scrollHeight;
}

// Backend base URL (adjust if your server runs elsewhere)
const BASE_URL = "http://127.0.0.1:8000";

startBtn.addEventListener("click", async () => {
  currentRole = document.getElementById("roleDropdown").value.trim().toLowerCase();
  currentMode = document.getElementById("modeDropdown").value.trim().toLowerCase();

  chatbox.innerHTML = "";
  currentQIndex = 0;

  try {
    const res = await fetch(`${BASE_URL}/start_interview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role: currentRole, mode: currentMode })
    });
    const data = await res.json();

    if (data.question) {
      addMessage(data.question, "bot");
    } else {
      addMessage("Error: Could not start interview.", "bot");
      console.error("Backend error:", data.error);
    }
  } catch (error) {
    addMessage("Error: Unable to connect to server.", "bot");
    console.error("Fetch error:", error);
  }
});

sendBtn.addEventListener("click", async () => {
  const answer = userInput.value.trim();
  if (!answer) return;

  addMessage(answer, "user");
  userInput.value = "";

  try {
    const res = await fetch(`${BASE_URL}/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        answer: answer,
        q_index: currentQIndex,
        role: currentRole,
        mode: currentMode,
      })
    });

    const data = await res.json();
    addMessage(data.feedback, "bot");

    if (data.next_question) {
      currentQIndex++;
      setTimeout(() => addMessage(data.next_question, "bot"), 1000);
    } else {
      addMessage("Interview finished! 🎉", "bot");
    }
  } catch (error) {
    addMessage("Error: Unable to connect to server.", "bot");
    console.error("Fetch error:", error);
  }
});

userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendBtn.click();
});
