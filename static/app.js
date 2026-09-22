document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const urlInput = document.getElementById("urlInput");
    const btnPaste = document.getElementById("btnPaste");
    const btnClear = document.getElementById("btnClear");
    const btnCheck = document.getElementById("btnCheck");
    const btnStartDownload = document.getElementById("btnStartDownload");
    const qualitySelect = document.getElementById("qualitySelect");

    const videoPreview = document.getElementById("videoPreview");
    const previewThumb = document.getElementById("previewThumb");
    const previewTitle = document.getElementById("previewTitle");
    const previewUploader = document.getElementById("previewUploader");
    const previewDetails = document.getElementById("previewDetails");
    const previewLiveBadge = document.getElementById("previewLiveBadge");

    const serverIp = document.getElementById("serverIp");
    const storagePath = document.getElementById("storagePath");
    const storageSpace = document.getElementById("storageSpace");
    const cookiesStatus = document.getElementById("cookiesStatus");

    const activeTasksList = document.getElementById("activeTasksList");
    const activeCount = document.getElementById("activeCount");
    const emptyActive = document.getElementById("emptyActive");

    const historyList = document.getElementById("historyList");
    const emptyHistory = document.getElementById("emptyHistory");
    const btnRefreshHistory = document.getElementById("btnRefreshHistory");

    // Modals
    const modalConnect = document.getElementById("modalConnect");
    const btnConnect = document.getElementById("btnConnect");
    const qrCodeImg = document.getElementById("qrCodeImg");
    const accessUrlText = document.getElementById("accessUrlText");
    const btnCopyUrl = document.getElementById("btnCopyUrl");

    const modalSettings = document.getElementById("modalSettings");
    const btnSettings = document.getElementById("btnSettings");
    const cfgSaveDir = document.getElementById("cfgSaveDir");
    const cfgAutoSubfolder = document.getElementById("cfgAutoSubfolder");
    const cfgDefaultQuality = document.getElementById("cfgDefaultQuality");
    const cfgTeleToken = document.getElementById("cfgTeleToken");
    const cfgTeleChatId = document.getElementById("cfgTeleChatId");
    const btnTestTele = document.getElementById("btnTestTele");
    const teleMsgResult = document.getElementById("teleMsgResult");
    const cookiesContent = document.getElementById("cookiesContent");
    const btnSaveCookies = document.getElementById("btnSaveCookies");
    const cookiesMsgResult = document.getElementById("cookiesMsgResult");
    const btnSaveAllSettings = document.getElementById("btnSaveAllSettings");
    const btnCancelSettings = document.getElementById("btnCancelSettings");

    let currentLanUrl = window.location.origin;

    function showToast(message, type = "info") {
        const container = document.getElementById("toastContainer");
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        
        const icons = { success: "✅", error: "❌", info: "ℹ️" };
        toast.innerHTML = `<span>${icons[type] || "ℹ️"}</span> <span>${message}</span>`;
        
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateY(20px)";
            toast.style.transition = "all 0.3s ease";
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    async function loadServerInfo() {
        try {
            const res = await fetch("/api/info");
            const data = await res.json();
            if (data) {
                currentLanUrl = window.location.origin;
                serverIp.textContent = "Cloud 24/7";
                accessUrlText.textContent = currentLanUrl;
                
                if (data.cloud_mode) {
                    storagePath.textContent = data.cloud_mode;
                }
                if (data.free_gb) {
                    storageSpace.textContent = `${data.free_gb} GB trống`;
                }

                if (data.has_cookies) {
                    cookiesStatus.textContent = "Đã nạp";
                    cookiesStatus.className = "badge badge-success";
                } else {
                    cookiesStatus.textContent = "Chưa có";
                    cookiesStatus.className = "badge";
                }

                const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(currentLanUrl)}`;
                qrCodeImg.src = qrUrl;
            }
        } catch (e) {
            serverIp.textContent = "Mất kết nối";
            serverIp.className = "status-value text-danger";
        }
    }

    btnPaste.addEventListener("click", async () => {
        try {
            if (navigator.clipboard && navigator.clipboard.readText) {
                const text = await navigator.clipboard.readText();
                if (text) {
                    urlInput.value = text.trim();
                    showToast("Đã dán link!", "info");
                    triggerCheckInfo(text.trim(), false);
                }
            } else {
                urlInput.focus();
                showToast("Nhấn giữ để dán vào ô nhập!", "info");
            }
        } catch (e) {
            urlInput.focus();
        }
    });

    btnClear.addEventListener("click", () => {
        urlInput.value = "";
        videoPreview.classList.add("hidden");
    });

    async function triggerCheckInfo(url, isManual = false) {
        if (!url || !url.includes("youtu")) return;
        btnCheck.disabled = true;
        btnCheck.innerHTML = `<span class="icon">⏳</span> Đang kiểm tra...`;

        try {
            const res = await fetch("/api/check", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url: url, quality: qualitySelect.value })
            });
            const data = await res.json();
            if (data && data.success) {
                previewTitle.textContent = data.title;
                previewUploader.textContent = `👤 ${data.uploader}`;
                
                let detailsText = "";
                if (data.resolution) detailsText += `Độ phân giải: ${data.resolution} `;
                if (data.fps) detailsText += `(${data.fps}fps) `;
                previewDetails.textContent = detailsText;

                if (data.thumbnail) {
                    previewThumb.src = data.thumbnail;
                }

                if (data.is_live) {
                    previewLiveBadge.classList.remove("hidden");
                } else {
                    previewLiveBadge.classList.add("hidden");
                }

                videoPreview.classList.remove("hidden");
                if (isManual) showToast("Đã nhận diện thông tin video!", "success");
            } else {
                if (isManual) showToast(data.error || "Không lấy được thông tin video.", "error");
            }
        } catch (e) {
            if (isManual) showToast("Lỗi khi kiểm tra link.", "error");
        } finally {
            btnCheck.disabled = false;
            btnCheck.innerHTML = `<span class="icon">🔍</span> Kiểm Tra Link`;
        }
    }

    btnCheck.addEventListener("click", () => {
        const url = urlInput.value.trim();
        if (!url) {
            showToast("Vui lòng nhập link YouTube!", "error");
            return;
        }
        triggerCheckInfo(url, true);
    });

    urlInput.addEventListener("paste", () => {
        setTimeout(() => {
            const url = urlInput.value.trim();
            if (url) triggerCheckInfo(url, false);
        }, 100);
    });

    btnStartDownload.addEventListener("click", async () => {
        const url = urlInput.value.trim();
        if (!url) {
            showToast("Vui lòng nhập URL YouTube!", "error");
            urlInput.focus();
            return;
        }

        btnStartDownload.disabled = true;
        btnStartDownload.innerHTML = `<span class="icon">⏳</span> Đang gửi lệnh...`;

        try {
            const res = await fetch("/api/download", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    url: url,
                    quality: qualitySelect.value
                })
            });
            const data = await res.json();
            if (data && data.success) {
                showToast("🚀 Đã nhận lệnh tải ngầm trên Cloud! Bạn có thể tắt máy / tắt web thoải mái.", "success");
                urlInput.value = "";
                videoPreview.classList.add("hidden");
                loadTasks();
            } else {
                showToast(data.detail || data.message || "Lỗi khi bắt đầu tải.", "error");
            }
        } catch (e) {
            showToast("Không thể kết nối đến Cloud server.", "error");
        } finally {
            btnStartDownload.disabled = false;
            btnStartDownload.innerHTML = `<span class="icon">🚀</span> BẮT ĐẦU TẢI NGẦM`;
        }
    });

    async function stopTask(taskId) {
        if (!confirm("Bạn có chắc chắn muốn dừng tác vụ này? Phần video đã tải sẽ được ghép lại.")) {
            return;
        }
        try {
            const res = await fetch("/api/stop", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ task_id: taskId })
            });
            const data = await res.json();
            if (data && data.success) {
                showToast("Đã gửi yêu cầu dừng! Đang ghép dữ liệu...", "info");
                loadTasks();
            } else {
                showToast(data.detail || "Không thể dừng tác vụ.", "error");
            }
        } catch (e) {
            showToast("Lỗi gửi yêu cầu dừng.", "error");
        }
    }

    function renderTasks(tasks) {
        const active = (tasks || []).filter(t => ["pending", "checking", "downloading", "merging", "uploading"].includes(t.status));
        activeCount.textContent = active.length;

        if (active.length === 0) {
            emptyActive.classList.remove("hidden");
            activeTasksList.innerHTML = "";
            activeTasksList.appendChild(emptyActive);
            return;
        }

        emptyActive.classList.add("hidden");
        activeTasksList.innerHTML = "";

        active.forEach(t => {
            const card = document.createElement("div");
            card.className = "task-card glass-card";

            const isIndeterminate = (t.progress_percent < 0 || t.status === "merging" || t.status === "uploading");
            const pct = isIndeterminate ? 100 : Math.max(0, Math.min(100, t.progress_percent || 0));

            let statusBadge = `<span class="badge badge-success">Đang tải</span>`;
            if (t.is_live) statusBadge = `<span class="badge badge-live">🔴 LIVE</span>`;
            if (t.status === "merging") statusBadge = `<span class="badge" style="background: rgba(245, 158, 11, 0.2); color: #f59e0b;">🎬 Đang ghép file</span>`;
            if (t.status === "uploading") statusBadge = `<span class="badge" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8;">☁️ Đẩy lên Drive</span>`;

            card.innerHTML = `
                <div class="task-header">
                    <div style="flex: 1; min-width: 0;">
                        <div class="task-title" title="${t.title || t.url}">${t.title || t.url}</div>
                        <div class="task-meta">👤 ${t.uploader || "Cloud Worker"} • 🎯 ${t.quality}</div>
                    </div>
                    <div>${statusBadge}</div>
                </div>

                <div class="progress-container">
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill ${isIndeterminate ? 'indeterminate' : ''}" style="width: ${pct}%;"></div>
                    </div>
                </div>

                <div class="task-stats">
                    <span>⚡ Tốc độ: <strong>${t.speed_str || "0 MB/s"}</strong></span>
                    <span>💾 Đã tải: <strong>${t.downloaded_str || "0 MB"}</strong> / ${t.total_str || "--"}</span>
                </div>

                <div class="task-footer">
                    <span class="task-status-text">${t.status_text || "Đang xử lý..."}</span>
                    <button class="btn btn-small btn-danger" onclick="window._stopTask('${t.id}')">🛑 Dừng</button>
                </div>
            `;
            activeTasksList.appendChild(card);
        });
    }

    window._stopTask = stopTask;

    async function loadTasks() {
        try {
            const res = await fetch("/api/tasks");
            const tasks = await res.json();
            renderTasks(tasks);
        } catch (e) {}
    }

    function setupWebSocket() {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws/tasks`;
        let ws;

        try {
            ws = new WebSocket(wsUrl);
            ws.onmessage = (event) => {
                try {
                    const tasks = JSON.parse(event.data);
                    renderTasks(tasks);
                } catch (e) {}
            };
            ws.onerror = () => startPolling();
            ws.onclose = () => setTimeout(setupWebSocket, 5000);
        } catch (e) {
            startPolling();
        }
    }

    let pollingInterval = null;
    function startPolling() {
        if (!pollingInterval) {
            pollingInterval = setInterval(loadTasks, 2500);
        }
    }

    async function loadHistory() {
        try {
            const res = await fetch("/api/history");
            const list = await res.json();
            renderHistory(list);
        } catch (e) {}
    }

    function renderHistory(list) {
        if (!list || list.length === 0) {
            emptyHistory.classList.remove("hidden");
            historyList.innerHTML = "";
            historyList.appendChild(emptyHistory);
            return;
        }

        emptyHistory.classList.add("hidden");
        historyList.innerHTML = "";

        list.slice(0, 25).forEach(item => {
            const div = document.createElement("div");
            div.className = "history-item";

            const isSuccess = item.status === "completed";
            const badgeClass = isSuccess ? "badge-success" : (item.status === "stopped" ? "badge" : "badge-live");
            const statusLabel = isSuccess ? "Hoàn tất" : (item.status === "stopped" ? "Đã dừng" : "Lỗi");

            const dateStr = item.finished_at ? new Date(item.finished_at).toLocaleString("vi-VN") : item.created_at;

            let actionBtn = "";
            if (item.web_link) {
                actionBtn = `<a href="${item.web_link}" target="_blank" class="btn btn-small btn-primary" style="margin-right: 6px;">📁 Xem Drive</a>`;
            } else if (item.download_url) {
                actionBtn = `<a href="${item.download_url}" download class="btn btn-small btn-secondary" style="margin-right: 6px;">⬇️ Tải về</a>`;
            }

            div.innerHTML = `
                <div class="history-info">
                    <div class="history-title" title="${item.title}">${item.title || item.url}</div>
                    <div class="history-sub">
                        <span>${dateStr}</span> • <span>${item.quality}</span>
                    </div>
                </div>
                <div class="history-meta-right" style="display: flex; align-items: center; gap: 8px;">
                    ${actionBtn}
                    <div class="history-size">${item.file_size_str || "--"}</div>
                    <span class="badge ${badgeClass}">${statusLabel}</span>
                    <button class="btn-inline" onclick="window._deleteHistory('${item.id}')" title="Xóa">✕</button>
                </div>
            `;
            historyList.appendChild(div);
        });
    }

    window._deleteHistory = async (id) => {
        try {
            await fetch(`/api/history/${id}`, { method: "DELETE" });
            loadHistory();
        } catch (e) {}
    };

    btnRefreshHistory.addEventListener("click", loadHistory);

    btnConnect.addEventListener("click", () => {
        modalConnect.classList.remove("hidden");
    });

    btnCopyUrl.addEventListener("click", () => {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(currentLanUrl);
            showToast("Đã sao chép link trang web!", "success");
        }
    });

    btnSettings.addEventListener("click", async () => {
        modalSettings.classList.remove("hidden");
        try {
            const res = await fetch("/api/config");
            const cfg = await res.json();
            cfgDefaultQuality.value = cfg.default_quality || "1080p (Full HD)";
            cfgTeleToken.value = cfg.telegram_token || "";
            cfgTeleChatId.value = cfg.telegram_chat_id || "";

            const cRes = await fetch("/api/cookies");
            const cData = await cRes.json();
            cookiesContent.value = cData.content || "";
        } catch (e) {}
    });

    document.querySelectorAll(".modal-close, #btnCancelSettings").forEach(btn => {
        btn.addEventListener("click", () => {
            modalConnect.classList.add("hidden");
            modalSettings.classList.add("hidden");
        });
    });

    btnSaveAllSettings.addEventListener("click", async () => {
        try {
            const res = await fetch("/api/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    default_quality: cfgDefaultQuality.value,
                    telegram_token: cfgTeleToken.value.trim(),
                    telegram_chat_id: cfgTeleChatId.value.trim(),
                })
            });
            const data = await res.json();
            if (data.success) {
                showToast("Đã lưu cài đặt!", "success");
                modalSettings.classList.add("hidden");
                loadServerInfo();
            }
        } catch (e) {
            showToast("Lỗi lưu cài đặt.", "error");
        }
    });

    btnTestTele.addEventListener("click", async () => {
        teleMsgResult.textContent = "Đang gửi thử...";
        try {
            await fetch("/api/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    telegram_token: cfgTeleToken.value.trim(),
                    telegram_chat_id: cfgTeleChatId.value.trim(),
                })
            });

            const res = await fetch("/api/test-telegram", { method: "POST" });
            const data = await res.json();
            if (data.success) {
                teleMsgResult.textContent = "✅ Gửi thành công!";
                teleMsgResult.style.color = "var(--success)";
            } else {
                teleMsgResult.textContent = "❌ Lỗi: " + (data.detail || "Gửi thất bại");
                teleMsgResult.style.color = "var(--danger)";
            }
        } catch (e) {
            teleMsgResult.textContent = "❌ Không kết nối được";
            teleMsgResult.style.color = "var(--danger)";
        }
    });

    btnSaveCookies.addEventListener("click", async () => {
        cookiesMsgResult.textContent = "Đang lưu...";
        try {
            const res = await fetch("/api/cookies", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ content: cookiesContent.value })
            });
            const data = await res.json();
            if (data.success) {
                cookiesMsgResult.textContent = "✅ Đã lưu cookies!";
                cookiesMsgResult.style.color = "var(--success)";
                loadServerInfo();
            }
        } catch (e) {
            cookiesMsgResult.textContent = "❌ Lỗi lưu cookies";
            cookiesMsgResult.style.color = "var(--danger)";
        }
    });

    loadServerInfo();
    loadTasks();
    loadHistory();
    setupWebSocket();
    setInterval(loadHistory, 10000);
});
