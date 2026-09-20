function submitLogin() {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!username || !password) {
        document.getElementById("loginError").classList.remove("d-none");
        document.getElementById("loginError").innerText = "⚠️ Please fill all fields!";
        return;
    }

    fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            window.location.href = "/dashboard";
        } else {
            document.getElementById("loginError").classList.remove("d-none");
            document.getElementById("loginError").innerText = "❌ Invalid username or password";
        }
    });
  
   
}
document.addEventListener("DOMContentLoaded", function() {
        document.addEventListener("keypress", function(e) {
            if (e.key === "Enter") {
                const modal = document.getElementById("loginModal");
                if (modal.classList.contains("show")) {
                    submitLogin();
                }
            }
        });
    });