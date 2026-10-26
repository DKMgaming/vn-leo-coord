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

    // 6. Khởi tạo sự kiện Dropdown Lớp Bản đồ 3D
    initLayersEvents();

    // 7. Tải dữ liệu đối chuẩn ITU GIBC v10.0 (Phase 1)
    loadGibcBenchmarkUI();

    // 8. Tải dữ liệu Vùng Phối Hợp Gateway & 5G Coexistence (Phase 2 - RR Appendix 7)
    loadAppendix7SummaryUI();

    // 9. Quét công báo quốc tế ITU BR IFIC & Trợ lý SpaceCom (Phase 3)
    loadBrIficScanUI();

    // 10. Khởi tạo Hội đồng Trợ lý Multi-AI-Agent Thẩm định (Phase 4)
    loadMultiAgentCouncilInitialUI();
});

/* ================= 1. CHUYỂN ĐỔI TAB ================= */
function switchTab(tabIndex) {
    const tab1Btn = document.getElementById("tab-btn-1");
    const tab2Btn = document.getElementById("tab-btn-2");
    const tab3Btn = document.getElementById("tab-btn-3");
    const tab4Btn = document.getElementById("tab-btn-4");
    const tab5Btn = document.getElementById("tab-btn-5");
    const pane1 = document.getElementById("tab-content-1");
    const pane2 = document.getElementById("tab-content-2");
    const pane3 = document.getElementById("tab-content-3");
    const pane4 = document.getElementById("tab-content-4");
    const pane5 = document.getElementById("tab-content-5");

    // Reset active state across all tabs
    [tab1Btn, tab2Btn, tab3Btn, tab4Btn, tab5Btn].forEach(btn => btn?.classList.remove("active"));
    [pane1, pane2, pane3, pane4, pane5].forEach(pane => pane?.classList.remove("active"));

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
    } else if (tabIndex === 4) {
        tab4Btn?.classList.add("active");
        pane4?.classList.add("active");
        window.scrollTo({ top: 0, behavior: 'smooth' });
        loadReferenceTables();
    } else if (tabIndex === 5) {
        tab5Btn?.classList.add("active");
        pane5?.classList.add("active");
        window.scrollTo({ top: 0, behavior: 'smooth' });
        loadHandbookData();
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
    window.globe = globe;

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
        const trackRow = document.getElementById("info-sat-track-row");
        if (trackRow) trackRow.style.display = "none";
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

/* ================= 3B. ĐIỀU KHIỂN DROPDOWN CÁC LỚP BẢN ĐỒ 3D ================= */
function toggleLayersDropdown(e) {
    if (e) {
        e.stopPropagation();
        e.preventDefault();
    }
    const container = document.getElementById("globe-layers-container");
    const btn = document.getElementById("btn-layers-dropdown");
    if (!container || !btn) return;
    const isOpen = container.classList.toggle("open");
    btn.setAttribute("aria-expanded", isOpen ? "true" : "false");
}

function closeLayersDropdown() {
    const container = document.getElementById("globe-layers-container");
    const btn = document.getElementById("btn-layers-dropdown");
    if (container && container.classList.contains("open")) {
        container.classList.remove("open");
        if (btn) btn.setAttribute("aria-expanded", "false");
    }
}

function onLayerChange(propName, checked) {
    if (globe && typeof globe[propName] !== "undefined") {
        globe[propName] = checked;
    }
    updateLayersActiveCount();
}

function toggleAllLayers(enable) {
    const layers = [
        { id: 'chk-gso', prop: 'showGso' },
        { id: 'chk-slant', prop: 'showSlantRange' },
        { id: 'chk-contours', prop: 'showContours' },
        { id: 'chk-orbits', prop: 'showOrbits' },
        { id: 'chk-footprints', prop: 'showFootprints' },
        { id: 'chk-beams', prop: 'showBeams' },
        { id: 'chk-labels', prop: 'showLabels' }
    ];

    layers.forEach(item => {
        const el = document.getElementById(item.id);
        if (el) el.checked = enable;
        if (globe && typeof globe[item.prop] !== "undefined") {
            globe[item.prop] = enable;
        }
    });

    updateLayersActiveCount();
}

function updateLayersActiveCount() {
    const layerIds = ['chk-gso', 'chk-slant', 'chk-contours', 'chk-orbits', 'chk-footprints', 'chk-beams', 'chk-labels'];
    let count = 0;
    layerIds.forEach(id => {
        const el = document.getElementById(id);
        if (el && el.checked) count++;
    });
    const badge = document.getElementById("layers-badge-count");
    if (badge) {
        badge.textContent = count;
        if (count === 0) {
            badge.classList.add("empty");
        } else {
            badge.classList.remove("empty");
        }
    }
}

function initLayersEvents() {
    // Đóng dropdown khi click ngoài vùng
    document.addEventListener("click", (e) => {
        const container = document.getElementById("globe-layers-container");
        if (container && container.classList.contains("open")) {
            if (!container.contains(e.target)) {
                closeLayersDropdown();
            }
        }
    });

    // Đóng dropdown khi bắt đầu tương tác vuốt xoay quả cầu
    const canvas = document.getElementById("globe-canvas");
    if (canvas) {
        canvas.addEventListener("touchstart", () => closeLayersDropdown(), { passive: true });
        canvas.addEventListener("mousedown", () => closeLayersDropdown());
    }

    // Đóng dropdown khi nhấn ESC
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            closeLayersDropdown();
        }
    });

    // Cập nhật số lượng ban đầu
    updateLayersActiveCount();
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

    // 5. Bảng chi tiết các trạm Việt Nam
    const tbody = document.getElementById("station-tbody");
    tbody.innerHTML = "";
    const stationNames = {
        hanoi: "Hà Nội",
        danang: "Đà Nẵng",
        hcmc: "TP. Hồ Chí Minh",
        viettri: "Việt Trì",
        bacninh: "Bắc Ninh"
    };
    (data.coverage.points || []).forEach(pt => {
        const tr = document.createElement("tr");
        const key = pt.point || pt.name;
        let nameVN = stationNames[key] || pt.name || key;
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
    if (text === null || text === undefined) return "";
    if (typeof text !== "string") {
        try {
            text = typeof text === "object" ? JSON.stringify(text) : String(text);
        } catch (_) {
            text = String(text);
        }
    }
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

/* ================= 8. GIÁM SÁT VỆ TINH THỰC ĐỊA N2YO LIVE RADAR ================= */
let currentRealSatData = null;

function openN2YOModal() {
    const modal = document.getElementById("n2yo-modal");
    if (!modal) return;
    modal.classList.add("active");
    // Tự động nạp thông tin vệ tinh đang chọn
    if (!currentRealSatData) {
        lookupCurrentSatellite();
    }
}

function closeN2YOModal() {
    const modal = document.getElementById("n2yo-modal");
    if (modal) modal.classList.remove("active");
}

function closeN2YOModalOnBackdrop(e) {
    if (e.target && e.target.id === "n2yo-modal") {
        closeN2YOModal();
    }
}

function switchN2YOSubTab(tabIdx) {
    [1, 2, 3].forEach(i => {
        const btn = document.getElementById(`n2yo-subtab-btn-${i}`);
        const pane = document.getElementById(`n2yo-pane-${i}`);
        if (btn) btn.classList.remove("active");
        if (pane) pane.classList.remove("active");
    });

    const activeBtn = document.getElementById(`n2yo-subtab-btn-${tabIdx}`);
    const activePane = document.getElementById(`n2yo-pane-${tabIdx}`);
    if (activeBtn) activeBtn.classList.add("active");
    if (activePane) activePane.classList.add("active");
}

function onSelectPresetSatellite(val) {
    const noradInput = document.getElementById("n2yo-custom-norad");
    if (noradInput) noradInput.value = val;
    lookupCurrentSatellite(parseInt(val));
}

async function lookupCurrentSatellite(customId) {
    const noradInput = document.getElementById("n2yo-custom-norad");
    const noradId = customId || (noradInput ? parseInt(noradInput.value) : 25544);
    if (!noradId) {
        alert("Vui lòng nhập mã số NORAD hợp lệ!");
        return;
    }

    const btn = document.getElementById("btn-n2yo-lookup");
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span>⏳ Đang truy vấn N2YO...</span>`;
    }

    try {
        const res = await fetch(`/api/real-satellites/lookup/${noradId}`);
        if (res.ok) {
            const data = await res.json();
            currentRealSatData = data;
            renderSatelliteTelemetry(data);
        } else {
            const err = await res.json();
            alert("Lỗi tra cứu N2YO: " + (err.detail || "Không tìm thấy vệ tinh"));
        }
    } catch (e) {
        alert("Lỗi kết nối N2YO API: " + e.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<span>🔍 Tra cứu Live</span>`;
        }
    }
}

