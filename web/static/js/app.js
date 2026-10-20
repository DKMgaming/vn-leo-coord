/**
 * LEO-COORD Mission Control Frontend Application
 * Điều khiển Tab 1 (Bản đồ 3D & Phân tích chòm sao) & Tab 2 (Kho tham luận/tài liệu)
 */

let globe = null;
let allDocuments = [];
let activeFileTypeFilter = 'all';

document.addEventListener("DOMContentLoaded", () => {
    // 1. Khởi tạo đồng hồ thời gian thực UTC+7
    initClock();

    // 2. Khởi tạo quả cầu 3D
    initGlobe();

    // 3. Tải dữ liệu chòm sao mặc định & chạy đánh giá ban đầu
    loadDefaultConstellation();

    // 4. Tải danh sách tham luận tài liệu (Tab 2)
    loadDocuments();

    // 5. Khởi tạo sự kiện Drag & Drop tệp tin
    initDropZone();
});

/* ================= 1. CHUYỂN ĐỔI TAB ================= */
function switchTab(tabIndex) {
    const tab1Btn = document.getElementById("tab-btn-1");
    const tab2Btn = document.getElementById("tab-btn-2");
    const tab3Btn = document.getElementById("tab-btn-3");
    const pane1 = document.getElementById("tab-content-1");
    const pane2 = document.getElementById("tab-content-2");
    const pane3 = document.getElementById("tab-content-3");

    // Reset active state across all tabs
    [tab1Btn, tab2Btn, tab3Btn].forEach(btn => btn?.classList.remove("active"));
    [pane1, pane2, pane3].forEach(pane => pane?.classList.remove("active"));

    if (tabIndex === 1) {
        tab1Btn?.classList.add("active");
        pane1?.classList.add("active");
        if (globe) {
            setTimeout(() => globe.resize(), 100);
        }
    } else if (tabIndex === 2) {
        tab2Btn?.classList.add("active");
        pane2?.classList.add("active");
        loadDocuments();
    } else if (tabIndex === 3) {
        tab3Btn?.classList.add("active");
        pane3?.classList.add("active");
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

/* ================= 2. ĐỒNG HỒ THỜI GIAN THỰC ================= */
function initClock() {
    const el = document.getElementById("live-clock");
    const update = () => {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('vi-VN', { hour12: false });
        el.textContent = `${timeStr} (UTC+7)`;
    };
    update();
    setInterval(update, 1000);
}

/* ================= 3. KHỞI TẠO BẢN ĐỒ SỐ 3D ================= */
function initGlobe() {
    globe = new LeoGlobe3D("globe-canvas");

    // Lắng nghe sự kiện click vệ tinh trên quả cầu 3D
    window.onSatelliteSelected = (sat) => {
        const card = document.getElementById("sat-info-card");
        if (!sat) {
            card.style.display = "none";
            return;
        }
        card.style.display = "block";
        document.getElementById("info-sat-id").textContent = sat.id;
        document.getElementById("info-sat-plane").textContent = `Pl ${sat.plane} (inc ${globe.incDeg}°)`;
        document.getElementById("info-sat-coords").textContent = `${sat.lat > 0 ? sat.lat + '°N' : -sat.lat + '°S'}, ${sat.lon > 0 ? sat.lon + '°E' : -sat.lon + '°W'}`;
        document.getElementById("info-sat-alt").textContent = `${sat.alt_km || globe.altKm} km`;
    };
}

function togglePlayPause() {
    if (!globe) return;
    globe.isPlaying = !globe.isPlaying;
    const btn = document.getElementById("btn-play-pause");
    if (btn) btn.textContent = globe.isPlaying ? "⏸️ Dừng" : "▶️ Tiếp";
    const btnTimeline = document.getElementById("btn-timeline-play");
    if (btnTimeline) btnTimeline.textContent = globe.isPlaying ? "⏸️" : "▶️";
}

function onTimelineSliderChange(val) {
    if (!globe) return;
    globe.setSimTime(parseFloat(val));
}

function stepTime(deltaSec) {
    if (!globe) return;
    globe.setSimTime(globe.simTime + deltaSec);
}

function resetTime() {
    if (!globe) return;
    globe.setSimTime(0);
}

window.updateTimelineUI = function(simSeconds) {
    const slider = document.getElementById("timeline-slider");
    if (slider) slider.value = Math.floor(simSeconds);
    const clock = document.getElementById("timeline-clock");
    if (clock) {
        const hrs = String(Math.floor(simSeconds / 3600)).padStart(2, '0');
        const mins = String(Math.floor((simSeconds % 3600) / 60)).padStart(2, '0');
        const secs = String(Math.floor(simSeconds % 60)).padStart(2, '0');
        clock.textContent = `${hrs}:${mins}:${secs}`;
    }
};

function setSpeed(spd) {
    if (!globe) return;
    globe.simSpeed = spd;
    document.querySelectorAll(".btn-speed").forEach(b => b.classList.remove("active"));
    const activeBtn = Array.from(document.querySelectorAll(".btn-speed")).find(b => b.textContent.includes(spd + 'x'));
    if (activeBtn) activeBtn.classList.add("active");
}

/* ================= 4. ĐÁNH GIÁ CHÒM SAO LEO (TAB 1) ================= */
async function loadDefaultConstellation() {
    try {
        const res = await fetch("/api/constellation/default");
        if (res.ok) {
            const data = await res.json();
            document.getElementById("cfg-name").value = data.name || "DEMO_LEO_KU";
            document.getElementById("cfg-alt").value = data.alt_km || 550;
            document.getElementById("cfg-inc").value = data.inc_deg || 53.0;
            document.getElementById("cfg-sats").value = data.n_sats || 120;
            document.getElementById("cfg-planes").value = data.n_planes || 6;
            if (data.downlink) {
                document.getElementById("cfg-freq").value = data.downlink.freq_ghz || 11.7;
                document.getElementById("cfg-eirp").value = data.downlink.eirp_dbw_per_mhz || 10.0;
            }
            runAssessment();
        }
    } catch (e) {
        console.error("Lỗi nạp cấu hình mặc định:", e);
    }
}

async function runAssessment() {
    const btn = document.getElementById("btn-run-assess");
    const originalText = btn.innerHTML;
    btn.innerHTML = `<span>⏳ ĐANG PHÂN TÍCH VÀ TÍNH TOÁN...</span>`;
    btn.disabled = true;

    const payload = {
        name: document.getElementById("cfg-name").value,
        alt_km: parseFloat(document.getElementById("cfg-alt").value),
        inc_deg: parseFloat(document.getElementById("cfg-inc").value),
        n_sats: parseInt(document.getElementById("cfg-sats").value),
        n_planes: parseInt(document.getElementById("cfg-planes").value),
        freq_ghz: parseFloat(document.getElementById("cfg-freq").value),
        eirp_dbw_per_mhz: parseFloat(document.getElementById("cfg-eirp").value),
        gso_lon: parseFloat(document.getElementById("cfg-gso").value),
        biu_deadline: "2024-03-01"
    };

    // Cập nhật lên bản đồ 3D
    if (globe) {
        globe.setConstellationParams(payload.alt_km, payload.inc_deg, payload.n_sats, payload.n_planes);
    }

    try {
        const res = await fetch("/api/assess", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            const data = await res.json();
            renderAssessmentResults(data);
        } else {
            alert("Lỗi khi chạy đánh giá kỹ thuật!");
        }
    } catch (e) {
        console.error("Lỗi gọi API đánh giá:", e);
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

function renderAssessmentResults(data) {
    document.getElementById("res-timestamp").textContent = `Cập nhật lúc: ${data.generated_at}`;

    // 1. Phủ sóng tổng thể
    const covFraction = data.coverage.grid_summary.mean_fraction * 100;
    document.getElementById("stat-cov").textContent = `${covFraction.toFixed(1)}%`;

    // 2. PFD Article 21
    const pfdPass = data.pfd.compliant;
    const pfdEl = document.getElementById("stat-pfd");
    pfdEl.innerHTML = pfdPass ? `<span class="badge-pass">ĐẠT CHUẨN</span>` : `<span class="badge-fail">KHÔNG ĐẠT</span>`;
    document.getElementById("stat-pfd-margin").textContent = `Margin: ${data.pfd.margin_db.toFixed(1)} dB`;

    // 3. EPFD Article 22
    const epfdPass = data.epfd.screening_pass;
    const epfdEl = document.getElementById("stat-epfd");
    epfdEl.innerHTML = epfdPass ? `<span class="badge-pass">ĐẠT CHUẨN</span>` : `<span class="badge-fail">CẦN XEM XÉT</span>`;
    document.getElementById("stat-epfd-anchor").textContent = `Margin: ${data.epfd.margin_vs_anchor_db.toFixed(1)} dB (Ngưỡng 22.1A)`;

    // 4. Nguy cơ xí phần (Warehousing)
    const risk = data.warehousing.risk;
    const whEl = document.getElementById("stat-warehouse");
    if (risk === "THAP") {
        whEl.innerHTML = `<span class="badge-pass">THẤP</span>`;
    } else if (risk === "TRUNG_BINH") {
        whEl.innerHTML = `<span class="badge-warn">TRUNG BÌNH</span>`;
    } else {
        whEl.innerHTML = `<span class="badge-fail">CAO</span>`;
    }

    // 5. Bảng chi tiết 3 trạm Việt Nam
    const tbody = document.getElementById("station-tbody");
    tbody.innerHTML = "";
    (data.coverage.points || []).forEach(pt => {
        const tr = document.createElement("tr");
        let nameVN = pt.point === "hanoi" ? "Hà Nội" : (pt.point === "danang" ? "Đà Nẵng" : "TP. Hồ Chí Minh");
        tr.innerHTML = `
            <td><strong>${nameVN}</strong></td>
            <td><span class="text-green">${(pt.fraction_covered * 100).toFixed(1)}%</span></td>
            <td>${pt.mean_sats_visible.toFixed(1)} vệ tinh</td>
            <td>${pt.max_gap_min.toFixed(1)} phút</td>
        `;
        tbody.appendChild(tr);
    });

    // 6. Phối hợp NGSO vs GSO
    if (data.coordination) {
        const req = data.coordination.coordination_likely_required;
        const tag = document.getElementById("coord-req-tag");
        tag.className = req ? "badge-tag-red" : "badge-tag";
        tag.textContent = req ? "CẦN PHỐI HỢP VỚI GSO VN" : "CHƯA CẦN PHỐI HỢP";
        
        const minSep = data.coordination.per_point && data.coordination.per_point[0] ? data.coordination.per_point[0].min_separation_deg : 2.0;
        document.getElementById("coord-min-sep").textContent = `${minSep.toFixed(1)}°`;
    }

    // 7. Mốc Res 35
    const msTrack = document.getElementById("milestones-track");
    msTrack.innerHTML = "";
    (data.milestones || []).forEach(m => {
        const div = document.createElement("div");
        const isDat = m.status === "DAT";
        const isTre = m.status === "TRE_HAN";
        div.className = `step-card ${isDat ? 'success' : (isTre ? 'warning' : 'pending')}`;
        div.innerHTML = `
            <div class="step-badge">Mốc ${m.percent}%</div>
            <div class="step-due">Hạn: ${m.due}</div>
            <div class="step-target">Yêu cầu: ${m.required_n} vệ tinh</div>
            <div class="step-result ${isDat ? 'text-green' : (isTre ? 'text-amber' : 'text-muted')}">
                ${isDat ? 'ĐÃ ĐẠT (' + m.deployed_n + ' vt)' : (isTre ? 'TRỄ HẠN (' + m.deployed_n + ' vt)' : 'CHƯA ĐẾN HẠN')}
            </div>
        `;
        msTrack.appendChild(div);
    });
}

/* ================= 5. KHO THAM LUẬN & TÀI LIỆU (TAB 2) ================= */
async function loadDocuments() {
    try {
        const res = await fetch("/api/documents");
        if (res.ok) {
            allDocuments = await res.json();
            updateDocStats();
            filterDocuments();
        }
    } catch (e) {
        console.error("Lỗi nạp danh sách tài liệu:", e);
    }
}

function updateDocStats() {
    document.getElementById("doc-count-badge").textContent = allDocuments.length;
    document.getElementById("stat-total-docs").textContent = allDocuments.length;

    const pdfCount = allDocuments.filter(d => d.file_type === 'pdf').length;
    const wordCount = allDocuments.filter(d => ['doc', 'docx'].includes(d.file_type)).length;
    const excelCount = allDocuments.filter(d => ['xls', 'xlsx'].includes(d.file_type)).length;
    const pptCount = allDocuments.filter(d => ['ppt', 'pptx'].includes(d.file_type)).length;

    document.getElementById("stat-pdf-count").textContent = pdfCount;
    document.getElementById("stat-word-count").textContent = wordCount;
    document.getElementById("stat-excel-count").textContent = excelCount;
    document.getElementById("stat-ppt-count").textContent = pptCount;
}

function setDocFilterType(type, btn) {
    activeFileTypeFilter = type;
    document.querySelectorAll(".docs-toolbar .filter-pill").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    filterDocuments();
}

function filterDocuments() {
    const search = (document.getElementById("doc-search-input").value || "").toLowerCase().trim();
    const category = document.getElementById("doc-category-select").value;

    const filtered = allDocuments.filter(doc => {
        // Lọc theo từ khóa
        const matchSearch = !search || 
            (doc.title && doc.title.toLowerCase().includes(search)) ||
            (doc.author && doc.author.toLowerCase().includes(search)) ||
            (doc.summary && doc.summary.toLowerCase().includes(search));

        // Lọc theo định dạng file
        let matchType = true;
        if (activeFileTypeFilter === 'pdf') matchType = doc.file_type === 'pdf';
        else if (activeFileTypeFilter === 'word') matchType = ['doc', 'docx'].includes(doc.file_type);
        else if (activeFileTypeFilter === 'excel') matchType = ['xls', 'xlsx'].includes(doc.file_type);
        else if (activeFileTypeFilter === 'ppt') matchType = ['ppt', 'pptx'].includes(doc.file_type);

        // Lọc theo chủ đề
        const matchCat = category === 'all' || doc.category === category;

        return matchSearch && matchType && matchCat;
    });

    renderDocumentsGrid(filtered);
}

function renderDocumentsGrid(docs) {
    const grid = document.getElementById("documents-grid");
    grid.innerHTML = "";

    if (docs.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 4rem 1rem; color: var(--text-muted);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
                <div style="font-size: 1.1rem; color: var(--text-primary); margin-bottom: 0.5rem;">Không tìm thấy tài liệu nào phù hợp</div>
                <div style="font-size: 0.85rem;">Hãy thử tìm kiếm với từ khóa khác hoặc nhấn "Tải Lên Mới" để bổ sung tham luận.</div>
            </div>
        `;
        return;
    }

    docs.forEach(doc => {
        const card = document.createElement("div");
        card.className = "doc-card";

        // Định dạng icon và style theo loại file
        let extClass = doc.file_type;
        let iconSymbol = "📄";
        let extLabel = doc.file_type.toUpperCase();

        if (doc.file_type === 'pdf') {
            iconSymbol = "📕";
            extLabel = "PDF";
        } else if (['doc', 'docx'].includes(doc.file_type)) {
            iconSymbol = "📘";
            extLabel = "WORD";
        } else if (['xls', 'xlsx'].includes(doc.file_type)) {
            iconSymbol = "📊";
            extLabel = "EXCEL";
        } else if (['ppt', 'pptx'].includes(doc.file_type)) {
            iconSymbol = "📽️";
            extLabel = "PPTX";
        }

        const sizeStr = formatFileSize(doc.file_size || 0);

        card.innerHTML = `
            <div>
                <div class="doc-card-top">
                    <div class="file-type-icon-box ${extClass}">${iconSymbol}</div>
                    <div class="doc-main-info">
                        <div class="doc-category-tag">${escapeHtml(doc.category || 'Tài liệu chuyên đề')}</div>
                        <h3 class="doc-title">${escapeHtml(doc.title)}</h3>
                        <div class="doc-meta">
                            <span>👤 ${escapeHtml(doc.author || 'Tác giả')}</span>
                            <span>📅 ${doc.upload_date || ''}</span>
                        </div>
                    </div>
                </div>
                <p class="doc-summary">${escapeHtml(doc.summary || 'Không có mô tả tóm tắt.')}</p>
            </div>

            <div class="doc-footer">
                <div class="doc-size-box">
                    <span class="ext-badge ${extClass}">${extLabel}</span>
                    <span>${sizeStr}</span>
                </div>
                <div class="doc-actions">
                    <button class="btn-card-read" onclick="openReaderModal('${doc.id}')" title="Xem toàn văn nội dung & góp ý chuyên môn">
                        <span>📖 Xem & Góp Ý</span>
                    </button>
                    <a href="/api/documents/${doc.id}/download" class="btn-card-action" title="Tải xuống tệp tin">
                        <span>⬇️ Tải Về</span>
                    </a>
                    <button class="btn-card-danger" onclick="deleteDocument('${doc.id}')" title="Xóa tài liệu">
                        🗑️
                    </button>
                </div>
            </div>
        `;
        grid.appendChild(card);
    });
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function escapeHtml(text) {
    if (!text) return "";
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/* ================= 6. TẢI LÊN TÀI LIỆU (UPLOAD MODAL) ================= */
function openUploadModal() {
    document.getElementById("upload-modal").classList.add("active");
}

function closeUploadModal() {
    document.getElementById("upload-modal").classList.remove("active");
    clearSelectedFile();
    document.getElementById("upload-form").reset();
    document.getElementById("upload-progress-box").style.display = "none";
}

function closeModalOnBackdrop(e) {
    if (e.target.id === "upload-modal") {
        closeUploadModal();
    }
}

function initDropZone() {
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");

    ['dragenter', 'dragover'].forEach(name => {
        dropZone.addEventListener(name, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add("dragover");
        });
    });

    ['dragleave', 'drop'].forEach(name => {
        dropZone.addEventListener(name, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove("dragover");
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            fileInput.files = files;
            handleFileSelect(fileInput);
        }
    });
}

function handleFileSelect(input) {
    if (!input.files || input.files.length === 0) return;
    const file = input.files[0];
    const previewBox = document.getElementById("file-preview-box");
    const nameEl = document.getElementById("preview-name");
    const sizeEl = document.getElementById("preview-size");
    const iconEl = document.getElementById("preview-icon");

    nameEl.textContent = file.name;
    sizeEl.textContent = `(${formatFileSize(file.size)})`;

    const ext = file.name.split('.').pop().toLowerCase();
    if (ext === 'pdf') iconEl.textContent = "📕";
    else if (['doc', 'docx'].includes(ext)) iconEl.textContent = "📘";
    else if (['xls', 'xlsx'].includes(ext)) iconEl.textContent = "📊";
    else if (['ppt', 'pptx'].includes(ext)) iconEl.textContent = "📽️";
    else iconEl.textContent = "📄";

    previewBox.style.display = "flex";

    // Tự động điền tiêu đề nếu chưa có
    const titleInput = document.getElementById("doc-title");
    if (!titleInput.value) {
        const base = file.name.substring(0, file.name.lastIndexOf('.')) || file.name;
        titleInput.value = base.replace(/[_-]/g, ' ');
    }
}

function clearSelectedFile() {
    document.getElementById("file-input").value = "";
    document.getElementById("file-preview-box").style.display = "none";
}

async function handleFormUpload(e) {
    e.preventDefault();
    const fileInput = document.getElementById("file-input");
    if (!fileInput.files || fileInput.files.length === 0) {
        alert("Vui lòng chọn một tệp tin (Word, Excel, PDF hoặc PPTX)!");
        return;
    }

    const formData = new FormData(document.getElementById("upload-form"));
    const pBox = document.getElementById("upload-progress-box");
    const pBar = document.getElementById("upload-bar");
    const pText = document.getElementById("upload-status-text");
    const btnSubmit = document.getElementById("btn-submit-upload");

    pBox.style.display = "block";
    pBar.style.width = "40%";
    pText.textContent = "Đang xử lý tệp tin và trích xuất dữ liệu...";
    btnSubmit.disabled = true;

    try {
        pBar.style.width = "75%";
        const res = await fetch("/api/documents/upload", {
            method: "POST",
            body: formData
        });

        pBar.style.width = "100%";
        if (res.ok) {
            pText.textContent = "Tải lên thành công!";
            setTimeout(() => {
                closeUploadModal();
                loadDocuments();
            }, 600);
        } else {
            const err = await res.json();
            alert("Lỗi tải lên: " + (err.detail || "Không thể lưu tệp!"));
            pBox.style.display = "none";
        }
    } catch (err) {
        alert("Lỗi kết nối khi tải lên: " + err.message);
        pBox.style.display = "none";
    } finally {
        btnSubmit.disabled = false;
    }
}

async function deleteDocument(docId) {
    if (!confirm("Bạn có chắc chắn muốn xóa bài tham luận này khỏi hệ thống?")) return;
    try {
        const res = await fetch(`/api/documents/${docId}`, { method: "DELETE" });
        if (res.ok) {
            loadDocuments();
        } else {
            alert("Không thể xóa tài liệu!");
        }
    } catch (e) {
        console.error("Lỗi xóa tài liệu:", e);
    }
}

/* ================= 7. ĐỌC NỘI DUNG & ĐÓNG GÓP Ý KIẾN THAM LUẬN ================= */
let activeReaderDocId = null;

async function openReaderModal(docId) {
    activeReaderDocId = docId;
    const doc = allDocuments.find(d => d.id === docId);
    if (!doc) return;

    const modal = document.getElementById("reader-modal");
    modal.classList.add("active");

    document.getElementById("reader-modal-title").textContent = doc.title;
    document.getElementById("reader-meta-author").textContent = `👤 Tác giả: ${doc.author || 'Chưa rõ'}`;
    document.getElementById("reader-meta-category").textContent = `🏷️ Chủ đề: ${doc.category || 'Tài liệu'}`;
    document.getElementById("reader-summary-text").textContent = doc.summary || 'Không có mô tả tóm tắt.';
    document.getElementById("reader-download-link").href = `/api/documents/${doc.id}/download`;
    document.getElementById("feedback-doc-id").value = docId;

    const viewer = document.getElementById("reader-text-viewer");
    viewer.innerHTML = '<div style="text-align: center; color: var(--cyan-accent); padding: 2rem;">⏳ Đang tải toàn văn tài liệu...</div>';

    // 1. Nạp nội dung toàn văn
    try {
        const res = await fetch(`/api/documents/${docId}/content`);
        if (res.ok) {
            const data = await res.json();
            viewer.innerHTML = formatMarkdownText(data.content || "Nội dung tệp trống hoặc đang được cập nhật.");
        } else {
            viewer.innerHTML = "<div style='padding: 2rem; text-align: center; color: var(--text-muted);'>Không thể tải nội dung xem trước trực tiếp. Bạn có thể nhấn '⬇️ Tải Tệp Gốc' phía trên để mở trong Word/Excel/PDF.</div>";
        }
    } catch (e) {
        viewer.innerHTML = "<div style='color: var(--red-fail); padding: 1rem;'>Lỗi nạp nội dung: " + escapeHtml(e.message) + "</div>";
    }

    // 2. Nạp luồng góp ý
    loadDocFeedback(docId);
}

function formatMarkdownText(text) {
    if (!text) return '<div class="text-muted" style="text-align: center; padding: 2rem;">Tệp tin không có nội dung văn bản.</div>';
    let safe = escapeHtml(text);
    // Heading 1 (# ...)
    safe = safe.replace(/^#\s+(.+)$/gm, '<h2 class="reader-h1">$1</h2>');
    // Heading 2 (## ...)
    safe = safe.replace(/^##\s+(.+)$/gm, '<h3 class="reader-h2">$1</h3>');
    // Heading 3 (### ...)
    safe = safe.replace(/^###\s+(.+)$/gm, '<h4 class="reader-h3">$1</h4>');
    // Bold (**...**)
    safe = safe.replace(/\*\*(.+?)\*\*/g, '<strong style="color: #ffffff;">$1</strong>');
    // Bullet list items (- ...)
    safe = safe.replace(/^[\-\*]\s+(.+)$/gm, '<div class="reader-bullet">• $1</div>');
    // Links [text](url)
    safe = safe.replace(/\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g, '<a href="$2" target="_blank" class="reader-link" style="color: #38bdf8; text-decoration: underline;">$1 ↗</a>');
    // Paragraph breaks
    safe = safe.replace(/\n\n+/g, '<div style="height: 12px;"></div>');
    return safe;
}

function closeReaderModal() {
    const modal = document.getElementById("reader-modal");
    if (modal) modal.classList.remove("active");
    activeReaderDocId = null;
}

function closeReaderModalOnBackdrop(e) {
    if (e.target.id === "reader-modal") {
        closeReaderModal();
    }
}

async function loadDocFeedback(docId) {
    const threadList = document.getElementById("feedback-thread-list");
    const countBadge = document.getElementById("feedback-count");
    threadList.innerHTML = '<div style="color: var(--text-muted); font-size: 0.8rem; text-align: center; padding: 1rem;">Đang tải góp ý...</div>';

    try {
        const res = await fetch(`/api/documents/${docId}/feedback`);
        if (res.ok) {
            const comments = await res.json();
            countBadge.textContent = comments.length;
            if (comments.length === 0) {
                threadList.innerHTML = `
                    <div style="text-align: center; color: var(--text-muted); font-size: 0.8rem; padding: 2rem 1rem;">
                        <div style="font-size: 1.8rem; margin-bottom: 0.5rem;">💡</div>
                        Chưa có ý kiến góp ý nào cho tham luận này.<br>Hãy là người đầu tiên đóng góp chuyên môn!
                    </div>
                `;
                return;
            }

            threadList.innerHTML = "";
            comments.forEach(c => {
                const item = document.createElement("div");
                item.className = "feedback-item";
                item.innerHTML = `
                    <div class="feedback-item-header">
                        <div>
                            <span class="feedback-item-author">${escapeHtml(c.author)}</span>
                            ${c.organization ? `<span class="feedback-item-org">(${escapeHtml(c.organization)})</span>` : ''}
                        </div>
                        <span class="feedback-item-time">${c.created_at || ''}</span>
                    </div>
                    <div class="feedback-badge">${escapeHtml(c.rating || 'Góp ý')}</div>
                    <div class="feedback-item-comment">${escapeHtml(c.comment)}</div>
                `;
                threadList.appendChild(item);
            });
        }
    } catch (e) {
        threadList.innerHTML = '<div style="color: var(--red-fail); font-size: 0.8rem;">Lỗi tải góp ý.</div>';
    }
}

async function submitFeedback(e) {
    e.preventDefault();
    const docId = document.getElementById("feedback-doc-id").value;
    if (!docId) return;

    const author = document.getElementById("fb-author").value.trim();
    const org = document.getElementById("fb-org").value.trim();
    const rating = document.getElementById("fb-rating").value;
    const comment = document.getElementById("fb-comment").value.trim();

    if (!author || !comment) {
        alert("Vui lòng điền họ tên và nội dung ý kiến!");
        return;
    }

    const btn = document.getElementById("btn-submit-feedback");
    btn.disabled = true;
    btn.innerHTML = "<span>Đang gửi ý kiến...</span>";

    try {
        const res = await fetch(`/api/documents/${docId}/feedback`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ author, organization: org, rating, comment })
        });

        if (res.ok) {
            document.getElementById("fb-comment").value = "";
            loadDocFeedback(docId);
        } else {
            const err = await res.json();
            alert("Lỗi: " + (err.detail || "Không thể gửi ý kiến!"));
        }
    } catch (e) {
        alert("Lỗi kết nối: " + e.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = "<span>Gửi Ý Kiến Góp Ý</span>";
    }
}

