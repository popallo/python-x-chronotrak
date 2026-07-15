(function () {
    const token = document.querySelector('meta[name="csrf-token"]')?.content || "";
    window.csrfToken = token;
})();
