document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("uploadForm");
    const fileInput = document.getElementById("document");
    const dropzone = document.getElementById("dropzone");
    const fileLabel = document.getElementById("fileLabel");
    const fileSelected = document.getElementById("fileSelected");
    const generateButton = document.getElementById("generateButton");
    const loadingState = document.getElementById("loadingState");
    const mobileMenu = document.getElementById("mobileMenu");
    const sidebar = document.getElementById("sidebar");

    const MAX_FILE_SIZE = 10 * 1024 * 1024;
    const ALLOWED_EXTENSIONS = ["pdf", "txt"];

    function getExtension(filename) {
        const parts = filename.split(".");
        return parts.length > 1
            ? parts.pop().toLowerCase()
            : "";
    }

    function formatFileSize(bytes) {
        if (bytes < 1024) {
            return `${bytes} B`;
        }

        if (bytes < 1024 * 1024) {
            return `${(bytes / 1024).toFixed(1)} KB`;
        }

        return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    }

    function showFile(file) {
        if (!file) {
            return false;
        }

        const extension = getExtension(file.name);

        if (!ALLOWED_EXTENSIONS.includes(extension)) {
            alert("Please select a PDF or TXT file.");
            fileInput.value = "";
            resetFileDisplay();
            return false;
        }

        if (file.size > MAX_FILE_SIZE) {
            alert("The file is too large. The maximum size is 10 MB.");
            fileInput.value = "";
            resetFileDisplay();
            return false;
        }

        fileLabel.innerHTML = "Document selected";

        fileSelected.textContent =
            `${file.name} · ${formatFileSize(file.size)}`;

        fileSelected.hidden = false;
        return true;
    }

    function resetFileDisplay() {
        fileLabel.innerHTML =
            'Drop your file here, or <span>browse</span>';

        fileSelected.textContent = "";
        fileSelected.hidden = true;
    }

    if (fileInput) {
        fileInput.addEventListener("change", () => {
            if (fileInput.files.length > 0) {
                showFile(fileInput.files[0]);
            } else {
                resetFileDisplay();
            }
        });
    }

    if (dropzone && fileInput) {
        ["dragenter", "dragover"].forEach((eventName) => {
            dropzone.addEventListener(eventName, (event) => {
                event.preventDefault();
                dropzone.classList.add("drag-over");
            });
        });

        ["dragleave", "dragend", "drop"].forEach((eventName) => {
            dropzone.addEventListener(eventName, (event) => {
                event.preventDefault();
                dropzone.classList.remove("drag-over");
            });
        });

        dropzone.addEventListener("drop", (event) => {
            const files = event.dataTransfer.files;

            if (!files.length) {
                return;
            }

            const file = files[0];
            const extension = getExtension(file.name);

            if (
                !ALLOWED_EXTENSIONS.includes(extension) ||
                file.size > MAX_FILE_SIZE
            ) {
                alert(
                    "Choose a PDF or TXT file no larger than 10 MB."
                );
                return;
            }

            const transfer = new DataTransfer();
            transfer.items.add(file);
            fileInput.files = transfer.files;

            showFile(file);
        });
    }

    if (form) {
        form.addEventListener("submit", (event) => {
            if (!fileInput || !fileInput.files.length) {
                event.preventDefault();
                alert("Please select a PDF or TXT document.");
                return;
            }

            const subject = document.getElementById("subject");

            if (subject && !subject.value.trim()) {
                event.preventDefault();
                subject.focus();
                alert("Please enter a subject or topic.");
                return;
            }

            if (generateButton) {
                generateButton.disabled = true;

                const label = generateButton.querySelector(".button-label");

                if (label) {
                    label.textContent = "Preparing materials...";
                }
            }

            if (loadingState) {
                loadingState.hidden = false;
            }
        });
    }

    if (mobileMenu && sidebar) {
        mobileMenu.addEventListener("click", () => {
            const isOpen = sidebar.classList.toggle("open");

            mobileMenu.setAttribute(
                "aria-expanded",
                String(isOpen)
            );
        });

        sidebar.querySelectorAll(".nav-link").forEach((link) => {
            link.addEventListener("click", () => {
                sidebar.classList.remove("open");
                mobileMenu.setAttribute("aria-expanded", "false");
            });
        });

        document.addEventListener("click", (event) => {
            const clickedInsideSidebar = sidebar.contains(event.target);
            const clickedMenuButton = mobileMenu.contains(event.target);

            if (!clickedInsideSidebar && !clickedMenuButton) {
                sidebar.classList.remove("open");
                mobileMenu.setAttribute("aria-expanded", "false");
            }
        });
    }

    function printReport() {
        window.print();
    }

    const printButton = document.getElementById("printButton");
    const printButtonBottom = document.getElementById("printButtonBottom");

    if (printButton) {
        printButton.addEventListener("click", printReport);
    }

    if (printButtonBottom) {
        printButtonBottom.addEventListener("click", printReport);
    }

    const resultSection = document.getElementById("results");

    if (resultSection) {
        const url = new URL(window.location.href);

        if (url.searchParams.get("showResults") === "1") {
            resultSection.scrollIntoView({
                behavior: "smooth",
                block: "start",
            });
        }
    }

    // Mark the current navigation destination.
    const navLinks = document.querySelectorAll(".nav-link");

    navLinks.forEach((link) => {
        link.addEventListener("click", () => {
            navLinks.forEach((item) => {
                item.classList.remove("active");
            });

            link.classList.add("active");
        });
    });
});