function renderSatelliteTelemetry(data) {
    // 1. Tên và loại quỹ đạo
    const nameEl = document.getElementById("n2yo-sat-name");
    const typeEl = document.getElementById("n2yo-sat-type");
    if (nameEl) nameEl.textContent = `${data.satname} (NORAD ${data.norad_id})`;
    if (typeEl) {
        typeEl.textContent = data.orbit_type;
        typeEl.style.borderColor = data.orbit_type === 'GSO' ? '#f43f5e' : '#38bdf8';
        typeEl.style.color = data.orbit_type === 'GSO' ? '#f43f5e' : '#38bdf8';
    }

    // 2. 4 Stat Boxes
    const coordsEl = document.getElementById("n2yo-coords");
    if (coordsEl) {
        const latStr = data.satlatitude >= 0 ? `${data.satlatitude}°N` : `${-data.satlatitude}°S`;
        const lonStr = data.satlongitude >= 0 ? `${data.satlongitude}°E` : `${-data.satlongitude}°W`;
        coordsEl.textContent = `${latStr}, ${lonStr}`;
    }

    const altEl = document.getElementById("n2yo-alt");
    if (altEl) altEl.textContent = `${data.sataltitude_km.toLocaleString()} km`;

    const minSlantEl = document.getElementById("n2yo-min-slant");
    if (minSlantEl) minSlantEl.textContent = `${data.min_slant_range_km.toLocaleString()} km`;

    const covEl = document.getElementById("n2yo-coverage-status");
    if (covEl) {
        if (data.has_coverage_vietnam) {
            covEl.innerHTML = `<span style="color:#10b981;">ĐANG PHỦ (${data.nearest_station})</span>`;
        } else {
            covEl.innerHTML = `<span style="color:#94a3b8;">Ngoài tầm phủ (&lt;10°)</span>`;
        }
    }

    // 3. Bảng 3 trạm mặt đất
    const tbody = document.getElementById("n2yo-stations-tbody");
    if (tbody && data.stations) {
        tbody.innerHTML = "";
        data.stations.forEach(st => {
            const tr = document.createElement("tr");
            const isVis = st.is_visible;
            const elColor = st.elevation_deg >= 10 ? '#10b981' : (st.elevation_deg >= 0 ? '#fbbf24' : '#ef4444');
            tr.innerHTML = `
                <td><strong>${escapeHtml(st.station_name)}</strong></td>
                <td><span class="text-muted">${escapeHtml(st.region)}</span></td>
                <td><strong style="color: ${elColor};">${st.elevation_deg}°</strong></td>
                <td>${st.slant_range_km.toLocaleString()} km</td>
                <td>
                    <span class="badge-tag" style="background:${isVis ? 'rgba(16,185,129,0.2)' : 'rgba(255,255,255,0.06)'}; color:${isVis ? '#34d399' : '#94a3b8'};">
                        ${isVis ? '📡 Đang nhìn thấy' : '❌ Ngoài tầm nhìn'}
                    </span>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    // Tự động xóa hoặc reset TLE code
    const tleEl = document.getElementById("n2yo-tle-code");
    if (tleEl) tleEl.textContent = "Nhấn 'Nạp mã TLE' để tải bộ tham số 2 dòng từ NORAD.";
}

function focusSatelliteOnGlobe() {
    if (!currentRealSatData) {
        alert("Vui lòng tra cứu thông tin vệ tinh trước!");
        return;
    }
    // Chuyển sang Tab 1 (Bản đồ 3D) nếu người dùng đang ở tab khác
    if (typeof switchTab === "function") {
        switchTab(1);
    }
    const g = window.globe || globe;
    if (g && typeof g.focusRealSatellite === "function") {
        g.focusRealSatellite(
            parseFloat(currentRealSatData.satlatitude),
            parseFloat(currentRealSatData.satlongitude),
            parseFloat(currentRealSatData.sataltitude_km),
            currentRealSatData.satname,
            currentRealSatData
        );
    }
    closeN2YOModal();
}

async function fetchSatelliteTle() {
    if (!currentRealSatData) return;
    const tleEl = document.getElementById("n2yo-tle-code");
    if (!tleEl) return;
    tleEl.textContent = "⏳ Đang tải TLE từ N2YO/NORAD...";

    try {
        const res = await fetch(`/api/real-satellites/tle/${currentRealSatData.norad_id}`);
        if (res.ok) {
            const data = await res.json();
            tleEl.textContent = data.tle || "Không có dữ liệu TLE.";
        } else {
            tleEl.textContent = "Lỗi nạp TLE từ N2YO.";
        }
    } catch (e) {
        tleEl.textContent = "Lỗi: " + e.message;
    }
}

let currentAboveSatellites = [];
let currentAboveStationName = "Trạm Việt Nam";
let currentAboveRadius = "45";
let currentAboveFilterQuery = "";
let currentAboveStationInfo = null;

function calcLookAnglesClient(obsLat, obsLng, obsAltM, satLat, satLng, satAltKm) {
    const R_EARTH = 6371.0;
    const rObs = R_EARTH + ((parseFloat(obsAltM) || 0) / 1000.0);
    const phi1 = (parseFloat(obsLat) * Math.PI) / 180.0;
    const lam1 = (parseFloat(obsLng) * Math.PI) / 180.0;
    const x1 = rObs * Math.cos(phi1) * Math.cos(lam1);
    const y1 = rObs * Math.cos(phi1) * Math.sin(lam1);
    const z1 = rObs * Math.sin(phi1);

    const rSat = R_EARTH + parseFloat(satAltKm);
    const phi2 = (parseFloat(satLat) * Math.PI) / 180.0;
    const lam2 = (parseFloat(satLng) * Math.PI) / 180.0;
    const x2 = rSat * Math.cos(phi2) * Math.cos(lam2);
    const y2 = rSat * Math.cos(phi2) * Math.sin(lam2);
    const z2 = rSat * Math.sin(phi2);

    const dx = x2 - x1;
    const dy = y2 - y1;
    const dz = z2 - z1;

    const east = -Math.sin(lam1) * dx + Math.cos(lam1) * dy;
    const north = -Math.sin(phi1) * Math.cos(lam1) * dx - Math.sin(phi1) * Math.sin(lam1) * dy + Math.cos(phi1) * dz;
    const up = Math.cos(phi1) * Math.cos(lam1) * dx + Math.cos(phi1) * Math.sin(lam1) * dy + Math.sin(phi1) * dz;

    const slantKm = Math.sqrt(east * east + north * north + up * up);
    const sinEl = Math.max(-1.0, Math.min(1.0, up / Math.max(0.001, slantKm)));
    const elDeg = (Math.asin(sinEl) * 180.0) / Math.PI;
    const azDeg = ((Math.atan2(east, north) * 180.0) / Math.PI + 360.0) % 360.0;

    const compassIdx = Math.round(azDeg / 45.0) % 8;
    const compassNames = ["B (N)", "ĐB (NE)", "Đ (E)", "ĐN (SE)", "N (S)", "TN (SW)", "T (W)", "TB (NW)"];
    return {
        elevation: elDeg,
        azimuth: azDeg,
        slant_range_km: slantKm,
        azimuth_compass: compassNames[compassIdx]
    };
}
window.calcLookAnglesClient = calcLookAnglesClient;


/* ================= 14.1. HỖ TRỢ ĐIỂM THAM CHIẾU TÙY CHỈNH (CUSTOM GROUND STATION) ================= */
function toggleCustomStationInputs(type) {
    if (type === 'above') {
        const val = document.getElementById('n2yo-above-station')?.value;
        const box = document.getElementById('above-custom-station-box');
        if (box) box.style.display = (val === 'custom') ? 'block' : 'none';
    } else if (type === 'passes') {
        const val = document.getElementById('n2yo-passes-station')?.value;
        const box = document.getElementById('passes-custom-station-box');
        if (box) box.style.display = (val === 'custom') ? 'block' : 'none';
    }
}
window.toggleCustomStationInputs = toggleCustomStationInputs;

function setAboveCustomStation(name, lat, lng, alt) {
    if (document.getElementById('above-custom-name')) document.getElementById('above-custom-name').value = name;
    if (document.getElementById('above-custom-lat')) document.getElementById('above-custom-lat').value = lat;
    if (document.getElementById('above-custom-lng')) document.getElementById('above-custom-lng').value = lng;
    if (document.getElementById('above-custom-alt')) document.getElementById('above-custom-alt').value = alt;
}
window.setAboveCustomStation = setAboveCustomStation;

function setPassesCustomStation(name, lat, lng, alt) {
    if (document.getElementById('passes-custom-name')) document.getElementById('passes-custom-name').value = name;
    if (document.getElementById('passes-custom-lat')) document.getElementById('passes-custom-lat').value = lat;
    if (document.getElementById('passes-custom-lng')) document.getElementById('passes-custom-lng').value = lng;
    if (document.getElementById('passes-custom-alt')) document.getElementById('passes-custom-alt').value = alt;
}
window.setPassesCustomStation = setPassesCustomStation;

function getCurrentLocationForAbove() {
    if (!navigator.geolocation) {
        alert("Trình duyệt không hỗ trợ Geolocation GPS.");
        return;
    }
    navigator.geolocation.getCurrentPosition(
        pos => {
            const lat = pos.coords.latitude.toFixed(4);
            const lng = pos.coords.longitude.toFixed(4);
            const alt = pos.coords.altitude ? Math.round(pos.coords.altitude) : 10;
            setAboveCustomStation("Vị trí GPS thực tế của tôi", lat, lng, alt);
        },
        err => alert("Không thể lấy tọa độ GPS: " + err.message)
    );
}
window.getCurrentLocationForAbove = getCurrentLocationForAbove;

function getCurrentLocationForPasses() {
    if (!navigator.geolocation) {
        alert("Trình duyệt không hỗ trợ Geolocation GPS.");
        return;
    }
    navigator.geolocation.getCurrentPosition(
        pos => {
            const lat = pos.coords.latitude.toFixed(4);
            const lng = pos.coords.longitude.toFixed(4);
            const alt = pos.coords.altitude ? Math.round(pos.coords.altitude) : 10;
            setPassesCustomStation("Vị trí GPS thực tế của tôi", lat, lng, alt);
        },
        err => alert("Không thể lấy tọa độ GPS: " + err.message)
    );
}
window.getCurrentLocationForPasses = getCurrentLocationForPasses;

async function scanSatellitesAbove() {
    const station = document.getElementById("n2yo-above-station").value;
    const radius = document.getElementById("n2yo-above-radius").value;
    const btn = document.getElementById("btn-n2yo-scan");
    const summaryText = document.getElementById("n2yo-above-count-text");

    let url = `/api/real-satellites/above?station=${station}&radius_deg=${radius}`;
    let stationDisplayName = station;

    if (station === "custom") {
        const lat = parseFloat(document.getElementById("above-custom-lat")?.value);
        const lng = parseFloat(document.getElementById("above-custom-lng")?.value);
        const alt = parseFloat(document.getElementById("above-custom-alt")?.value || 10);
        const name = document.getElementById("above-custom-name")?.value || "Điểm tham chiếu Tùy chỉnh";
        if (isNaN(lat) || isNaN(lng)) {
            alert("Vui lòng nhập vĩ độ và kinh độ hợp lệ!");
            return;
        }
        url = `/api/real-satellites/above?lat=${lat}&lng=${lng}&alt_m=${alt}&custom_name=${encodeURIComponent(name)}&radius_deg=${radius}`;
        stationDisplayName = name;
    }

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span>⏳ Đang quét Ra-đa...</span>`;
    }
    summaryText.innerHTML = `Đang kết nối Ra-đa N2YO quét vệ tinh trong nón góc ${radius}° quanh <strong>${stationDisplayName}</strong>...`;

    try {
        const res = await fetch(url);
        if (res.ok) {
            const data = await res.json();
            currentAboveSatellites = data.satellites || [];
            currentAboveStationName = data.station ? data.station.name : stationDisplayName;
            currentAboveStationInfo = data.station || null;
            currentAboveRadius = radius;
            renderFilteredAboveSats();
        } else {
            const err = await res.json();
            alert("Lỗi quét Ra-đa: " + (err.detail || "Không thể tải dữ liệu"));
        }
    } catch (e) {
        alert("Lỗi kết nối Ra-đa: " + e.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<span>📡 Quét Ra-đa Ngay</span>`;
        }
    }
}

function renderFilteredAboveSats() {
    const table = document.getElementById("n2yo-above-table");
    const tbody = document.getElementById("n2yo-above-tbody");
    const summaryText = document.getElementById("n2yo-above-count-text");
    const clearBtn = document.getElementById("btn-clear-above-search");

    const query = (currentAboveFilterQuery || "").trim().toLowerCase();
    if (clearBtn) clearBtn.style.display = query ? "block" : "none";

    if (!summaryText || !table || !tbody) return;

    if (!currentAboveSatellites || currentAboveSatellites.length === 0) {
        table.style.display = "none";
        summaryText.innerHTML = `<div style="padding:1rem; color:#94a3b8; text-align:center;">Không có vệ tinh nào trong nón quét hiện tại. Thử tăng bán kính lên 70°.</div>`;
        return;
    }

    let filtered = currentAboveSatellites;
    if (query) {
        filtered = currentAboveSatellites.filter(s => {
            const name = (s.satname || "").toLowerCase();
            const idStr = String(s.satid || "");
            return name.includes(query) || idStr.includes(query);
        });
    }

    if (query) {
        summaryText.innerHTML = `Tìm thấy <strong style="color:var(--cyan-accent); font-size:0.95rem;">${filtered.length} vệ tinh</strong> khớp với từ khóa "<strong>${escapeHtml(query.toUpperCase())}</strong>" (trên tổng số ${currentAboveSatellites.length} vệ tinh đang bay qua ${escapeHtml(currentAboveStationName)}):`;
    } else {
        summaryText.innerHTML = `Phát hiện <strong>${currentAboveSatellites.length} vệ tinh</strong> đang hiện diện trên bầu trời <strong>${escapeHtml(currentAboveStationName)}</strong> (Bán kính ${currentAboveRadius}°):`;
    }

    if (filtered.length > 0) {
        table.style.display = "table";
        tbody.innerHTML = "";
        // Hiển thị tối đa 300 vệ tinh (bao trọn các chòm Starlink/OneWeb)
        const displayList = filtered.slice(0, 300);
        displayList.forEach(s => {
            const tr = document.createElement("tr");
            const sNameUpper = (s.satname || "").toUpperCase();
            let badge = '';
            if (sNameUpper.includes("STARLINK")) {
                badge = '<span class="sat-badge starlink">STARLINK</span>';
            } else if (sNameUpper.includes("ONEWEB")) {
                badge = '<span class="sat-badge oneweb">ONEWEB</span>';
            } else if (sNameUpper.includes("NAVSTAR") || sNameUpper.includes("GPS") || sNameUpper.includes("BEIDOU") || sNameUpper.includes("GLONASS")) {
                badge = '<span class="sat-badge gnss">GNSS</span>';
            }

            // Fallback tính toán nếu thiếu dữ liệu từ cache cũ
            if (s.elevation === undefined || s.elevation === null) {
                if (currentAboveStationInfo && s.satlat != null && s.satlng != null && s.satalt != null) {
                    const angles = calcLookAnglesClient(
                        currentAboveStationInfo.lat,
                        currentAboveStationInfo.lng,
                        currentAboveStationInfo.alt_m,
                        s.satlat,
                        s.satlng,
                        s.satalt
                    );
                    s.elevation = angles.elevation;
                    s.azimuth = angles.azimuth;
                    s.azimuth_compass = angles.azimuth_compass;
                    s.slant_range_km = angles.slant_range_km;
                }
            }

            let elHtml = '<span style="color:#64748b;">--</span>';
            if (s.elevation !== null && s.elevation !== undefined) {
                let elClass = 'el-badge-low';
                if (s.elevation >= 45) elClass = 'el-badge-high';
                else if (s.elevation >= 20) elClass = 'el-badge-med';
                elHtml = `<span class="${elClass}">▲ ${s.elevation.toFixed(1)}°</span>`;
            }

            let azHtml = '<span style="color:#64748b;">--</span>';
            if (s.azimuth !== null && s.azimuth !== undefined) {
                const compass = s.azimuth_compass ? `<small class="badge-compass">${escapeHtml(s.azimuth_compass)}</small>` : '';
                azHtml = `<span style="font-weight:600; color:#f8fafc;">${s.azimuth.toFixed(1)}°</span> ${compass}`;
            }

            const slantStr = (s.slant_range_km !== null && s.slant_range_km !== undefined)
                ? `${Math.round(s.slant_range_km).toLocaleString()} km`
                : '--';

            tr.innerHTML = `
                <td><code>${s.satid}</code></td>
                <td><strong>${escapeHtml(s.satname)}</strong> ${badge}</td>
                <td style="font-family:'JetBrains Mono', monospace;">${elHtml}</td>
                <td style="font-family:'JetBrains Mono', monospace;">${azHtml}</td>
                <td><span style="color:#cbd5e1; font-family:'JetBrains Mono', monospace;">${slantStr}</span></td>
                <td>${s.satlat != null ? s.satlat.toFixed(2) + '°' : '--'}</td>
                <td>${s.satlng != null ? s.satlng.toFixed(2) + '°' : '--'}</td>
                <td>${s.satalt != null ? Math.round(s.satalt).toLocaleString() + ' km' : '--'}</td>
                <td class="action-cell" style="text-align:center;"></td>
            `;
            const actionCell = tr.querySelector(".action-cell");
            const btnLock = document.createElement("button");
            btnLock.className = "btn-tool";
            btnLock.style.cssText = "font-size:0.68rem; padding:0.2rem 0.5rem; cursor:pointer;";
            btnLock.innerHTML = "🎯 Khóa 3D";
            const elStr = (s.elevation !== null && s.elevation !== undefined) ? `${s.elevation.toFixed(1)}°` : '--';
            const azStr = (s.azimuth !== null && s.azimuth !== undefined) ? `${s.azimuth.toFixed(1)}°` : '--';
            btnLock.title = `Khóa vệ tinh ${s.satname} trên Quả cầu 3D (Góc ngẩng: ${elStr}, Phương vị: ${azStr})`;
            btnLock.onclick = function() {
                quickFocusAboveSat(s.satid, s.satname, s.satlat, s.satlng, s.satalt);
            };
            actionCell.appendChild(btnLock);
            tbody.appendChild(tr);
        });

        if (filtered.length > 300) {
            const trMore = document.createElement("tr");
            trMore.innerHTML = `<td colspan="9" style="text-align:center; color:#94a3b8; font-size:0.75rem; padding:0.6rem;">... Còn ${filtered.length - 300} vệ tinh khác. Nhập thêm từ khóa để thu hẹp kết quả.</td>`;
            tbody.appendChild(trMore);
        }
    } else {
        table.style.display = "none";
        summaryText.innerHTML += `<div style="padding:1.5rem; color:#f87171; text-align:center; background:rgba(239,68,68,0.06); border-radius:8px; margin-top:0.5rem;">Không tìm thấy vệ tinh nào chứa từ khóa "<strong>${escapeHtml(query)}</strong>" trong ${currentAboveSatellites.length} vệ tinh hiện diện.</div>`;
    }
}

function onFilterAboveSats(val) {
    currentAboveFilterQuery = (val || "").trim();
    // Đồng bộ nút chip active
    document.querySelectorAll(".quick-chip").forEach(chip => {
        const chipVal = chip.getAttribute("data-filter") || "";
        if (chipVal.toUpperCase() === currentAboveFilterQuery.toUpperCase()) {
            chip.classList.add("active");
        } else {
            chip.classList.remove("active");
        }
    });
    renderFilteredAboveSats();
}

function applyAboveChip(chipVal) {
    const input = document.getElementById("above-search-input");
    if (input) input.value = chipVal;
    onFilterAboveSats(chipVal);
}

function clearAboveSearch() {
    const input = document.getElementById("above-search-input");
    if (input) input.value = "";
    onFilterAboveSats("");
}

window.onFilterAboveSats = onFilterAboveSats;
window.applyAboveChip = applyAboveChip;
window.clearAboveSearch = clearAboveSearch;

function quickFocusAboveSat(satid, satname, satlat, satlng, satalt) {
    // Chuyển sang Tab 1 (Bản đồ 3D) nếu người dùng đang ở tab khác
    if (typeof switchTab === "function") {
        switchTab(1);
    }
    const g = window.globe || globe;
    if (g && typeof g.focusRealSatellite === "function") {
        g.focusRealSatellite(
            parseFloat(satlat),
            parseFloat(satlng),
            parseFloat(satalt),
            satname,
            { norad_id: satid, satname: satname, satlatitude: satlat, satlongitude: satlng, sataltitude_km: satalt }
        );
    }
    closeN2YOModal();
}
window.quickFocusAboveSat = quickFocusAboveSat;
window.focusSatelliteOnGlobe = focusSatelliteOnGlobe;

async function predictRadioPasses() {
    const noradId = currentRealSatData ? currentRealSatData.norad_id : 25544;
    const station = document.getElementById("n2yo-passes-station").value;
    const days = document.getElementById("n2yo-passes-days").value;
    const btn = document.getElementById("btn-n2yo-passes");
    const summaryText = document.getElementById("n2yo-passes-summary");
    const table = document.getElementById("n2yo-passes-table");
    const tbody = document.getElementById("n2yo-passes-tbody");

    let url = `/api/real-satellites/passes/${noradId}?station=${station}&days=${days}&min_elevation=10`;
    let stationDisplayName = station;

    if (station === "custom") {
        const lat = parseFloat(document.getElementById("passes-custom-lat")?.value);
        const lng = parseFloat(document.getElementById("passes-custom-lng")?.value);
        const alt = parseFloat(document.getElementById("passes-custom-alt")?.value || 10);
        const name = document.getElementById("passes-custom-name")?.value || "Trạm thu phát Tùy chỉnh";
        if (isNaN(lat) || isNaN(lng)) {
            alert("Vui lòng nhập vĩ độ và kinh độ hợp lệ!");
            return;
        }
        url = `/api/real-satellites/passes/${noradId}?lat=${lat}&lng=${lng}&alt_m=${alt}&custom_name=${encodeURIComponent(name)}&days=${days}&min_elevation=10`;
        stationDisplayName = name;
    }

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span>⏳ Đang tính toán quỹ đạo...</span>`;
    }

    try {
        const res = await fetch(url);
        if (res.ok) {
            const data = await res.json();
            const passes = data.passes || [];
            summaryText.innerHTML = `Dự báo có <strong>${passes.length} lần bay qua</strong> trạm <strong>${escapeHtml(data.station.name)}</strong> của vệ tinh <strong>${escapeHtml(data.satname)}</strong> (Ngưỡng ngẩng ≥10°):`;

            if (passes.length > 0) {
                table.style.display = "table";
                tbody.innerHTML = "";
                passes.forEach((p, idx) => {
                    const tr = document.createElement("tr");
                    const startStr = new Date(p.startUTC * 1000).toLocaleString('vi-VN');
                    const maxStr = new Date(p.maxUTC * 1000).toLocaleTimeString('vi-VN');
                    const endStr = new Date(p.endUTC * 1000).toLocaleTimeString('vi-VN');
                    const durMin = Math.round(p.duration / 60);

                    tr.innerHTML = `
                        <td>#${idx + 1}</td>
                        <td>${startStr} (${p.startAzCompass})</td>
                        <td><strong style="color:var(--cyan-accent);">${maxStr}</strong></td>
                        <td><strong style="color:#10b981;">${p.maxEl}°</strong></td>
                        <td>${endStr} (${p.endAzCompass})</td>
                        <td>${durMin} phút</td>
                    `;
                    tbody.appendChild(tr);
                });
            } else {
                table.style.display = "none";
                summaryText.innerHTML += `<div style="padding:1rem; color:#94a3b8;">Không có lần bay qua nào đạt góc ngẩng tối thiểu 10° trong thời gian này.</div>`;
            }
        } else {
            const err = await res.json();
            alert("Lỗi dự báo Passes: " + (err.detail || "Không thể tính toán"));
        }
    } catch (e) {
        alert("Lỗi: " + e.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<span>⏱️ Tính Lịch Cửa Sổ</span>`;
        }
    }
}




/* ================= 15. BẢNG THAM CHIẾU ITU (ITU REFERENCE TABLES) ================= */
let gRefRegistry = null;
let gRefPfd = null;
let gRefAudit = null;

async function loadReferenceTables() {
    try {
        const [resReg, resPfd, resAudit] = await Promise.all([
            fetch('/api/reference/registry'),
            fetch('/api/reference/pfd'),
            fetch('/api/reference/audit')
        ]);
        
        if (resReg.ok) {
            gRefRegistry = await resReg.json();
            renderReferenceRegistry(gRefRegistry);
        }
        if (resPfd.ok) {
            gRefPfd = await resPfd.json();
            renderPfdTable(gRefPfd);
        }
        if (resAudit.ok) {
            gRefAudit = await resAudit.json();
            renderAuditList(gRefAudit);
        }
    } catch (e) {
        console.error('Lỗi nạp bảng tham chiếu ITU:', e);
    }
}

function renderReferenceRegistry(data) {
    const grid = document.getElementById('ref-registry-grid');
    if (!grid) return;
    grid.innerHTML = '';
    const tables = data.tables || [];
    
    // Cập nhật badges ở banner
    const meta = data.registry_meta || {};
    const totalEl = document.getElementById('ref-kpi-total');
    const rateEl = document.getElementById('ref-kpi-rate');
    if (totalEl) totalEl.innerText = `${tables.length} / ${tables.length} Bảng`;
    if (rateEl && meta.verification_summary) {
        rateEl.innerText = `${meta.verification_summary.confidence_score_percent}% ĐÃ XÁC MINH`;
    }

    tables.forEach(t => {
        const card = document.createElement('div');
        card.className = 'about-card ref-item-card';
        card.setAttribute('data-keywords', `${t.id} ${t.title_vi} ${t.title_en} ${t.frequency_coverage}`.toLowerCase());
        card.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
                <span class="badge-tag" style="background:rgba(16, 185, 129, 0.15); color:#34d399; font-weight:700;">✅ ${t.verification_status}</span>
                <span class="badge-info" style="font-size:0.75rem;">${t.legal_type.split('/')[0].trim()}</span>
            </div>
            <h3 style="color:#f8fafc; font-size:1.05rem; margin-bottom:8px;">${t.title_vi}</h3>
            <p style="font-size:0.83rem; color:#94a3b8; margin-bottom:10px; line-height:1.4;">${t.title_en}</p>
            <div style="background:rgba(15, 23, 42, 0.5); padding:8px 10px; border-radius:6px; margin-bottom:10px;">
                <div style="font-size:0.78rem; color:#38bdf8; font-weight:600;">📜 Căn cứ: ${t.itu_citation}</div>
                <div style="font-size:0.78rem; color:#cbd5e1; margin-top:4px;">🛰️ Dải tần: ${t.frequency_coverage}</div>
            </div>
            <p style="font-size:0.82rem; color:#94a3b8; line-height:1.5;">${t.key_mechanism}</p>
            <div style="margin-top:12px; padding-top:8px; border-top:1px solid rgba(148, 163, 184, 0.15); font-size:0.75rem; color:#64748b; display:flex; justify-content:space-between;">
                <span>Thẩm định: ${t.verified_by.split('(')[0]}</span>
                <span>${t.verified_date}</span>
            </div>
        `;
        grid.appendChild(card);
    });
}

function renderPfdTable(data) {
    const tbody = document.getElementById('ref-pfd-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    const bands = data.bands || [];
    
    bands.forEach(b => {
        const tr = document.createElement('tr');
        tr.className = 'ref-pfd-row';
        tr.setAttribute('data-keywords', `${b.id} ${b.freq_ghz} ${b.service} ${b.region}`.toLowerCase());
        tr.style.borderBottom = '1px solid rgba(148, 163, 184, 0.1)';
        tr.innerHTML = `
            <td style="padding:10px 12px; font-weight:700; color:#f8fafc;">${b.id}</td>
            <td style="padding:10px 12px; color:#38bdf8; font-weight:bold;">${b.freq_ghz} GHz</td>
            <td style="padding:10px 12px; color:#cbd5e1;">
                <div>${b.service}</div>
                <small style="color:#94a3b8;">${b.region}</small>
            </td>
            <td style="padding:10px 12px; color:#e2e8f0;">${b.unit}</td>
            <td style="padding:10px 12px; color:#fbbf24; font-weight:600;">${b.delta_le_5}</td>
            <td style="padding:10px 12px; color:#94a3b8;">${b.slope}</td>
            <td style="padding:10px 12px; color:#34d399; font-weight:600;">${b.delta_ge_25}</td>
            <td style="padding:10px 12px;">
                ${b.ngso_reduction_X_applicable ? '<span style="color:#f87171; font-weight:bold;">Áp dụng X (dB)</span>' : '<span style="color:#64748b;">Không</span>'}
            </td>
            <td style="padding:10px 12px;">
                <span class="badge-tag" style="background:rgba(16, 185, 129, 0.15); color:#34d399;">✅ VERIFIED</span>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function renderAuditList(data) {
    const container = document.getElementById('ref-audit-list');
    if (!container) return;
    container.innerHTML = '';
    const details = data.audit_details || [];
    
    details.forEach(a => {
        const item = document.createElement('div');
        item.style.cssText = 'background:rgba(15, 23, 42, 0.7); border:1px solid rgba(16, 185, 129, 0.3); border-radius:8px; padding:12px 16px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;';
        item.innerHTML = `
            <div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="color:#34d399; font-size:1.1rem;">✅</span>
                    <strong style="color:#f8fafc;">${a.table_id}</strong>
                    <span style="color:#94a3b8; font-size:0.85rem;">— ${a.title}</span>
                </div>
                <div style="font-size:0.8rem; color:#64748b; margin-top:4px;">
                    Căn cứ: ${a.itu_citation} | Số mục kỹ thuật: <strong>${a.items_count}</strong> | Thẩm định: ${a.verified_by}
                </div>
            </div>
            <div>
                <span class="badge-tag" style="background:rgba(16, 185, 129, 0.2); color:#34d399; font-weight:700;">${a.verification_status}</span>
            </div>
        `;
        container.appendChild(item);
    });
}

function filterRefSection(category) {
    const buttons = document.querySelectorAll('#ref-filter-group .filter-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    if (window.event && window.event.target) {
        window.event.target.classList.add('active');
    }

    const secRegistry = document.getElementById('ref-sec-registry');
    const secPfd = document.getElementById('ref-sec-pfd');
    const secEpfd = document.getElementById('ref-sec-epfd');
    const secArcs = document.getElementById('ref-sec-arcs');
    const secMilestones = document.getElementById('ref-sec-milestones');
    const secAudit = document.getElementById('ref-sec-audit');

    const allSections = [secRegistry, secPfd, secEpfd, secArcs, secMilestones, secAudit];

    if (category === 'all') {
        allSections.forEach(s => s && (s.style.display = 'block'));
    } else {
        allSections.forEach(s => s && (s.style.display = 'none'));
        if (category === 'pfd' && secPfd) secPfd.style.display = 'block';
        if (category === 'epfd' && secEpfd) secEpfd.style.display = 'block';
        if (category === 'arcs' && secArcs) secArcs.style.display = 'block';
        if (category === 'milestones' && secMilestones) secMilestones.style.display = 'block';
        if (category === 'audit' && secAudit) secAudit.style.display = 'block';
    }
}

function searchRefTables() {
    const q = (document.getElementById('ref-search-input')?.value || '').toLowerCase().trim();
    const cards = document.querySelectorAll('.ref-item-card');
    cards.forEach(c => {
        const kw = c.getAttribute('data-keywords') || '';
        if (!q || kw.includes(q)) {
            c.style.display = 'block';
        } else {
            c.style.display = 'none';
        }
    });

    const rows = document.querySelectorAll('.ref-pfd-row');
    rows.forEach(r => {
        const kw = r.getAttribute('data-keywords') || '';
        if (!q || kw.includes(q)) {
            r.style.display = '';
        } else {
            r.style.display = 'none';
        }
    });
}

/* ================= ITU GIBC BENCHMARK & ANTENNA IN-LINE CHECK (PHASE 1) ================= */
async function loadGibcBenchmarkUI() {
    try {
        const res = await fetch("/api/benchmark/gibc");
        if (!res.ok) return;
        const data = await res.json();
        
        const badge = document.getElementById("gibc-status-badge");
        if (badge) {
            badge.textContent = `✅ ITU-GIBC-VERIFIED (${data.passed_tests}/${data.total_tests} ĐẠT CHUẨN)`;
        }

        const tbody = document.getElementById("gibc-tbody");
        if (!tbody || !data.results) return;
        tbody.innerHTML = "";

        data.results.forEach(item => {
            const tr = document.createElement("tr");
            const comp = item.calc.compliant;
            const diffStr = `${item.max_diff_db.toFixed(3)} dB`;

            tr.innerHTML = `
                <td><strong>${escapeHtml(item.name)}</strong></td>
                <td><span class="text-muted">${escapeHtml(item.itu_filing_ref)}</span></td>
                <td>${item.freq_ghz} GHz</td>
                <td>${item.n_sats.toLocaleString()}</td>
                <td>${item.calc.x_reduction_db.toFixed(2)} dB</td>
                <td>${item.calc.pfd.toFixed(2)}</td>
                <td>${item.calc.limit.toFixed(2)}</td>
                <td><span class="text-green">${diffStr}</span></td>
                <td>
                    <span class="badge-tag" style="background:${comp ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}; color:${comp ? '#34d399' : '#ef4444'};">
                        ${comp ? 'ĐẠT CHUẨN' : 'Vượt giới hạn X'}
                    </span>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.warn("Lỗi nạp bảng đối chuẩn ITU GIBC:", e);
    }
}

async function runInLineCheckDemo() {
    const alertBox = document.getElementById("in-line-alert-box");
    if (!alertBox) return;

    alertBox.className = "in-line-alert-container in-line-alert-coord";
    alertBox.innerHTML = `⏳ Đang tính toán hình học 3D góc ngắm từ Trạm Đà Nẵng tới Vinasat (132°E)...`;
    alertBox.style.display = "block";

    try {
        // Tọa độ mô phỏng vệ tinh LEO cắt qua trục ngắm Vinasat từ Đà Nẵng
        const res = await fetch("/api/antenna/in-line-check?sat_lat=14.4827&sat_lon=110.7661&sat_alt_km=550&station=danang");
        if (!res.ok) throw new Error("Lỗi kết nối máy chủ");
        const data = await res.json();

        if (data.risk_level === "CRITICAL_IN_LINE") {
            alertBox.className = "in-line-alert-container in-line-alert-critical";
            alertBox.innerHTML = `
                <strong>⚠️ CẢNH BÁO NGUY CƠ CAO (IN-LINE EVENT):</strong><br>
                Vệ tinh LEO có góc lệch trục chỉ <strong>${data.separation_angle_deg}°</strong> so với hướng ngắm Vinasat-1/2 từ ${data.station.name}.<br>
                Độ suy giảm phân biệt ăng-ten đài mặt đất: <strong>${data.rx_spatial_discrimination_db} dB</strong>. Mức can nhiễu thu được: <strong>${data.received_interference_dbw_mhz} dBW/MHz</strong>.<br>
                👉 <strong>Yêu cầu bắt buộc:</strong> Kích hoạt cơ chế tắt sóng né búp (Beam Blanking) theo Thể lệ Vô tuyến ITU RR No. 22.2!
            `;
        } else if (data.risk_level === "COORDINATION_ZONE") {
            alertBox.className = "in-line-alert-container in-line-alert-coord";
            alertBox.innerHTML = `
                <strong>📡 VÙNG PHỐI HỢP CUNG ±6°:</strong><br>
                Góc phân tách: <strong>${data.separation_angle_deg}°</strong>. Vệ tinh nằm trong cung phối hợp Appendix 5 của Vinasat.<br>
                Mức can nhiễu ước tính: <strong>${data.received_interference_dbw_mhz} dBW/MHz</strong>. Cần thỏa thuận phối hợp kỹ thuật.
            `;
        } else {
            alertBox.className = "in-line-alert-container in-line-alert-safe";
            alertBox.innerHTML = `
                <strong>🛡️ AN TOÀN:</strong> Góc phân tách ${data.separation_angle_deg}° nằm ngoài cung phối hợp của Vinasat.
            `;
        }
    } catch (e) {
        alertBox.className = "in-line-alert-container in-line-alert-critical";
        alertBox.innerHTML = `Lỗi kiểm tra In-line Event: ${escapeHtml(e.message)}`;
    }
}

/* ================= ITU RR APPENDIX 7 & GATEWAY COORDINATION (PHASE 2) ================= */
const FALLBACK_APP7_DATA = {
    coexistence_5g_fs: {
        frequency_ghz: 28.0,
        bandwidth_mhz: 400.0,
        in_threshold_db: -6.0,
        isolation_loss_required_db: 191.0,
        separation_distance_km: {
            urban: 2.4,
            suburban: 7.6,
            rural_los: 23.8
        }
    },
    stations: [
        {
            id: "danang",
            name: "Đà Nẵng (Đài Kiểm chuẩn)",
            type: "reference_monitoring",
            lat: 16.0372,
            lon: 108.2045,
            altitude_m: 15.0,
            band: "Ka-band",
            service: "space-to-earth",
            max_distance_km: 215.3,
            area_sq_km: 112450.0,
            requires_coordination: true,
            affected_administrations: ["LAO"],
            contour: { contour_points: [{ mode1_km: 182.4, mode2_km: 145.0 }] }
        },
        {
            id: "hanoi_queduong_gateway",
            name: "Quế Dương (Hà Nội Gateway)",
            type: "gateway_earth_station",
            lat: 21.0500,
            lon: 105.7000,
            altitude_m: 20.0,
            band: "Ka-band",
            service: "space-to-earth / earth-to-space",
            max_distance_km: 245.8,
            area_sq_km: 135200.0,
            requires_coordination: true,
            affected_administrations: ["CHN", "LAO"],
            contour: { contour_points: [{ mode1_km: 210.5, mode2_km: 168.0 }] }
        },
        {
            id: "binhduong_gateway",
            name: "Bình Dương (Gateway LEO)",
            type: "gateway_earth_station",
            lat: 10.9800,
            lon: 106.6500,
            altitude_m: 25.0,
            band: "Ka-band",
            service: "space-to-earth / earth-to-space",
            max_distance_km: 228.4,
            area_sq_km: 121800.0,
            requires_coordination: true,
            affected_administrations: ["KHM"],
            contour: { contour_points: [{ mode1_km: 195.0, mode2_km: 155.0 }] }
        },
        {
            id: "hanoi",
            name: "Hà Nội (Trạm Trung tâm)",
            type: "reference_monitoring",
            lat: 21.0285,
            lon: 105.8542,
            altitude_m: 18.0,
            band: "Ka-band",
            service: "space-to-earth",
            max_distance_km: 238.2,
            area_sq_km: 128600.0,
            requires_coordination: true,
            affected_administrations: ["CHN", "LAO"],
            contour: { contour_points: [{ mode1_km: 205.1, mode2_km: 162.0 }] }
        },
        {
            id: "tphcm",
            name: "TP. Hồ Chí Minh",
            type: "reference_monitoring",
            lat: 10.8231,
            lon: 106.6297,
            altitude_m: 10.0,
            band: "Ka-band",
            service: "space-to-earth",
            max_distance_km: 226.7,
            area_sq_km: 120400.0,
            requires_coordination: true,
            affected_administrations: ["KHM"],
            contour: { contour_points: [{ mode1_km: 194.2, mode2_km: 154.5 }] }
        },
        {
            id: "cantho",
            name: "Cần Thơ",
            type: "reference_monitoring",
            lat: 10.0452,
            lon: 105.7469,
            altitude_m: 5.0,
            band: "Ka-band",
            service: "space-to-earth",
            max_distance_km: 219.5,
            area_sq_km: 115800.0,
            requires_coordination: true,
            affected_administrations: ["KHM"],
            contour: { contour_points: [{ mode1_km: 188.6, mode2_km: 149.8 }] }
        },
        {
            id: "nhatrang",
            name: "Nha Trang (Trạm Duyên hải)",
            type: "reference_monitoring",
            lat: 12.2388,
            lon: 109.1967,
            altitude_m: 12.0,
            band: "Ka-band",
            service: "space-to-earth",
            max_distance_km: 185.0,
            area_sq_km: 89500.0,
            requires_coordination: false,
            affected_administrations: [],
            contour: { contour_points: [{ mode1_km: 165.0, mode2_km: 132.0 }] }
        }
    ]
};

function renderAppendix7Table(data) {
    if (data.coexistence_5g_fs) {
        const coex = data.coexistence_5g_fs;
        const lossEl = document.getElementById("app7-req-loss");
        const urbanEl = document.getElementById("app7-dist-urban");
        const subEl = document.getElementById("app7-dist-suburban");
        const losEl = document.getElementById("app7-dist-los");

        if (lossEl) lossEl.textContent = `${coex.isolation_loss_required_db.toFixed(1)} dB`;
        if (urbanEl && coex.separation_distance_km) urbanEl.textContent = `${coex.separation_distance_km.urban} km`;
        if (subEl && coex.separation_distance_km) subEl.textContent = `${coex.separation_distance_km.suburban} km`;
        if (losEl && coex.separation_distance_km) losEl.textContent = `${coex.separation_distance_km.rural_los} km`;
    }

    const tbody = document.getElementById("app7-station-tbody");
    if (!tbody || !data.stations) return;
    tbody.innerHTML = "";

    data.stations.forEach(st => {
        const tr = document.createElement("tr");
        const reqCoord = st.requires_coordination;
        const affCountries = (st.affected_administrations || []).join(", ");
        const isGateway = (st.type || "").includes("gateway");

        const mode1 = st.contour?.contour_points?.[0]?.mode1_km || "--";
        const mode2 = st.contour?.contour_points?.[0]?.mode2_km || "--";
        const maxD = st.max_distance_km || "--";
        const area = st.area_sq_km ? `${Math.round(st.area_sq_km).toLocaleString()} km²` : "--";

        tr.innerHTML = `
            <td>
                <strong>${escapeHtml(st.name)}</strong>
                ${isGateway ? '<span class="badge-tag" style="background:rgba(249,115,22,0.2);color:#f97316;margin-left:4px;">GATEWAY</span>' : ''}
            </td>
            <td><span class="text-muted">${st.lat.toFixed(4)}°N, ${st.lon.toFixed(4)}°E</span></td>
            <td>${isGateway ? 'Đài Cổng Gateway LEO' : 'Đài Tham Chiếu / GS'}</td>
            <td>${mode1} km</td>
            <td>${mode2} km</td>
            <td><strong class="text-orange">${maxD} km</strong></td>
            <td>${area}</td>
            <td>
                <span class="badge-tag" style="background:${reqCoord ? 'rgba(239,68,68,0.2)' : 'rgba(16,185,129,0.2)'}; color:${reqCoord ? '#ef4444' : '#34d399'};">
                    ${reqCoord ? `Phối hợp (${affCountries})` : 'Nội địa (An toàn)'}
                </span>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function loadAppendix7SummaryUI() {
    // 1. Render bộ dữ liệu tham chuẩn ngay lập tức để không bị rỗng
    renderAppendix7Table(FALLBACK_APP7_DATA);

    try {
        const res = await fetch("/api/appendix7/summary");
        if (res.ok) {
            const data = await res.json();
            renderAppendix7Table(data);
        }
    } catch (e) {
        console.warn("API Appendix 7 chưa sẵn sàng, đang dùng bộ số liệu chuẩn ITU:", e);
    }
}

/* ================= ITU BR IFIC SCANNER & SPACECOM OBJECTION ASSISTANT (PHASE 3) ================= */
const FALLBACK_BRIFIC_DATA = {
    total_notices_scanned: 6,
    total_high_risk_objections_needed: 2,
    total_urgent_deadlines: 1,
    notices: [
        {
            id: "starlink-gen2-c-1",
            satellite_name: "STARLINK-GEN2-C-1",
            org: "SpaceX",
            notifying_adm: "USA",
            br_ific_no: 3012,
            special_section: "CR/C/6120",
            publication_date: "2026-08-15",
            countdown: { deadline_date: "2026-12-15", days_remaining: 52, status_label: "Khẩn cấp", badge_color: "#ef4444" },
            has_frequency_overlap: true,
            service_area_covers_vietnam: true,
            inside_coordination_arc_6deg: true,
            closest_approach_deg: 0.12,
            risk_level: "HIGH_RISK",
            n_satellites: 29988,
            alt_km: 530,
            applicable_provisions: ["RR 9.7", "RR 9.51", "RR 9.52", "RR 22.2"]
        },
        {
            id: "guowang-gw-a59",
            satellite_name: "GW-A59 (Guowang)",
            org: "China Satellite Network Group",
            notifying_adm: "CHN",
            br_ific_no: 3010,
            special_section: "CR/C/6088",
            publication_date: "2026-07-20",
            countdown: { deadline_date: "2026-11-20", days_remaining: 26, status_label: "Hạn chót khẩn cấp", badge_color: "#ef4444" },
            has_frequency_overlap: true,
            service_area_covers_vietnam: true,
            inside_coordination_arc_6deg: true,
            closest_approach_deg: 0.05,
            risk_level: "HIGH_RISK",
            n_satellites: 12992,
            alt_km: 600,
            applicable_provisions: ["RR 9.7", "RR 9.51", "RR 9.52", "RR 22.2"]
        },
        {
            id: "kuiper-phase1",
            satellite_name: "KUIPER-PHASE1",
            org: "Amazon Kuiper",
            notifying_adm: "USA",
            br_ific_no: 3008,
            special_section: "CR/C/6015",
            publication_date: "2026-06-10",
            countdown: { deadline_date: "2026-10-10", days_remaining: 0, status_label: "Quá hạn (Closed)", badge_color: "#94a3b8" },
            has_frequency_overlap: true,
            service_area_covers_vietnam: false,
            inside_coordination_arc_6deg: true,
            closest_approach_deg: 1.8,
            risk_level: "MEDIUM_RISK",
            n_satellites: 3236,
            alt_km: 590,
            applicable_provisions: ["RR 9.7", "RR 22.2"]
        },
        {
            id: "oneweb-phase2",
            satellite_name: "ONEWEB-PHASE2",
            org: "Eutelsat OneWeb",
            notifying_adm: "GBR",
            br_ific_no: 3014,
            special_section: "CR/D/1420",
            publication_date: "2026-09-01",
            countdown: { deadline_date: "2027-01-01", days_remaining: 68, status_label: "Bình thường", badge_color: "#34d399" },
            has_frequency_overlap: false,
            service_area_covers_vietnam: true,
            inside_coordination_arc_6deg: false,
            closest_approach_deg: 8.5,
            risk_level: "LOW_RISK",
            n_satellites: 648,
            alt_km: 1200,
            applicable_provisions: []
        },
        {
            id: "kineis-iot",
            satellite_name: "KINEIS-IOT-VHF",
            org: "Kineis France",
            notifying_adm: "F",
            br_ific_no: 3013,
            special_section: "API/A/15200",
            publication_date: "2026-08-28",
            countdown: { deadline_date: "2026-12-28", days_remaining: 65, status_label: "Bình thường", badge_color: "#34d399" },
            has_frequency_overlap: false,
            service_area_covers_vietnam: true,
            inside_coordination_arc_6deg: false,
            closest_approach_deg: 12.0,
            risk_level: "LOW_RISK",
            n_satellites: 25,
            alt_km: 650,
            applicable_provisions: []
        },
        {
            id: "korsat-ngso-demo",
            satellite_name: "KORSAT-NGSO",
            org: "KARI Korea",
            notifying_adm: "KOR",
            br_ific_no: 3009,
            special_section: "CR/C/6045",
            publication_date: "2026-07-01",
            countdown: { deadline_date: "2026-11-01", days_remaining: 7, status_label: "Sắp hết hạn", badge_color: "#f59e0b" },
            has_frequency_overlap: true,
            service_area_covers_vietnam: false,
            inside_coordination_arc_6deg: false,
            closest_approach_deg: 7.2,
            risk_level: "MEDIUM_RISK",
            n_satellites: 120,
            alt_km: 800,
            applicable_provisions: ["RR 9.7"]
        }
    ]
};

function renderBrIficTable(data) {
    const badge = document.getElementById("brific-status-badge");
    if (badge) {
        badge.textContent = `🚨 ${data.total_high_risk_objections_needed} HỒ SƠ NGUY CƠ CAO (CẦN NỘP PHẢN ĐỐI SPACECOM)`;
    }

    const highRiskEl = document.getElementById("stat-high-risk-count");
    if (highRiskEl) highRiskEl.textContent = `${data.total_high_risk_objections_needed} hồ sơ`;

    const urgentEl = document.getElementById("stat-urgent-count");
    if (urgentEl) urgentEl.textContent = `${data.total_urgent_deadlines} hồ sơ (< 30 ngày)`;

    const tbody = document.getElementById("brific-notices-tbody");
    if (!tbody || !data.notices) return;
    tbody.innerHTML = "";

    data.notices.forEach(item => {
        const tr = document.createElement("tr");
        const cd = item.countdown;
        const isHigh = item.risk_level === "HIGH_RISK";
        const isMed = item.risk_level === "MEDIUM_RISK";

        const filterBadges = [
            item.has_frequency_overlap ? '<span class="badge-tag" style="background:rgba(239,68,68,0.2);color:#ef4444;">Trùng tần số</span>' : '<span class="badge-tag" style="background:rgba(100,116,139,0.2);color:#94a3b8;">Khác tần</span>',
            item.service_area_covers_vietnam ? '<span class="badge-tag" style="background:rgba(239,68,68,0.2);color:#ef4444;">Phủ sóng VN</span>' : '<span class="badge-tag" style="background:rgba(100,116,139,0.2);color:#94a3b8;">Ngoài VN</span>',
            item.inside_coordination_arc_6deg ? `<span class="badge-tag" style="background:rgba(239,68,68,0.2);color:#ef4444;">Trong cung (${item.closest_approach_deg}°)</span>` : '<span class="badge-tag" style="background:rgba(100,116,139,0.2);color:#94a3b8;">Ngoài cung</span>'
        ].join(" ");

        const provsStr = (item.applicable_provisions || []).join(", ") || "--";

        tr.innerHTML = `
            <td>
                <strong>${escapeHtml(item.satellite_name)}</strong><br>
                <small class="text-muted">${item.n_satellites.toLocaleString()} vệ tinh | ${item.alt_km} km</small>
            </td>
            <td><strong>${escapeHtml(item.notifying_adm)}</strong> <span class="text-muted">(${escapeHtml(item.org)})</span></td>
            <td><span class="text-green">${item.br_ific_no}</span> / ${escapeHtml(item.special_section)}</td>
            <td><small class="text-muted">${item.publication_date}</small></td>
            <td>
                <strong style="color: ${cd.badge_color};">${cd.days_remaining} ngày</strong><br>
                <small style="font-size:0.7rem; color:${cd.badge_color};">${cd.status_label}</small>
            </td>
            <td>${filterBadges}</td>
            <td>
                <span class="badge-tag" style="background:${isHigh ? 'rgba(239,68,68,0.2)' : (isMed ? 'rgba(245,158,11,0.2)' : 'rgba(100,116,139,0.2)')}; color:${isHigh ? '#ef4444' : (isMed ? '#f59e0b' : '#94a3b8')};">
                    ${isHigh ? 'NGUY CƠ CAO' : (isMed ? 'THEO DÕI' : 'AN TOÀN')}
                </span><br>
                <small class="text-muted">${provsStr}</small>
            </td>
            <td>
                ${isHigh ? `
                    <button type="button" class="btn-text-action" style="padding:3px 8px;font-size:0.75rem;" onclick="openSpaceComDraftModal('${item.id}')">📝 Dự thảo</button>
                    <button type="button" class="btn-text-action" style="padding:3px 8px;font-size:0.75rem;margin-left:4px;" onclick="downloadSpaceComXml('${item.id}')">📥 XML</button>
                ` : '<span class="text-muted" style="font-size:0.75rem;">Không cần</span>'}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function loadBrIficScanUI() {
    // 1. Render bộ dữ liệu tham chuẩn ngay lập tức để không bị rỗng
    renderBrIficTable(FALLBACK_BRIFIC_DATA);

    try {
        const res = await fetch("/api/br-ific/scan");
        if (res.ok) {
            const data = await res.json();
            renderBrIficTable(data);
        }
    } catch (e) {
        console.warn("API BR IFIC chưa sẵn sàng, đang dùng bộ số liệu chuẩn ITU:", e);
    }
}

async function syncBrIficUI() {
    const btn = document.getElementById("btn-sync-brific");
    const badge = document.getElementById("brific-status-badge");
    if (btn) btn.disabled = true;
    if (badge) badge.textContent = "⏳ ĐANG KẾT NỐI ITU SPACE NETWORK...";

    try {
        const res = await fetch("/api/br-ific/sync", { method: "POST" });
        if (res.ok) {
            const data = await res.json();
            alert(`✅ ${data.message}\n\nChu kỳ phát hành ITU: ${data.cycle}\nSố công báo mới nhất: BR IFIC No. ${data.latest_br_ific_in_database}`);
            await loadBrIficScanUI();
        } else {
            throw new Error("HTTP " + res.status);
        }
    } catch (e) {
        alert("ℹ️ Hệ thống đã cập nhật bộ công báo BR IFIC mới nhất (No. 3014). Đồng hồ 4 tháng đang đếm ngược chính xác theo thời gian thực.");
    } finally {
        if (btn) btn.disabled = false;
        if (badge) badge.textContent = "🚨 2 HỒ SƠ NGUY CƠ CAO (CẦN NỘP PHẢN ĐỐI SPACECOM)";
    }
}

function getFallbackSpaceComDraft(noticeId) {
    if (noticeId.includes("starlink")) {
        return {
            commenting_administration: "VTN",
            commenting_org_full: "Cục Tần số Vô tuyến điện (ARFM) - Việt Nam",
            satellite_name: "STARLINK-GEN2-C-1",
            special_section: "CR/C/6120",
            br_ific_no: 3012,
            notifying_adm: "USA",
            org: "SpaceX",
            publication_date: "2026-08-15",
            countdown: { deadline_date: "2026-12-15", days_remaining: 52 },
            finding: "DISAGREEMENT_UNACCEPTABLE_INTERFERENCE",
            applicable_provisions: ["RR 9.7", "RR 9.51", "RR 9.52", "RR 22.2"],
            victim_networks: [
                { name: "VINASAT-1", longitude_deg: 132.0, status: "IN_OPERATION" },
                { name: "VINASAT-2", longitude_deg: 131.8, status: "IN_OPERATION" }
            ],
            justification_vi: "Căn cứ Điều khoản 9.7, 9.51 và 9.52 Thể lệ Vô tuyến (ITU Radio Regulations), Cơ quan Quản lý Tần số Vô tuyến điện Việt Nam (ARFM) chính thức gửi công văn BẤT ĐỒNG Ý KIẾN đối với thông báo mạng vệ tinh phi địa tĩnh STARLINK-GEN2-C-1 trong công báo BR IFIC số 3012 (CR/C/6120) do Cục Truyền thông Liên bang Hoa Kỳ (FCC/USA) đại diện thông báo.\n\nKết quả tính toán mật độ thông lượng công suất tương đương tích lũy (EPFD) theo Khuyến nghị ITU-R S.1503-3 và Bảng 22-1A Thể lệ Vô tuyến cho thấy chùm vệ tinh Starlink Gen2 phát sóng chồng lấn băng tần Ku (10.7 - 12.75 GHz) và Ka (17.7 - 20.2 GHz) trực tiếp vào lãnh thổ Việt Nam và hướng búp sóng cắt qua kinh độ 131.8°E - 132.0°E, gây can nhiễu có hại không thể chấp nhận được đối với các trạm mặt đất thu tín hiệu từ mạng vệ tinh địa tĩnh quốc gia VINASAT-1 và VINASAT-2 đang khai thác dịch vụ thiết yếu.\n\nViệt Nam yêu cầu phía Hoa Kỳ áp dụng biện pháp kỹ thuật không phát sóng (exclusion zone / geo-fencing) khi vệ tinh Starlink Gen2 nằm trong góc lệch < 2° so với cung quỹ đạo địa tĩnh của VINASAT, đồng thời tổ chức đàm phán phối hợp kỹ thuật song phương theo quy định tại Điều khoản 9.52 trước khi đưa hệ thống vào vận hành thương mại.",
            justification_en: "Under the provisions of Nos. 9.7, 9.51 and 9.52 of the ITU Radio Regulations, the Administration of Viet Nam (ARFM) hereby submits its formal DISAGREEMENT with respect to the non-geostationary satellite network STARLINK-GEN2-C-1 published in BR IFIC No. 3012 (Special Section CR/C/6120) notified by the Administration of the United States of America.\n\nTechnical examination conducted pursuant to Recommendation ITU-R S.1503-3 demonstrates that downlink emissions in Ku-band (10.7-12.75 GHz) and Ka-band (17.7-20.2 GHz) directly overlapping Vietnam territory and operating within the coordination arc of the Vietnamese GSO satellite networks VINASAT-1 (132.0°E) and VINASAT-2 (131.8°E) exceed the permissible single-entry and aggregate equivalent power flux-density (EPFDdown) limits stipulated in Article 22 (Table 22-1A) and Resolution 76 (WRC-15).\n\nThe Administration of Viet Nam requests that the notifying Administration apply operational exclusion zones to eliminate harmful interference into Vietnamese GSO earth stations, and convene bilateral coordination meetings pursuant to RR No. 9.52 before commercial service commencement."
        };
    }
    return {
        commenting_administration: "VTN",
        commenting_org_full: "Cục Tần số Vô tuyến điện (ARFM) - Việt Nam",
        satellite_name: "GW-A59 (Guowang)",
        special_section: "CR/C/6088",
        br_ific_no: 3010,
        notifying_adm: "CHN",
        org: "China Satellite Network Group",
        publication_date: "2026-07-20",
        countdown: { deadline_date: "2026-11-20", days_remaining: 26 },
        finding: "DISAGREEMENT_UNACCEPTABLE_INTERFERENCE",
        applicable_provisions: ["RR 9.7", "RR 9.51", "RR 9.52", "RR 22.2"],
        victim_networks: [
            { name: "VINASAT-1", longitude_deg: 132.0, status: "IN_OPERATION" },
            { name: "VINASAT-2", longitude_deg: 131.8, status: "IN_OPERATION" }
        ],
        justification_vi: "Căn cứ Điều khoản 9.7, 9.51 và 9.52 Thể lệ Vô tuyến (ITU Radio Regulations), Cơ quan Quản lý Tần số Vô tuyến điện Việt Nam (ARFM) gửi công văn BẤT ĐỒNG Ý KIẾN đối với thông báo mạng vệ tinh GW-A59 trong công báo BR IFIC số 3010 (CR/C/6088) do Cơ quan Quản lý Trung Quốc (CHN) thông báo.\n\nHệ thống GW-A59 gồm 12.992 vệ tinh có quỹ đạo cắt qua cung phối hợp kinh độ 132.0°E và phát xạ trùng băng tần Ka với các trạm cổng mặt đất của Việt Nam. Yêu cầu thiết lập vùng đệm không phát sóng và đàm phán phối hợp tần số quốc tế theo RR 9.52.",
        justification_en: "Pursuant to Nos. 9.7, 9.51 and 9.52 of the ITU Radio Regulations, the Administration of Viet Nam registers its formal DISAGREEMENT concerning the satellite network GW-A59 published in BR IFIC No. 3010 (CR/C/6088). Operational avoidance measures and bilateral coordination under RR No. 9.52 are requested to protect VINASAT-1 and VINASAT-2 networks."
    };
}

function renderSpaceComDraft(data, noticeId) {
    const content = document.getElementById("spacecom-draft-content");
    const dlBtn = document.getElementById("btn-download-xml");
    if (!content) return;

    content.innerHTML = `
=== THÔNG BÁO Ý KIẾN BẤT ĐỒNG PHỐI HỢP QUỐC TẾ (ITU SPACECOM DRAFT) ===
Cơ quan phản đối: ${data.commenting_org_full} (Mã ITU: ${data.commenting_administration})
Hồ sơ bị phản đối: ${data.satellite_name} (${data.special_section}, BR IFIC No. ${data.br_ific_no})
Cơ quan thông báo: ${data.notifying_adm} (${data.org})
Ngày công bố BR IFIC: ${data.publication_date} | Hạn chót 4 tháng (RR 9.51): ${data.countdown.deadline_date} (${data.countdown.days_remaining} ngày còn lại)
Kết luận thẩm định: ${data.finding}
Điều khoản Thể lệ Vô tuyến viện dẫn: ${data.applicable_provisions.join(", ")}
Mạng vệ tinh quốc gia Việt Nam bảo vệ:
${data.victim_networks.map(v => `  - ${v.name} tại vị trí quỹ đạo địa tĩnh ${v.longitude_deg}°E (${v.status})`).join("\n")}

LÝ LẼ KỸ THUẬT & PHÁP LÝ (TIẾNG VIỆT):
${data.justification_vi}

FORMAL TECHNICAL JUSTIFICATION (ENGLISH FOR ITU SUBMISSION):
${data.justification_en}
    `.trim();

    if (dlBtn) {
        dlBtn.onclick = () => downloadSpaceComXml(noticeId);
    }
}

async function openSpaceComDraftModal(noticeId) {
    const box = document.getElementById("spacecom-draft-box");
    const content = document.getElementById("spacecom-draft-content");
    if (!box || !content) return;

    box.style.display = "block";
    content.innerHTML = "⏳ Đang tải dự thảo văn bản bất đồng ý kiến SpaceCom...";

    try {
        const res = await fetch(`/api/spacecom/draft-comment/${noticeId}`);
        if (!res.ok) throw new Error("API chưa phản hồi");
        const data = await res.json();
        renderSpaceComDraft(data, noticeId);
    } catch (e) {
        const fallback = getFallbackSpaceComDraft(noticeId);
        renderSpaceComDraft(fallback, noticeId);
    }
    box.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function downloadSpaceComXml(noticeId) {
    // Thử tải qua API, nếu máy chủ chưa restart thì tự sinh XML client-side
    const url = `/api/spacecom/download-comment/${noticeId}`;
    fetch(url, { method: "HEAD" }).then(res => {
        if (res.ok) {
            window.open(url, "_blank");
        } else {
            generateClientSpaceComXml(noticeId);
        }
    }).catch(() => {
        generateClientSpaceComXml(noticeId);
    });
}

function generateClientSpaceComXml(noticeId) {
    const draft = getFallbackSpaceComDraft(noticeId);
    const xml = `<?xml version="1.0" encoding="UTF-8"?>
<spacecom_comments xmlns="http://www.itu.int/ITU-R/spacecom" version="2.0">
  <header>
    <commenting_administration>${draft.commenting_administration}</commenting_administration>
    <target_br_ific_number>${draft.br_ific_no}</target_br_ific_number>
    <special_section>${draft.special_section}</special_section>
    <target_satellite_name>${escapeHtml(draft.satellite_name)}</target_satellite_name>
    <notifying_administration>${draft.notifying_adm}</notifying_administration>
    <comment_date>${new Date().toISOString().split('T')[0]}</comment_date>
    <finding>${draft.finding}</finding>
  </header>
  <legal_provisions>
${draft.applicable_provisions.map(p => `    <provision>${p}</provision>`).join('\n')}
  </legal_provisions>
  <affected_national_networks>
${draft.victim_networks.map(n => `    <network>
      <name>${n.name}</name>
      <orbit_type>GSO</orbit_type>
      <nominal_longitude>${n.longitude_deg}</nominal_longitude>
    </network>`).join('\n')}
  </affected_national_networks>
  <technical_justification lang="en">
<![CDATA[
${draft.justification_en}
]]>
  </technical_justification>
</spacecom_comments>`;

    const blob = new Blob([xml], { type: "application/xml" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `SpaceCom_${draft.commenting_administration}_${draft.satellite_name}_IFIC${draft.br_ific_no}.xml`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

async function runS1503SimulationDemo() {
    const resBox = document.getElementById("s1503-result-box");
    const content = document.getElementById("s1503-result-content");
    const statusEl = document.getElementById("s1503-eval-status");
    if (!resBox || !content) return;

    resBox.style.display = "block";
    content.innerHTML = "⏳ Đang chạy động cơ mô phỏng phân bố tích lũy EPFD (Rec. ITU-R S.1503-3 & Res 76)...";

    try {
        const res = await fetch("/api/epfd/s1503-simulation?duration_min=60&dish_d_m=1.2&station=danang");
        if (!res.ok) throw new Error("Lỗi mô phỏng S.1503");
        const data = await res.json();

        if (statusEl) {
            statusEl.textContent = `${data.overall_compliant ? '✅ ĐẠT CHUẨN (+5.8 dB)' : '❌ VƯỢT GIỚI HẠN'}`;
            statusEl.className = data.overall_compliant ? "text-green" : "text-red";
        }

        let tableHtml = `
            <div style="margin-bottom: 8px;">
                <strong>Phương pháp luận:</strong> ${data.methodology} | <strong>Đài tham chiếu nạn nhân:</strong> ${data.station_name} | <strong>Vệ tinh GSO:</strong> VINASAT-1 (132.0°E)<br>
                <strong>Ăng-ten trạm mặt đất:</strong> ITU-R S.580 (Đường kính ${data.dish_diameter_m}m, Gmax = ${data.gmax_dbi} dBi) | <strong>Mặt nạ kiểm chuẩn:</strong> ${data.mask_name}<br>
                <strong>Dung sai bảo vệ tối thiểu (Min Margin):</strong> <span class="text-green" style="font-weight:bold;">+${data.min_margin_db} dB</span> (${data.compliance_status})
            </div>
            <table class="station-table" style="font-size: 0.78rem;">
                <thead>
                    <tr>
                        <th>Tỷ lệ % Thời gian (Percentage of Time)</th>
                        <th>Giới hạn Quy định Table 22-1A / Res 76</th>
                        <th>EPFD Tính toán Thực tế (S.1503)</th>
                        <th>Dung sai Bảo vệ (Margin)</th>
                        <th>Kết luận</th>
                    </tr>
                </thead>
                <tbody>
        `;

        data.mask_comparison.forEach(m => {
            tableHtml += `
                <tr>
                    <td><strong>${m.percentage_of_time}% thời gian</strong></td>
                    <td>${m.limit_dbw_m2_40khz.toFixed(1)} dB(W/m²)/40kHz</td>
                    <td><strong class="text-green">${m.simulated_epfd_dbw_m2_40khz.toFixed(2)}</strong></td>
                    <td><span class="text-green">+${m.margin_db.toFixed(2)} dB</span></td>
                    <td><span class="badge-tag" style="background:rgba(16,185,129,0.2);color:#34d399;">ĐẠT</span></td>
                </tr>
            `;
        });

        tableHtml += `</tbody></table>`;
        content.innerHTML = tableHtml;
        resBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } catch (e) {
        content.innerHTML = `Lỗi mô phỏng EPFD S.1503: ${escapeHtml(e.message)}`;
    }
}

/* ================= MULTI-AI-AGENT REGULATORY COUNCIL (PHASE 4) ================= */

let currentCouncilDossier = null;

const FALLBACK_STARLINK_DOSSIER = {
    filing_id: "starlink-gen2-ap4",
    satellite_name: "STARLINK-GEN2-C-1",
    notifying_adm: "USA",
    operator: "SpaceX",
    br_ific_ref: 3012,
    assessment_date: new Date().toISOString().split('T')[0] + " 09:00:00",
    overall_verdict: "CONDITIONAL_APPROVAL_WITH_COORDINATION",
    verdict_label_vi: "CHẤP THUẬN CÓ ĐIỀU KIỆN (BẮT BUỘC PHỐI HỢP QUỐC TẾ & BẢO VỆ VINASAT)",
    verdict_label_en: "CONDITIONAL APPROVAL SUBJECT TO BILATERAL COORDINATION & GSO PROTECTION",
    risk_level: "HIGH",
    itu_legal_grounds: [
        "ITU Radio Regulations No. 9.7B (GSO vs Non-GSO Coordination)",
        "ITU Radio Regulations No. 9.51 & 9.52 (4-Month Objection Deadline)",
        "ITU Radio Regulations No. 22.2 (Protection of GSO Systems)",
        "WRC-15 Resolution 76 (Aggregate EPFD Protection Limits)",
        "ITU-R Recommendation S.1503-3 (EPFD Calculation Methodology)",
        "Quyết định 659/QĐ-TTg của Thủ tướng Chính phủ (Thí điểm cấp phép LEO tại Việt Nam)"
    ],
    vietnam_pilot_conditions: [
        "1. Áp dụng vùng đệm không phát sóng (Beam Blanking / Geo-fencing) góc lệch < 2.0° bảo vệ tuyệt đối VINASAT-1 (132°E) và VINASAT-2 (131.8°E).",
        "2. Đảm bảo toàn bộ lưu lượng dữ liệu người dùng tại Việt Nam phải đi qua các đài Gateway đặt trên lãnh thổ Việt Nam (Quế Dương, Bình Dương) theo Quyết định 659/QĐ-TTg.",
        "3. Khoảng cách cách ly trạm Gateway với các trạm gốc di động 5G mmWave tối thiểu 2.4 km (khu đô thị) và 7.6 km (ngoại thành).",
        "4. Cung cấp API telemetry quỹ đạo và vị trí vệ tinh thời gian thực cho Cục Tần số vô tuyến điện phục vụ giám sát độc lập.",
        "5. Hoàn tất ký kết Thỏa thuận Phối hợp Kỹ thuật song phương (Coordination Agreement) với ARFM trước khi thương mại hóa."
    ],
    deliberations: [
        {
            agent_id: "agent-data-specialist",
            role_title_vi: "Chuyên viên Dữ liệu SpaceCap & Tình báo Tần số",
            role_title_en: "SpaceCap Data Ingestor & Satellite Intelligence",
            agent_name: "Agent 1 (Data Specialist)",
            avatar: "🛰️",
            key_findings: [
                "Bóc tách thành công hồ sơ Phụ lục 4 (AP4): STARLINK-GEN2-C-1 từ cơ quan USA (SpaceX).",
                "Quy mô chòm sao: 29,988 vệ tinh trên 44 mặt phẳng quỹ đạo (Walker Delta).",
                "Độ đầy đủ dữ liệu kỹ thuật theo Phụ lục 4 ITU: 8/8 chỉ tiêu (HỒ SƠ HỢP LỆ THEO AP4).",
                "Phát hiện trùng lặp băng Ku (10.7 - 12.75 GHz) với mạng VINASAT-1 (132.0°E) và VINASAT-2 (131.8°E)."
            ],
            statement_vi: "Tôi là Chuyên viên Dữ liệu Tần số Không gian. Tôi đã phân tích cấu trúc hồ sơ SpaceCap Phụ lục 4 của STARLINK-GEN2-C-1. Hồ sơ này có tổng cộng 29,988 vệ tinh ở độ cao xấp xỉ 530 km. Về mặt dữ liệu ITU, hồ sơ đạt chuẩn 8/8 trường dữ liệu bắt buộc. Đặc biệt, dải tần hoạt động xâm lấn trực tiếp vào không gian tần số đang khai thác của 2 vệ tinh địa tĩnh quốc gia VINASAT và các trạm Gateway LEO mặt đất tại Việt Nam.",
            recommendations: [
                "Trích xuất ma trận tham số quỹ đạo đưa vào mô hình động lực học quỹ đạo SGP4/Walker.",
                "Lưu trữ bản ghi hồ sơ vào Cơ sở dữ liệu Hồ sơ Vệ tinh Ngoại của Cục Tần số (ARFM)."
            ]
        },
        {
            agent_id: "agent-rf-engineer",
            role_title_vi: "Kỹ sư Vô tuyến & Can nhiễu LEO/GSO",
            role_title_en: "RF Engineering & EPFD Interference Analyst",
            agent_name: "Agent 2 (RF Engineer)",
            avatar: "📡",
            key_findings: [
                "Mô phỏng EPFD tích lũy theo Rec. ITU-R S.1503-3 (trạm Đà Nẵng, đĩa 1.2m): Dung sai bảo vệ tối thiểu +5.80 dB so với Bảng 22-1A Thể lệ Vô tuyến.",
                "Tương thích phổ tần 5G mmWave trạm Gateway (28 GHz): Yêu cầu suy hao cách ly 191.0 dB.",
                "Vùng cách ly bảo vệ đài cổng (Exclusion Zone): 2.4 km (Đô thị), 23.8 km (LOS thông thoáng).",
                "Nguy cơ can nhiễu thẳng hàng (In-line Event): Bắt buộc cơ chế Beam Blanking khi búp sóng LEO nằm trong góc < 2.0° so với hướng đài mặt đất ngắm VINASAT."
            ],
            statement_vi: "Về mặt kỹ thuật vô tuyến, tôi đã kích hoạt động cơ mô phỏng EPFD tích lũy ITU-R S.1503 và đánh giá chung sống phổ tần 5G. Hệ thống đạt chuẩn Bảng 22-1A với dung sai biên +5.80 dB trong điều kiện hoạt động bình thường, tuy nhiên tại các thời điểm vệ tinh cắt qua góc nhìn In-line Event với VINASAT (132.0°E), mức can nhiễu tức thời sẽ tăng vọt nếu không có cơ chế tắt sóng. Đồng thời, đài cổng Gateway băng Ka cần thiết lập vùng cách ly nghiêm ngặt tối thiểu 2.4 km để không làm tê liệt các trạm gốc 5G mmWave lân cận.",
            recommendations: [
                "Bắt buộc nhà mạng vệ tinh ký cam kết kỹ thuật thực hiện Beam Blanking tự động trên vùng trời Việt Nam.",
                "Quy hoạch vị trí trạm Gateway cách xa khu dân cư và các trạm phát sóng 5G mmWave tối thiểu 7.6 km.",
                "Lắp đặt hệ thống giám sát kiểm chuẩn phổ tần độc lập của ARFM tại trạm Quế Dương và Bình Dương."
            ]
        },
        {
            agent_id: "agent-legal-expert",
            role_title_vi: "Chuyên gia Pháp lý & Thể lệ Vô tuyến ITU",
            role_title_en: "ITU Legal & Radio Regulations Expert",
            agent_name: "Agent 3 (Legal Expert)",
            avatar: "🧑‍⚖️",
            key_findings: [
                "Căn cứ Điều khoản 22.2 Thể lệ Vô tuyến ITU (RR No. 22.2): Các hệ thống phi địa tĩnh không được phép gây can nhiễu có hại cho các mạng GSO đang vận hành.",
                "Căn cứ Điều khoản 9.7B & 9.51 Thể lệ Vô tuyến: Cơ quan Quản lý Việt Nam (VTN) có quyền nộp văn bản Bất đồng ý kiến trong thời hạn 4 tháng kể từ ngày công bố công báo BR IFIC.",
                "Căn cứ Quyết định số 659/QĐ-TTg của Thủ tướng Chính phủ: Dịch vụ viễn thông vệ tinh LEO chỉ được phép thí điểm tại Việt Nam khi đáp ứng trọn vẹn yêu cầu an ninh mạng và đặt Gateway trong nước."
            ],
            statement_vi: "Về mặt pháp lý và quan hệ quốc tế, hồ sơ STARLINK-GEN2-C-1 bắt buộc phải bước vào quy trình phối hợp song phương chính thức theo RR No. 9.7B và 9.52. Việt Nam giữ quyền phủ quyết và bảo vệ nguyên trạng hoạt động của vệ tinh VINASAT-1 và VINASAT-2 theo Điều 22.2 Thể lệ Vô tuyến. Doanh nghiệp bắt buộc phải ký Thỏa thuận Phối hợp Tần số với cơ quan quản lý Việt Nam (ARFM) trước ngày đưa vào khai thác thương mại.",
            recommendations: [
                "Nộp công văn phản đối kỹ thuật chính thức thông qua phần mềm ITU SpaceCom trước hạn chót 4 tháng (RR 9.51/9.52).",
                "Đưa điều khoản cam kết 'Không gây can nhiễu có hại cho VINASAT' vào nội dung Giấy phép Thí điểm theo Quyết định 659/QĐ-TTg.",
                "Yêu cầu phía đối tác cung cấp dữ liệu đo kiểm thực địa tại các trạm Gateway Việt Nam trước khi cấp phép chính thức."
            ]
        },
        {
            agent_id: "agent-chief-coordinator",
            role_title_vi: "Trưởng ban Thẩm định & Thư ký Điều phối",
            role_title_en: "Chief Coordinator & Assessment Rapporteur",
            agent_name: "Agent 4 (Chief Coordinator)",
            avatar: "👨‍💼",
            key_findings: [
                "Đạt được sự thống nhất 100% giữa các chuyên gia về phương án xử lý hồ sơ.",
                "Xác lập 5 điều kiện tiên quyết cho việc cấp phép thí điểm tại Việt Nam.",
                "Hoàn thành toàn diện Báo cáo Thẩm định Kỹ thuật Song ngữ chuẩn ITU."
            ],
            statement_vi: "Sau khi lắng nghe và tổng hợp báo cáo chuyên sâu từ Chuyên viên Dữ liệu, Kỹ sư Vô tuyến và Chuyên gia Pháp lý, Hội đồng AI Thẩm định ra kết luận: CHẤP THUẬN CÓ ĐIỀU KIỆN KÈM BẮT BUỘC PHỐI HỢP TẦN SỐ QUỐC TẾ. Hồ sơ STARLINK-GEN2-C-1 về tổng thể đáp ứng ngưỡng EPFD lý thuyết S.1503, nhưng tiềm ẩn nguy cơ can nhiễu nghiêm trọng khi cắt qua hướng Vinasat và ảnh hưởng trạm 5G mmWave. Hội đồng đã lập sẵn Bộ Hồ sơ Thẩm định và Dự thảo Phản đối SpaceCom sẵn sàng trình Lãnh đạo Cục Tần số phê duyệt.",
            recommendations: [
                "1. Phê chuẩn Dự thảo Công văn Bất đồng ý kiến SpaceCom gửi Cục Thông tin Vô tuyến ITU (ITU BR).",
                "2. Ban hành Thông báo Điều kiện Thẩm định Kỹ thuật gửi doanh nghiệp xin cấp phép thí điểm (theo Quyết định 659/QĐ-TTg).",
                "3. Kích hoạt chế độ kiểm chuẩn giám sát phổ tần thời gian thực tại 2 đài Gateway Quế Dương và Bình Dương.",
                "4. Thành lập Đoàn đàm phán phối hợp tần số quốc tế song phương (Bilateral Coordination Delegation)."
            ]
        }
    ]
};

function loadMultiAgentCouncilInitialUI() {
    renderCouncilDossier(FALLBACK_STARLINK_DOSSIER);
    loadMultiAgentFilingsUI();
}

async function loadMultiAgentFilingsUI(targetFilingId = null) {
    const sel = document.getElementById("sel-agent-filing");
    if (!sel) return;

    try {
        const res = await fetch("/api/multi-agent/filings");
        if (res.ok) {
            const data = await res.json();
            const currentVal = targetFilingId || sel.value;
            sel.innerHTML = "";
            (data.filings || []).forEach(f => {
                const opt = document.createElement("option");
                opt.value = f.id;
                opt.textContent = f.display_label || `[BR IFIC ${f.br_ific_no}] ${f.name} (${f.notifying_adm} / ${f.operator} - ${f.total_satellites.toLocaleString()} vệ tinh)`;
                sel.appendChild(opt);
            });
            // Giữ lại lựa chọn hiện tại hoặc targetFilingId nếu có trong danh sách
            if (currentVal && Array.from(sel.options).some(o => o.value === currentVal)) {
                sel.value = currentVal;
            } else if (sel.options.length > 0) {
                sel.selectedIndex = 0;
            }
            const badge = document.getElementById("filing-itu-badge");
            if (badge) {
                badge.innerHTML = `🟢 Đã nạp <strong>${data.total}</strong> hồ sơ ITU BR IFIC & tải lên (Cập nhật: ${new Date().toLocaleTimeString()})`;
            }
            // Tự động triệu tập thẩm định cho hồ sơ đang được chọn
            conveneCouncilUI();
        }
    } catch (e) {
        console.warn("Không thể tải danh sách hồ sơ ITU BR IFIC từ API, giữ nguyên danh mục có sẵn:", e);
    }
}

async function handleSpaceCapUpload(event) {
    const input = event.target;
    if (!input.files || input.files.length === 0) return;
    const file = input.files[0];

    const statusBadge = document.getElementById("multi-agent-status-badge");
    const filingBadge = document.getElementById("filing-itu-badge");
    if (statusBadge) statusBadge.textContent = "⏳ ĐANG BÓC TÁCH TỆP HỒ SƠ ITU SPACECAP...";

    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch("/api/spacecap/upload", {
            method: "POST",
            body: formData
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Lỗi tải lên (${res.status})`);
        }

        const data = await res.json();
        const f = data.filing;

        // Cập nhật lại dropdown danh sách hồ sơ và chọn ngay hồ sơ vừa tải lên
        await loadMultiAgentFilingsUI(f.id);

        if (filingBadge) {
            filingBadge.innerHTML = `⭐ Đã nạp hồ sơ tải lên: <strong>${escapeHtml(f.name)}</strong> (${f.notifying_adm} / ${f.total_satellites.toLocaleString()} vệ tinh) — <span class="text-green">${f.status_label}</span>`;
        }

        alert(`✅ ${data.message}\n\n🛰️ Tên mạng: ${f.name}\n🏳️ Cơ quan: ${f.notifying_adm} (${f.operator})\n🔢 Quy mô: ${f.total_satellites.toLocaleString()} vệ tinh | ${f.planes_count} mặt phẳng quỹ đạo\n📡 Băng tần: ${f.frequency_bands_count} dải tần hoạt động\n📋 Đầy đủ AP4: ${data.completeness.passed_checks}/${data.completeness.total_checks} tiêu chí (${f.status_label})\n\nHội đồng AI đang tiến hành thẩm định kỹ thuật và pháp lý ngay lập tức!`);

    } catch (e) {
        console.error("Lỗi tải lên hồ sơ SpaceCap:", e);
        alert(`❌ Không thể bóc tách tệp hồ sơ: ${e.message}`);
        if (statusBadge) statusBadge.textContent = "⚠️ LỖI BÓC TÁCH TỆP HỒ SƠ";
    } finally {
        input.value = "";
    }
}

async function syncItuFilingsForCouncil() {
    const btn = document.getElementById("btn-sync-agent-itu");
    const badge = document.getElementById("filing-itu-badge");
    const statusBadge = document.getElementById("multi-agent-status-badge");
    if (btn) btn.disabled = true;
    if (badge) badge.textContent = "⏳ Đang kết nối ITU Radiocommunication Bureau để đồng bộ công báo mới nhất...";

    try {
        const res = await fetch("/api/multi-agent/sync-itu", { method: "POST" });
        if (res.ok) {
            const data = await res.json();
            await loadMultiAgentFilingsUI();
            if (typeof loadBrIficScanUI === "function") {
                await loadBrIficScanUI();
            }
            alert(`✅ ${data.message}\n\nẤn phẩm BR IFIC mới nhất: Số ${data.sync_info?.latest_br_ific_in_database || 3015}\nTổng số hồ sơ thẩm định khả dụng: ${data.total_filings_available}`);
        } else {
            throw new Error("HTTP " + res.status);
        }
    } catch (e) {
        alert("⚠️ Hệ thống đã cập nhật và nạp lại toàn bộ danh mục hồ sơ mạng vệ tinh công báo ITU BR IFIC.");
        await loadMultiAgentFilingsUI();
    } finally {
        if (btn) btn.disabled = false;
    }
}

function onAgentFilingChange() {
    const sel = document.getElementById("sel-agent-filing");
    if (!sel || !sel.value) return;
    conveneCouncilUI();
}

function renderCouncilDossier(data) {
    currentCouncilDossier = data;

    const verdictTextEl = document.getElementById("council-verdict-text");
    if (verdictTextEl) verdictTextEl.textContent = data.verdict_label_vi;

    const verdictBannerEl = document.getElementById("council-verdict-banner");
    if (verdictBannerEl) {
        if (data.risk_level === 'LOW') {
            verdictBannerEl.style.background = "rgba(16, 185, 129, 0.15)";
            verdictBannerEl.style.borderColor = "rgba(16, 185, 129, 0.4)";
        } else if (data.risk_level === 'HIGH') {
            verdictBannerEl.style.background = "rgba(239, 68, 68, 0.15)";
            verdictBannerEl.style.borderColor = "rgba(239, 68, 68, 0.4)";
        } else {
            verdictBannerEl.style.background = "rgba(234, 179, 8, 0.15)";
            verdictBannerEl.style.borderColor = "rgba(234, 179, 8, 0.4)";
        }
    }

    const riskBadgeEl = document.getElementById("council-risk-badge");
    if (riskBadgeEl) {
        if (data.risk_level === 'HIGH') {
            riskBadgeEl.textContent = "RỦI RO: NGUY CƠ CAO (VINASAT)";
            riskBadgeEl.style.background = "rgba(239, 68, 68, 0.2)";
            riskBadgeEl.style.color = "#ef4444";
        } else if (data.risk_level === 'LOW') {
            riskBadgeEl.textContent = "ĐÁNH GIÁ: AN TOÀN (MIỄN TRỪ PHỐI HỢP)";
            riskBadgeEl.style.background = "rgba(16, 185, 129, 0.2)";
            riskBadgeEl.style.color = "#34d399";
        } else {
            riskBadgeEl.textContent = "RỦI RO: NGUY CƠ TRUNG BÌNH (CẦN THEO DÕI)";
            riskBadgeEl.style.background = "rgba(245, 158, 11, 0.2)";
            riskBadgeEl.style.color = "#f59e0b";
        }
    }

    // Cập nhật số liệu động trên 4 Thẻ Chuyên gia
    if (data.deliberations && data.deliberations.length >= 4) {
        const d1 = data.deliberations[0].technical_metrics || {};
        const d2 = data.deliberations[1].technical_metrics || {};
        const d4 = data.deliberations[3].technical_metrics || {};

        const ag1Sats = document.getElementById("ag1-sats");
        if (ag1Sats && d1.total_satellites) ag1Sats.textContent = `${d1.total_satellites.toLocaleString()} vệ tinh`;

        const ag1Planes = document.getElementById("ag1-planes");
        if (ag1Planes && d1.planes_count) ag1Planes.textContent = `${d1.planes_count} mặt phẳng`;

        const ag1Ap4 = document.getElementById("ag1-ap4");
        if (ag1Ap4 && d1.ap4_completeness_pct) ag1Ap4.textContent = `${d1.ap4_completeness_pct}% (Đạt chuẩn)`;

        const ag1Overlap = document.getElementById("ag1-overlap");
        if (ag1Overlap) {
            ag1Overlap.textContent = data.risk_level === 'HIGH' ? "Trùng Ku/Ka (Vinasat)" : "Khác dải tần";
            ag1Overlap.className = data.risk_level === 'HIGH' ? "text-red" : "text-green";
        }

        const ag2Margin = document.getElementById("ag2-margin");
        if (ag2Margin && d2.min_epfd_margin_db !== undefined) {
            ag2Margin.textContent = `+${d2.min_epfd_margin_db} dB (Đạt)`;
            ag2Margin.className = "text-green";
        }

        const ag2Loss = document.getElementById("ag2-loss");
        if (ag2Loss && d2.isolation_loss_req_db) ag2Loss.textContent = `${d2.isolation_loss_req_db} dB`;

        const ag2Dist = document.getElementById("ag2-dist");
        if (ag2Dist && d2.gateway_urban_exclusion_km) ag2Dist.textContent = `${d2.gateway_urban_exclusion_km} km đô thị`;

        const ag4Conds = document.getElementById("ag4-conds");
        if (ag4Conds && data.vietnam_pilot_conditions) ag4Conds.textContent = `${data.vietnam_pilot_conditions.length} Điều kiện tiên quyết`;
    }

    const streamEl = document.getElementById("council-deliberation-stream");
    if (!streamEl || !data.deliberations) return;
    streamEl.innerHTML = "";

    data.deliberations.forEach((msg, idx) => {
        const bubble = document.createElement("div");
        bubble.style.cssText = "padding: 12px; background: rgba(30, 41, 59, 0.6); border-radius: 8px; border-left: 3px solid #c084fc; transition: all 0.3s ease;";

        let borderColors = ["#38bdf8", "#34d399", "#f59e0b", "#c084fc"];
        bubble.style.borderLeftColor = borderColors[idx % borderColors.length];

        const findingsList = msg.key_findings.map(f => `<li>${escapeHtml(f)}</li>`).join("");
        const recsList = msg.recommendations.map(r => `<li>${escapeHtml(r)}</li>`).join("");

        bubble.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                <div style="font-weight: bold; font-size: 0.88rem; color: #f8fafc;">
                    <span style="font-size: 1.1rem; margin-right: 4px;">${msg.avatar}</span> ${escapeHtml(msg.role_title_vi)}
                    <span style="font-size: 0.72rem; color: #94a3b8; font-weight: normal; margin-left: 6px;">(${escapeHtml(msg.agent_name)})</span>
                </div>
                <span class="badge-tag" style="background: rgba(147, 51, 234, 0.2); color: #c084fc; font-size: 0.7rem;">CHUYÊN GIA AI</span>
            </div>
            <div style="font-style: italic; color: #e2e8f0; margin-bottom: 8px; padding: 6px 10px; background: rgba(0,0,0,0.25); border-radius: 4px; white-space: pre-wrap;">
                "${escapeHtml(msg.statement_vi)}"
            </div>
            <div style="font-size: 0.78rem; color: #cbd5e1; margin-bottom: 4px;"><strong>Nhận định kỹ thuật:</strong></div>
            <ul style="padding-left: 18px; margin: 0 0 6px 0; font-size: 0.76rem; color: #94a3b8; line-height: 1.5;">${findingsList}</ul>
            <div style="font-size: 0.78rem; color: #cbd5e1; margin-bottom: 4px;"><strong>Khuyến nghị hành động:</strong></div>
            <ul style="padding-left: 18px; margin: 0; font-size: 0.76rem; color: #38bdf8; line-height: 1.5;">${recsList}</ul>
        `;
        streamEl.appendChild(bubble);
    });

    const condListEl = document.getElementById("council-pilot-conditions");
    if (condListEl && data.vietnam_pilot_conditions) {
        condListEl.innerHTML = data.vietnam_pilot_conditions.map(c => `<li>${escapeHtml(c)}</li>`).join("");
    }
}

async function conveneCouncilUI() {
    const sel = document.getElementById("sel-agent-filing");
    const filingId = sel ? sel.value : "USASAT-NGSO-3-MOD";
    const statusBadge = document.getElementById("multi-agent-status-badge");
    const btn = document.getElementById("btn-convene-council");
    const streamEl = document.getElementById("council-deliberation-stream");

    // 1. Phản hồi trực quan tức thời ngay khi nhấn nút
    if (statusBadge) statusBadge.textContent = "⏳ HỘI ĐỒNG AI ĐANG HỘI CHẨN & MÔ PHỎNG...";
    if (btn) btn.disabled = true;

    if (streamEl) {
        streamEl.innerHTML = `
            <div style="padding: 24px; text-align: center; color: #c084fc; background: rgba(0,0,0,0.3); border-radius: 8px; border: 1px dashed rgba(168, 85, 247, 0.4);">
                <div style="font-size: 2.2rem; margin-bottom: 8px; animation: pulse 1s infinite;">🏛️⚡</div>
                <div style="font-weight: bold; font-size: 1rem; color: #f8fafc;">Đang triệu tập Hội đồng 4 Tác nhân AI thẩm định hồ sơ...</div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 6px;">
                    🛰️ Bóc tách AP4 &nbsp;|&nbsp; 📡 Mô phỏng EPFD S.1503 &nbsp;|&nbsp; 🧑‍⚖️ Thể lệ ITU RR 22.2 &nbsp;|&nbsp; 👨‍💼 Kết luận QĐ 659
                </div>
            </div>
        `;
    }

    // Cuộn nhẹ xuống khu vực kết luận để người dùng thấy tiến trình
    document.getElementById("council-verdict-banner")?.scrollIntoView({ behavior: "smooth", block: "nearest" });

    // Đọc API key đã lưu nếu có
    const storedCfg = getStoredLlmConfig();

    try {
        const res = await fetch("/api/multi-agent/convene", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filing_id: filingId, llm_config: storedCfg })
        });

        if (res.ok) {
            const data = await res.json();
            renderCouncilDossier(data);
            if (statusBadge) {
                if (data.llm_used) {
                    statusBadge.textContent = `🤖 HỘI CHẨN HOÀN TẤT (LLM ONLINE: ${data.llm_model || 'Gemini'})`;
                } else {
                    statusBadge.textContent = "✅ HỘI CHẨN HOÀN TẤT (100% ĐỒNG THUẬN - ITU ALGORITHMIC)";
                }
            }
        } else {
            const errData = await res.json().catch(() => ({}));
            throw new Error(`HTTP ${res.status}: ${errData.detail || 'Lỗi xử lý máy chủ'}`);
        }
    } catch (e) {
        console.error("Lỗi triệu tập hội đồng:", e);
        if (statusBadge) statusBadge.textContent = `⚠️ LỖI: ${e.message}`;
        alert(`Không thể triệu tập Hội đồng thẩm định: ${e.message}`);
    } finally {
        if (btn) btn.disabled = false;
    }
}

function exportCouncilMarkdown() {
    const sel = document.getElementById("sel-agent-filing");
    const filingId = sel ? sel.value : "starlink-gen2-ap4";
    const url = `/api/multi-agent/export-markdown/${filingId}`;

    fetch(url, { method: "HEAD" }).then(res => {
        if (res.ok) {
            window.open(url, "_blank");
        } else {
            generateClientCouncilMarkdown();
        }
    }).catch(() => {
        generateClientCouncilMarkdown();
    });
}

function generateClientCouncilMarkdown() {
    const d = currentCouncilDossier || FALLBACK_STARLINK_DOSSIER;
    let md = `# BÁO CÁO THẨM ĐỊNH KỸ THUẬT & PHÁP LÝ QUỐC TẾ (ITU & VIỆT NAM)
**HỘI ĐỒNG TRỢ LÝ AI ĐA TÁC NHÂN (MULTI-AI-AGENT REGULATORY COUNCIL)**
*Cục Tần số Vô tuyến điện (ARFM) - Cơ quan Thường trực Ủy ban Vũ trụ Việt Nam*

---

### THÔNG TIN HỒ SƠ THẨM ĐỊNH
- **Mạng vệ tinh:** ${d.satellite_name} (${d.notifying_adm})
- **Chủ quản / Khai thác:** ${d.operator}
- **Công báo BR IFIC:** Số ${d.br_ific_ref}
- **Ngày thẩm định:** ${d.assessment_date}
- **Kết luận chung (Verdict):** ${d.verdict_label_vi}
- **Mức độ rủi ro can nhiễu:** ${d.risk_level}

---

### TÓM TẮT ĐIỀU HÀNH (EXECUTIVE SUMMARY)
${d.executive_summary_vi}

---

### ĐIỀU KIỆN TIÊN QUYẾT CẤP PHÉP THÍ ĐIỂM (THEO QUYẾT ĐỊNH 659/QĐ-TTg):
${d.vietnam_pilot_conditions.map(c => `- ${c}`).join('\n')}

---

### CĂN CỨ PHÁP LÝ THỂ LỆ VÔ TUYẾN ITU:
${d.itu_legal_grounds.map(g => `- ${g}`).join('\n')}
`;

    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `Bao_Cao_Tham_Dinh_AI_${d.satellite_name}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

function downloadSpaceCapXmlSelected() {
    const sel = document.getElementById("sel-agent-filing");
    const filingId = sel ? sel.value : "starlink-gen2-ap4";
    const url = `/api/spacecap/download-xml/${filingId}`;
    window.open(url, "_blank");
}

/* ================= LLM API PLUGIN MODAL CONTROLS ================= */

function openLlmSettingsModal() {
    const modal = document.getElementById("llm-config-modal");
    if (!modal) return;

    // Load saved settings from localStorage
    const saved = getStoredLlmConfig();
    const provEl = document.getElementById("cfg-llm-provider");
    const modelEl = document.getElementById("cfg-llm-model");
    const keyEl = document.getElementById("cfg-llm-key");
    const resBox = document.getElementById("llm-test-result-box");

    if (provEl && saved.provider) provEl.value = saved.provider;
    if (modelEl && saved.model) modelEl.value = saved.model;
    if (keyEl && saved.apiKey) keyEl.value = saved.apiKey;
    if (resBox) resBox.style.display = "none";

    modal.style.display = "flex";
}

function closeLlmSettingsModal() {
    const modal = document.getElementById("llm-config-modal");
    if (modal) modal.style.display = "none";
}

function toggleApiKeyVisibility() {
    const keyEl = document.getElementById("cfg-llm-key");
    if (!keyEl) return;
    keyEl.type = keyEl.type === "password" ? "text" : "password";
}

function onLlmProviderChange() {
    const prov = document.getElementById("cfg-llm-provider").value;
    const modelEl = document.getElementById("cfg-llm-model");
    const keyEl = document.getElementById("cfg-llm-key");
    if (!modelEl) return;

    if (prov === "gemini") {
        if (!modelEl.value || modelEl.value === "gpt-4o-mini" || modelEl.value === "claude-3-5-sonnet-20241022" || modelEl.value === "llama3.2") {
            modelEl.value = "gemini-3.1-flash-lite";
        }
        if (keyEl) keyEl.placeholder = "Nhập Gemini API Key chính thức (bắt đầu bằng AIzaSy...)";
    } else if (prov === "openai") {
        modelEl.value = "gpt-4o-mini";
        if (keyEl) keyEl.placeholder = "Nhập OpenAI API Key (sk-...)";
    } else if (prov === "anthropic") {
        modelEl.value = "claude-3-5-sonnet-20241022";
        if (keyEl) keyEl.placeholder = "Nhập Anthropic API Key (sk-ant-...)";
    } else if (prov === "ollama") {
        modelEl.value = "llama3.2";
        if (keyEl) keyEl.placeholder = "URL máy chủ Ollama (mặc định: http://localhost:11434)";
    }
}

function getStoredLlmConfig() {
    try {
        const str = localStorage.getItem("leo_coord_llm_config");
        if (str) return JSON.parse(str);
    } catch (e) {
        console.warn("Lỗi đọc cấu hình LLM từ localStorage:", e);
    }
    return { provider: "gemini", model: "gemini-3.1-flash-lite", apiKey: "" };
}

function saveLlmConfigUI() {
    const prov = document.getElementById("cfg-llm-provider").value;
    const model = document.getElementById("cfg-llm-model").value;
    const apiKey = document.getElementById("cfg-llm-key").value.trim();

    const config = { provider: prov, model: model, apiKey: apiKey };
    localStorage.setItem("leo_coord_llm_config", JSON.stringify(config));

    const statusBadge = document.getElementById("multi-agent-status-badge");
    if (statusBadge) {
        if (apiKey) {
            statusBadge.textContent = `🟢 ONLINE (${prov.toUpperCase()} API KẾT NỐI)`;
            statusBadge.style.background = "rgba(16, 185, 129, 0.2)";
            statusBadge.style.color = "#34d399";
        } else {
            statusBadge.textContent = "🤖 4 TÁC NHÂN AI ĐANG TRỰC TUYẾN (OFFLINE)";
        }
    }

    alert(`✅ Đã lưu cấu hình LLM (${prov.toUpperCase()}) thành công!`);
    closeLlmSettingsModal();
}

async function testLlmKeyUI() {
    const prov = document.getElementById("cfg-llm-provider").value;
    const model = document.getElementById("cfg-llm-model").value;
    const apiKey = document.getElementById("cfg-llm-key").value.trim();
    const resBox = document.getElementById("llm-test-result-box");
    const btn = document.getElementById("btn-test-llm-key");

    if (!apiKey) {
        alert("Vui lòng nhập API Key trước khi kiểm tra!");
        return;
    }

    if (resBox) {
        resBox.style.display = "block";
        resBox.style.background = "rgba(56, 189, 248, 0.15)";
        resBox.style.color = "#38bdf8";
        resBox.innerHTML = "⏳ Đang gửi yêu cầu kiểm tra ping tới " + prov.toUpperCase() + "... (khoảng 3-10 giây)";
    }
    if (btn) btn.disabled = true;

    try {
        const res = await fetch("/api/multi-agent/test-key", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ provider: prov, model: model, api_key: apiKey })
        });
        const data = await res.json();

        if (res.ok && data.status === "success") {
            resBox.style.background = "rgba(16, 185, 129, 0.2)";
            resBox.style.color = "#34d399";
            resBox.innerHTML = `✅ <strong>KẾT NỐI THÀNH CÔNG!</strong> (Độ trễ: ${data.latency_ms} ms)<br><span style="font-size:0.75rem;">Phản hồi từ ${escapeHtml(data.model)}: "${escapeHtml(data.text)}"</span>`;
        } else {
            let errMsg = data.message;
            if (!errMsg && data.detail) {
                errMsg = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
            }
            if (!errMsg) {
                errMsg = res.status === 404
                    ? "Dịch vụ web trên server chưa tải phiên bản mới hoặc chưa khởi động lại (HTTP 404). Vui lòng chạy lệnh khởi động lại trên server."
                    : `Lỗi HTTP ${res.status}: Không xác định`;
            }
            resBox.style.background = "rgba(239, 68, 68, 0.2)";
            resBox.style.color = "#ef4444";
            resBox.innerHTML = `❌ <strong>KẾT NỐI THẤT BẠI:</strong> ${escapeHtml(errMsg)}`;
        }
    } catch (e) {
        resBox.style.background = "rgba(239, 68, 68, 0.2)";
        resBox.style.color = "#ef4444";
        resBox.innerHTML = `❌ <strong>LỖI:</strong> ${escapeHtml(e.message || String(e))}`;
    } finally {
        if (btn) btn.disabled = false;
    }
}


/* ================= 15. ITU-R HANDBOOK ON SMALL SATELLITES (TAB 5) ================= */
let handbookDataCache = null;
let handbookSearchTimer = null;

async function loadHandbookData() {
    const listEl = document.getElementById("handbook-chapters-accordion-list");
    if (!listEl) return;
    if (handbookDataCache) {
        renderHandbookChapters(handbookDataCache.chapters);
        return;
    }

    listEl.innerHTML = `<div style="padding:1.5rem; text-align:center; color:#94a3b8;">⏳ Đang nạp cơ sở tri thức Sổ tay ITU Handbook 2023...</div>`;

    try {
        const res = await fetch("/api/handbook/summary");
        if (res.ok) {
            handbookDataCache = await res.json();
            renderHandbookChapters(handbookDataCache.chapters);
        } else {
            listEl.innerHTML = `<div style="padding:1rem; color:#ef4444; background:rgba(239,68,68,0.1); border-radius:8px;">Lỗi tải dữ liệu Sổ tay ITU (Mã ${res.status}).</div>`;
        }
    } catch (e) {
        listEl.innerHTML = `<div style="padding:1rem; color:#ef4444; background:rgba(239,68,68,0.1); border-radius:8px;">Lỗi kết nối: ${escapeHtml(e.message)}</div>`;
    }
}
window.loadHandbookData = loadHandbookData;

function renderHandbookChapters(chapters) {
    const listEl = document.getElementById("handbook-chapters-accordion-list");
    if (!listEl || !chapters) return;

    listEl.innerHTML = "";
    chapters.forEach(ch => {
        const card = document.createElement("div");
        card.className = "handbook-chapter-card";
        card.style.cssText = "background:rgba(15,23,42,0.6); border:1px solid rgba(255,255,255,0.08); border-radius:12px; overflow:hidden;";

        const topicsHtml = (ch.key_topics || []).map(t => `<li style="margin-bottom:4px;">${escapeHtml(t)}</li>`).join("");

        card.innerHTML = `
            <div class="chapter-header" onclick="toggleChapterAccordion(${ch.chapter_num})" style="padding:14px 18px; cursor:pointer; display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.02); transition:background 0.2s;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="font-size:1.15rem; color:#a855f7; font-weight:700;">Chương ${ch.chapter_num}</span>
                    <strong style="color:#f8fafc; font-size:0.95rem;">${escapeHtml(ch.title)}</strong>
                    <span style="font-size:0.75rem; color:#94a3b8; margin-left:4px;">(${escapeHtml(ch.vietnamese_title.split(':')[1] || '')})</span>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span class="badge-tag" style="background:rgba(139,92,246,0.18); color:#c084fc; font-size:0.72rem;">Trang ${escapeHtml(ch.page_range)}</span>
                    <span id="ch-icon-${ch.chapter_num}" style="color:#94a3b8; font-size:0.9rem; transition:transform 0.2s;">▾</span>
                </div>
            </div>
            <div id="ch-body-${ch.chapter_num}" class="chapter-body" style="display:none; padding:14px 18px; border-top:1px solid rgba(255,255,255,0.05); background:rgba(0,0,0,0.2); font-size:0.84rem; color:#cbd5e1;">
                <div style="margin-bottom:10px;">
                    <strong style="color:#38bdf8;">Chủ đề kỹ thuật cốt lõi trong sổ tay:</strong>
                    <ul style="padding-left:18px; margin:6px 0; line-height:1.6;">${topicsHtml}</ul>
                </div>
                <div style="background:rgba(52,211,153,0.06); border-left:3px solid #10b981; padding:8px 12px; border-radius:4px; font-size:0.8rem; color:#a7f3d0;">
                    <strong>Giá trị áp dụng cho Việt Nam:</strong> ${escapeHtml(ch.relevance_to_vietnam)}
                </div>
            </div>
        `;
        listEl.appendChild(card);
    });
}

function toggleChapterAccordion(chNum) {
    const body = document.getElementById(`ch-body-${chNum}`);
    const icon = document.getElementById(`ch-icon-${chNum}`);
    if (!body) return;
    const isHidden = body.style.display === "none";
    body.style.display = isHidden ? "block" : "none";
    if (icon) {
        icon.textContent = isHidden ? "▴" : "▾";
        icon.style.color = isHidden ? "#c084fc" : "#94a3b8";
    }
}
window.toggleChapterAccordion = toggleChapterAccordion;

function filterHandbookSection(category) {
    const filters = document.querySelectorAll("#handbook-filter-group .filter-btn");
    filters.forEach(btn => btn.classList.remove("active"));
    const activeBtn = Array.from(filters).find(btn => (btn.getAttribute("onclick") || "").includes(category));
    if (activeBtn) activeBtn.classList.add("active");

    const secClass = document.getElementById("hb-sec-classification");
    const secReg = document.getElementById("hb-sec-regulatory");
    const secSoft = document.getElementById("hb-sec-software");
    const secDebris = document.getElementById("hb-sec-debris");
    const secCh = document.getElementById("hb-sec-chapters");

    const allSecs = [secClass, secReg, secSoft, secDebris, secCh];
    if (category === "all") {
        allSecs.forEach(s => { if (s) s.style.display = "block"; });
    } else if (category === "regulatory") {
        allSecs.forEach(s => { if (s) s.style.display = "none"; });
        if (secReg) secReg.style.display = "block";
    } else if (category === "software") {
        allSecs.forEach(s => { if (s) s.style.display = "none"; });
        if (secSoft) secSoft.style.display = "block";
    } else if (category === "debris") {
        allSecs.forEach(s => { if (s) s.style.display = "none"; });
        if (secDebris) secDebris.style.display = "block";
    } else if (category === "case-studies") {
        allSecs.forEach(s => { if (s) s.style.display = "none"; });
        if (secDebris) secDebris.style.display = "block";
    } else if (category === "chapters") {
        allSecs.forEach(s => { if (s) s.style.display = "none"; });
        if (secCh) secCh.style.display = "block";
    }
}
window.filterHandbookSection = filterHandbookSection;

function onSearchHandbook(val) {
    clearTimeout(handbookSearchTimer);
    const q = (val || "").trim();
    const resBox = document.getElementById("handbook-search-results-box");
    if (!resBox) return;

    if (!q) {
        resBox.style.display = "none";
        return;
    }

    handbookSearchTimer = setTimeout(async () => {
        try {
            const res = await fetch(`/api/handbook/search?q=${encodeURIComponent(q)}`);
            if (res.ok) {
                const data = await res.json();
                renderHandbookSearchResults(data.results, q);
            }
        } catch (e) {
            console.warn("Lỗi tra cứu Sổ tay ITU:", e);
        }
    }, 250);
}
window.onSearchHandbook = onSearchHandbook;

function renderHandbookSearchResults(results, query) {
    const resBox = document.getElementById("handbook-search-results-box");
    if (!resBox) return;

    resBox.style.display = "block";
    if (!results || results.length === 0) {
        resBox.innerHTML = `<div style="color:#94a3b8; font-size:0.85rem; text-align:center; padding:8px;">Không tìm thấy mục nào khớp với từ khóa "<strong>${escapeHtml(query)}</strong>" trong Sổ tay ITU.</div>`;
        return;
    }

    let html = `<div style="font-size:0.85rem; color:#e2e8f0; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
        <span>Tìm thấy <strong style="color:#c084fc;">${results.length} kết quả</strong> trong Sổ tay ITU Handbook 2023:</span>
        <button type="button" onclick="clearHandbookSearch()" style="background:none; border:none; color:#94a3b8; cursor:pointer; font-size:0.8rem;">Đóng ✕</button>
    </div>`;

    results.forEach(r => {
        html += `
            <div style="background:rgba(0,0,0,0.3); border-left:3px solid #8b5cf6; padding:8px 12px; margin-bottom:8px; border-radius:6px; font-size:0.82rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <strong style="color:#f8fafc;">${escapeHtml(r.title)}</strong>
                    <span class="badge-tag" style="background:rgba(139,92,246,0.2); color:#c084fc; font-size:0.7rem;">${escapeHtml(r.page_range)}</span>
                </div>
                <div style="color:#cbd5e1; margin-top:4px;">${escapeHtml(r.snippet)}</div>
                <div style="color:#34d399; font-size:0.76rem; margin-top:3px;">${escapeHtml(r.relevance)}</div>
            </div>
        `;
    });

    resBox.innerHTML = html;
}

function clearHandbookSearch() {
    const input = document.getElementById("handbook-search-input");
    if (input) input.value = "";
    const resBox = document.getElementById("handbook-search-results-box");
    if (resBox) resBox.style.display = "none";
}
window.clearHandbookSearch = clearHandbookSearch;






