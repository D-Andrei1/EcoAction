/* app.js - small helpers used on every page.
PROVIDED COMPLETE - type it in exactly and do not change it. */
(function () {
    "use strict";
    var meta = document.querySelector('meta[name="csrf-token"]');
    var csrfToken = meta ? meta.getAttribute("content") : "";
    // Send JSON to our own API. Gives back a promise of {ok, status, data}.
    // api("/api/calc/preview", {category: "transport", actionType: "cycling", quantity: 8, unit: "km"})
    // .then(function (result) { if (result.ok) { ... result.data ... } });
    window.api = function (path, payload, method) {
        return fetch(path, {
            method: method || "POST",
            headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken },
            body: payload === undefined ? undefined : JSON.stringify(payload),
            credentials: "same-origin"
        }).then(function (response) {
            return response.json().catch(function () { return {}; }).then(function (data) {
                return { ok: response.ok, status: response.status, data: data };
            });
        }).catch(function () {
            return { ok: false, status: 0, data: { error: "Couldn't reach the app. Check it is still running." } };
        });
    };
    // Show a message in the corner from JavaScript: showToast("Saved", "success")
    window.showToast = function (message, kind) {
        var box = document.getElementById("toasts");
        var toast = document.createElement("div");
        kind = kind || "info";
        toast.className = "toast toast-" + kind;
        toast.setAttribute("role", kind === "error" ? "alert" : "status");
        var text = document.createElement("span");
        text.textContent = message;
        var close = document.createElement("button");
        close.type = "button";
        close.className = "toast-close";
        close.setAttribute("aria-label", "Dismiss message");
        close.innerHTML = "&times;";
        toast.appendChild(text);
        toast.appendChild(close);
        box.appendChild(toast);
        if (kind !== "error") { setTimeout(function () { toast.remove(); }, 6000); }
    };
    // Forms: "Are you sure?" questions and stopping double submits.
    // A form with data-js="1" is handled by its own page script instead.
    document.addEventListener("submit", function (event) {
        var form = event.target;
        if (form.getAttribute("data-js") === "1") { return; }
        var question = form.getAttribute("data-confirm");
        if (question && !window.confirm(question)) { event.preventDefault(); return; }
        if (form.getAttribute("data-busy") === "1") { event.preventDefault(); return; }
        form.setAttribute("data-busy", "1");
        var buttons = form.querySelectorAll('button[type="submit"]');
        for (var i = 0; i < buttons.length; i++) {
            buttons[i].disabled = true;
            buttons[i].setAttribute("aria-busy", "true");
        }
    });
    // When someone comes back with the Back button, switch buttons on again.
    window.addEventListener("pageshow", function () {
        var forms = document.querySelectorAll('form[data-busy="1"]');
        for (var i = 0; i < forms.length; i++) {
            forms[i].removeAttribute("data-busy");
            var buttons = forms[i].querySelectorAll("button[disabled]");
            for (var j = 0; j < buttons.length; j++) {
                buttons[j].disabled = false;
                buttons[j].removeAttribute("aria-busy");
            }
        }
    });
    // Filter forms with data-autosubmit="1" update as soon as a choice changes.
    document.addEventListener("change", function (event) {
        var form = event.target.form;
        if (form && form.getAttribute("data-autosubmit") === "1") { form.submit(); }
    });
    document.addEventListener("click", function (event) {
        var target = event.target;
        if (target.classList.contains("toast-close")) { target.parentNode.remove(); }
        var opener = target.closest("[data-open-modal]");
        if (opener) { document.getElementById(opener.getAttribute("data-open-modal")).showModal(); }
        if (target.hasAttribute("data-close-modal")) { target.closest("dialog").close(); }
    });
    // Success messages disappear by themselves; error messages stay until dismissed.
    var toasts = document.querySelectorAll(".toasts .toast:not(.toast-error)");
    for (var k = 0; k < toasts.length; k++) {
        (function (t) { setTimeout(function () { t.remove(); }, 6000); })(toasts[k]);
    }
})();