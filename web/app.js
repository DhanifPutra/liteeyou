// YouTube Lite — Frontend Application Logic

(function () {
  // DOM Elements variables
  let searchInput, clearSearchBtn, searchBtn, brandBtn, navHomeBtn, fullscreenToggleBtn, sidebarToggleBtn, sidebar;
  let categoryBar, refreshBtn;
  let sideHomeBtn, sideHistoryBtn, addChannelBtn, channelList;
  let sideDownloadsBtn, sideDownloadsBadge, navDownloadsBtn, navDownloadsBadge;
  let feedSection, feedTitle, feedCount, cardsGrid, loadingSkeleton, emptyState;
  let downloadsSection, dlSummaryText, openFolderBtn, clearCompletedBtn, downloadsList, emptyDownloadsState;
  let countAll, countActive, countCompleted;
  let channelModal, channelHandleInput, closeModalBtn, cancelModalBtn, saveChannelModalBtn;
  let downloadModal, closeDlModalBtn, cancelDlModalBtn, confirmDownloadBtn;
  let dlModalThumb, dlModalTitle, dlModalChannel;
  let dlFormatVideo, dlFormatAudio, dlOptionVideoLabel, dlOptionAudioLabel, dlResolutionRow, dlResolutionSelect;
  let toast;

  // State
  let currentFeed = [];
  let currentVideo = null;
  let bookmarkedChannels = [];
  let isCurrentFeedHistory = false;
  let allDownloads = [];
  let downloadsPollingTimer = null;
  let currentDlFilter = "all";
  let pendingDownloadVideo = null;

  // Original empty state text (preserved to avoid overwrite)
  const EMPTY_STATE_DEFAULT_TITLE = "Tidak ada video ditemukan";
  const EMPTY_STATE_DEFAULT_DESC = "Coba kata kunci pencarian yang lain atau periksa koneksi internet Anda.";
  const EMPTY_STATE_HISTORY_TITLE = "Belum ada riwayat tontonan";
  const EMPTY_STATE_HISTORY_DESC = "Video yang Anda putar akan otomatis tersimpan di sini.";

  // ==========================================
  // INTERNATIONALIZATION (i18n)
  // ==========================================
  const LANGS = {
    id: {
      trending: "Trending",
      searchPlaceholder: "Cari video atau tempel URL YouTube...",
      home: "Beranda",
      history: "Riwayat Tontonan",
      channelFavorites: "Channel Favorit",
      addChannel: "Tambah Channel",
      noChannels: "Belum ada channel disimpan.",
      noVideos: "Tidak ada video ditemukan",
      noVideosTip: "Coba kata kunci pencarian yang lain atau periksa koneksi internet Anda.",
      noHistory: "Belum ada riwayat tontonan",
      noHistoryTip: "Video yang Anda putar akan otomatis tersimpan di sini.",
      videoCount: (n) => `(${n} video)`,
      channelVideoCount: (n) => `(${n} video terbaru)`,
      historyVideoCount: (n) => `(${n} video tersimpan)`,
      loadingChannelVideos: "Memuat video terbaru...",
      loadError: "Gagal memuat video: ",
      channelLoadError: "Gagal memuat video channel.",
      playError: "Gagal memutar video: ",
      bookmarkSaved: (name) => `Channel "${name}" disimpan!`,
      bookmarkRemoved: (name) => `Channel "${name}" dihapus.`,
      bookmarkSaveError: "Gagal menyimpan bookmark channel.",
      bookmarkRemoveError: "Gagal menghapus bookmark.",
      downloadStarted: "Download dimulai!",
      downloadError: "Gagal memulai download.",
      removeBookmark: "Hapus dari Bookmark",
      saveChannel: "Simpan Channel",
      viewChannel: "Lihat channel",
      searchResults: (q) => `Hasil Pencarian: "${q}"`,
      channelFeed: (name) => `Channel: ${name}`,
      historyTitle: "Riwayat Tontonan",
      download: "Download",
    },
  };

  let currentLang = "id";

  function t(key, ...args) {
    const val = LANGS[currentLang]?.[key];
    if (typeof val === "function") return val(...args);
    return val || key;
  }

  // Asynchronously load modular component HTML partials
  async function loadComponents() {
    const includes = document.querySelectorAll("[data-include]");
    const errors = [];
    for (const el of includes) {
      const file = el.getAttribute("data-include");
      try {
        const res = await fetch(file);
        if (res.ok) {
          const html = await res.text();
          el.outerHTML = html;
        } else {
          errors.push(`HTTP ${res.status} for ${file}`);
          console.error(`Gagal memuat komponen: ${file} (HTTP ${res.status})`);
        }
      } catch (err) {
        errors.push(`${file}: ${err.message}`);
        console.error("Gagal memuat komponen:", file, err);
      }
    }
    if (errors.length > 0) {
      console.warn(`${errors.length} komponen gagal dimuat:`, errors);
    }
  }

  function bindDomElements() {
    searchInput = document.getElementById("searchInput");
    clearSearchBtn = document.getElementById("clearSearchBtn");
    searchBtn = document.getElementById("searchBtn");
    brandBtn = document.getElementById("brandBtn");
    navHomeBtn = document.getElementById("navHomeBtn");
    fullscreenToggleBtn = document.getElementById("fullscreenToggleBtn");
    sidebarToggleBtn = document.getElementById("sidebarToggleBtn");
    sidebar = document.getElementById("sidebar");

    categoryBar = document.getElementById("categoryBar");
    refreshBtn = document.getElementById("refreshBtn");

    sideHomeBtn = document.getElementById("sideHomeBtn");
    sideHistoryBtn = document.getElementById("sideHistoryBtn");
    sideDownloadsBtn = document.getElementById("sideDownloadsBtn");
    sideDownloadsBadge = document.getElementById("sideDownloadsBadge");
    navDownloadsBtn = document.getElementById("navDownloadsBtn");
    navDownloadsBadge = document.getElementById("navDownloadsBadge");
    addChannelBtn = document.getElementById("addChannelBtn");
    channelList = document.getElementById("channelList");

    feedSection = document.getElementById("feedSection");
    feedTitle = document.getElementById("feedTitle");
    feedCount = document.getElementById("feedCount");
    cardsGrid = document.getElementById("cardsGrid");
    loadingSkeleton = document.getElementById("loadingSkeleton");
    emptyState = document.getElementById("emptyState");

    downloadsSection = document.getElementById("downloadsSection");
    dlSummaryText = document.getElementById("dlSummaryText");
    openFolderBtn = document.getElementById("openFolderBtn");
    clearCompletedBtn = document.getElementById("clearCompletedBtn");
    downloadsList = document.getElementById("downloadsList");
    emptyDownloadsState = document.getElementById("emptyDownloadsState");

    countAll = document.getElementById("countAll");
    countActive = document.getElementById("countActive");
    countCompleted = document.getElementById("countCompleted");

    channelModal = document.getElementById("channelModal");
    channelHandleInput = document.getElementById("channelHandleInput");
    closeModalBtn = document.getElementById("closeModalBtn");
    cancelModalBtn = document.getElementById("cancelModalBtn");
    saveChannelModalBtn = document.getElementById("saveChannelModalBtn");

    downloadModal = document.getElementById("downloadModal");
    closeDlModalBtn = document.getElementById("closeDlModalBtn");
    cancelDlModalBtn = document.getElementById("cancelDlModalBtn");
    confirmDownloadBtn = document.getElementById("confirmDownloadBtn");
    dlModalThumb = document.getElementById("dlModalThumb");
    dlModalTitle = document.getElementById("dlModalTitle");
    dlModalChannel = document.getElementById("dlModalChannel");
    dlFormatVideo = document.getElementById("dlFormatVideo");
    dlFormatAudio = document.getElementById("dlFormatAudio");
    dlOptionVideoLabel = document.getElementById("dlOptionVideoLabel");
    dlOptionAudioLabel = document.getElementById("dlOptionAudioLabel");
    dlResolutionRow = document.getElementById("dlResolutionRow");
    dlResolutionSelect = document.getElementById("dlResolutionSelect");

    toast = document.getElementById("toast");
  }

  // Initialize
  async function init() {
    await loadComponents();
    bindDomElements();
    setupEventListeners();
    await loadBookmarks();
    loadCategory("Trending", "trending indonesia");
    loadDownloads();
  }

  function setupEventListeners() {
    // Brand & Nav
    if (brandBtn) brandBtn.addEventListener("click", () => showFeedView());
    if (navHomeBtn) navHomeBtn.addEventListener("click", () => showFeedView());

    // Search
    if (searchBtn) searchBtn.addEventListener("click", handleSearch);
    if (searchInput) {
      searchInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") handleSearch();
      });
      searchInput.addEventListener("input", () => {
        if (clearSearchBtn) clearSearchBtn.style.display = searchInput.value ? "block" : "none";
      });
      // Fix clear button visibility on page load (e.g. browser cache restoring value)
      if (searchInput.value && clearSearchBtn) {
        clearSearchBtn.style.display = "block";
      }
    }
    if (clearSearchBtn) {
      clearSearchBtn.addEventListener("click", () => {
        if (searchInput) {
          searchInput.value = "";
          clearSearchBtn.style.display = "none";
          searchInput.focus();
        }
      });
    }

    // Categories
    if (categoryBar) {
      categoryBar.addEventListener("click", (e) => {
        const chip = e.target.closest(".chip");
        if (!chip || chip === refreshBtn) return;
        document.querySelectorAll(".chip").forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
        const query = chip.dataset.query;
        loadCategory(chip.textContent, query);
      });
    }

    if (refreshBtn) {
      refreshBtn.addEventListener("click", () => {
        const activeChip = document.querySelector(".chip.active");
        if (activeChip) {
          loadCategory(activeChip.textContent, activeChip.dataset.query);
        } else {
          loadCategory("Trending", "trending indonesia");
        }
      });
    }

    // Sidebar
    if (sidebarToggleBtn && sidebar) {
      sidebarToggleBtn.addEventListener("click", () => {
        sidebar.classList.toggle("collapsed");
      });
    }
    if (sideHomeBtn) {
      sideHomeBtn.addEventListener("click", () => {
        showFeedView();
      });
    }
    if (sideHistoryBtn) {
      sideHistoryBtn.addEventListener("click", () => {
        setActiveSideLink(sideHistoryBtn);
        loadHistory();
      });
    }
    if (sideDownloadsBtn) {
      sideDownloadsBtn.addEventListener("click", () => {
        showDownloadsView();
      });
    }
    if (navDownloadsBtn) {
      navDownloadsBtn.addEventListener("click", () => {
        showDownloadsView();
      });
    }

    // Downloads Actions & Delegation
    if (openFolderBtn) {
      openFolderBtn.addEventListener("click", () => {
        fetch("/api/downloads/open-folder", { method: "POST" });
      });
    }

    if (clearCompletedBtn) {
      clearCompletedBtn.addEventListener("click", async () => {
        try {
          await fetch("/api/downloads/clear", { method: "POST" });
          loadDownloads();
        } catch (e) {
          console.error(e);
        }
      });
    }

    if (downloadsList) {
      downloadsList.addEventListener("click", async (e) => {
        const btn = e.target.closest("button[data-action]");
        if (!btn) return;
        const action = btn.dataset.action;
        const id = btn.dataset.id;

        try {
          if (action === "pause") {
            await fetch("/api/downloads/pause", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ id: id }),
            });
            loadDownloads();
          } else if (action === "resume") {
            await fetch("/api/downloads/resume", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ id: id }),
            });
            loadDownloads();
          } else if (action === "cancel") {
            await fetch("/api/downloads/cancel", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ id: id }),
            });
            loadDownloads();
          } else if (action === "open-file") {
            await fetch("/api/downloads/open-file", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ id: id }),
            });
          } else if (action === "open-folder") {
            await fetch("/api/downloads/open-folder", { method: "POST" });
          }
        } catch (err) {
          console.error("Action error:", err);
        }
      });
    }

    document.querySelectorAll(".dl-tab-btn").forEach((tab) => {
      tab.addEventListener("click", () => {
        document.querySelectorAll(".dl-tab-btn").forEach((t) => t.classList.remove("active"));
        tab.classList.add("active");
        currentDlFilter = tab.dataset.filter || "all";
        renderDownloads();
      });
    });

    // Bookmarks Modal
    if (addChannelBtn) {
      addChannelBtn.addEventListener("click", () => {
        if (channelHandleInput && channelModal) {
          channelHandleInput.value = "";
          channelModal.style.display = "flex";
          channelHandleInput.focus();
        }
      });
    }
    if (closeModalBtn) closeModalBtn.addEventListener("click", () => { if (channelModal) channelModal.style.display = "none"; });
    if (cancelModalBtn) cancelModalBtn.addEventListener("click", () => { if (channelModal) channelModal.style.display = "none"; });
    if (saveChannelModalBtn) saveChannelModalBtn.addEventListener("click", handleSaveChannelModal);

    // Download Modal Listeners
    if (closeDlModalBtn) closeDlModalBtn.addEventListener("click", closeDownloadModal);
    if (cancelDlModalBtn) cancelDlModalBtn.addEventListener("click", closeDownloadModal);
    if (confirmDownloadBtn) confirmDownloadBtn.addEventListener("click", handleConfirmDownload);

    if (dlOptionVideoLabel && dlOptionAudioLabel) {
      dlOptionVideoLabel.addEventListener("click", () => {
        if (dlFormatVideo) dlFormatVideo.checked = true;
        dlOptionVideoLabel.classList.add("active");
        dlOptionAudioLabel.classList.remove("active");
        if (dlResolutionRow) dlResolutionRow.style.display = "block";
      });
      dlOptionAudioLabel.addEventListener("click", () => {
        if (dlFormatAudio) dlFormatAudio.checked = true;
        dlOptionAudioLabel.classList.add("active");
        dlOptionVideoLabel.classList.remove("active");
        if (dlResolutionRow) dlResolutionRow.style.display = "none";
      });
    }

    // Fullscreen
    if (fullscreenToggleBtn) fullscreenToggleBtn.addEventListener("click", toggleFullscreen);

    // Keyboard Shortcuts (F / F11 for fullscreen, Esc to exit)
    window.addEventListener("keydown", (e) => {
      if (e.key === "F11" || (e.key.toLowerCase() === "f" && document.activeElement !== searchInput && document.activeElement !== channelHandleInput)) {
        e.preventDefault();
        toggleFullscreen();
      } else if (e.key === "Escape") {
        if (channelModal && channelModal.style.display === "flex") {
          channelModal.style.display = "none";
        }
        if (downloadModal && downloadModal.style.display === "flex") {
          closeDownloadModal();
        }
      }
    });
  }

  function setActiveSideLink(btn) {
    document.querySelectorAll(".side-link").forEach((l) => l.classList.remove("active"));
    if (btn) btn.classList.add("active");
  }

  // ==========================================
  // NAVIGATION & VIEWS
  // ==========================================
  function showFeedView() {
    if (downloadsSection) downloadsSection.style.display = "none";
    if (feedSection) feedSection.style.display = "block";
    if (categoryBar) categoryBar.style.display = "flex";
    if (navHomeBtn) navHomeBtn.classList.add("active");
    if (navDownloadsBtn) navDownloadsBtn.classList.remove("active");
    setActiveSideLink(sideHomeBtn);
  }

  function showDownloadsView() {
    if (feedSection) feedSection.style.display = "none";
    if (categoryBar) categoryBar.style.display = "none";
    if (downloadsSection) downloadsSection.style.display = "block";
    if (navHomeBtn) navHomeBtn.classList.remove("active");
    if (navDownloadsBtn) navDownloadsBtn.classList.add("active");
    setActiveSideLink(sideDownloadsBtn);
    loadDownloads();
  }

  // ==========================================
  // SEARCH & FEED FETCHING
  // ==========================================
  function handleSearch() {
    if (!searchInput) return;
    const query = searchInput.value.trim();
    if (!query) return;

    // Check if it's a direct YouTube URL
    if (isYouTubeUrl(query)) {
      const vidId = extractVideoId(query);
      if (vidId) {
        openPlayer({
          id: vidId,
          title: "Video YouTube",
          channel: "YouTube",
          duration: "--:--",
          url: query,
        });
        return;
      }
    }

    loadCategory(`${t("searchResults", query)}`, query);
  }

  function isYouTubeUrl(val) {
    try {
      const u = new URL(val);
      return ["youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"].includes(u.hostname.toLowerCase());
    } catch {
      return false;
    }
  }

  function extractVideoId(url) {
    try {
      if (url.includes("youtu.be/")) return url.split("youtu.be/")[1].split(/[?#]/)[0];
      const u = new URL(url);
      return u.searchParams.get("v");
    } catch {
      return "";
    }
  }

  function showEmptyState(titleText, descText) {
    if (!emptyState) return;
    emptyState.style.display = "block";
    const h3 = emptyState.querySelector("h3");
    const p = emptyState.querySelector("p");
    if (h3) h3.textContent = titleText || EMPTY_STATE_DEFAULT_TITLE;
    if (p) p.textContent = descText || EMPTY_STATE_DEFAULT_DESC;
  }

  function hideEmptyState() {
    if (emptyState) emptyState.style.display = "none";
  }

  async function loadCategory(title, query) {
    showFeedView();
    setActiveSideLink(sideHomeBtn);
    isCurrentFeedHistory = false;
    if (feedTitle) feedTitle.textContent = title;
    if (feedCount) feedCount.textContent = "";

    if (cardsGrid) cardsGrid.innerHTML = "";
    hideEmptyState();
    if (loadingSkeleton) loadingSkeleton.style.display = "grid";

    try {
      const res = await fetch(`/api/feed?q=${encodeURIComponent(query)}&count=18`);
      const data = await res.json();
      if (loadingSkeleton) loadingSkeleton.style.display = "none";

      if (!data || !data.length) {
        showEmptyState(EMPTY_STATE_DEFAULT_TITLE, EMPTY_STATE_DEFAULT_DESC);
        return;
      }

      currentFeed = data;
      if (feedCount) feedCount.textContent = t("videoCount", data.length);
      renderCards(data);
    } catch (err) {
      if (loadingSkeleton) loadingSkeleton.style.display = "none";
      showEmptyState(EMPTY_STATE_DEFAULT_TITLE, EMPTY_STATE_DEFAULT_DESC);
      showToast(t("loadError") + err.message);
    }
  }

  async function loadChannelFeed(channelName, channelUrl) {
    showFeedView();
    isCurrentFeedHistory = false;
    if (feedTitle) feedTitle.textContent = `${t("channelFeed", channelName)}`;
    if (feedCount) feedCount.textContent = t("loadingChannelVideos");

    if (cardsGrid) cardsGrid.innerHTML = "";
    hideEmptyState();
    if (loadingSkeleton) loadingSkeleton.style.display = "grid";

    try {
      const target = channelUrl || `@${channelName.replace(/\s+/g, "")}`;
      const res = await fetch(`/api/feed?q=${encodeURIComponent(target)}&channel=true&count=16`);
      const data = await res.json();
      if (loadingSkeleton) loadingSkeleton.style.display = "none";

      if (!data || !data.length) {
        showEmptyState(EMPTY_STATE_DEFAULT_TITLE, EMPTY_STATE_DEFAULT_DESC);
        if (feedCount) feedCount.textContent = "";
        return;
      }

      currentFeed = data;
      if (feedCount) feedCount.textContent = t("channelVideoCount", data.length);
      renderCards(data);
    } catch (err) {
      if (loadingSkeleton) loadingSkeleton.style.display = "none";
      showEmptyState(EMPTY_STATE_DEFAULT_TITLE, EMPTY_STATE_DEFAULT_DESC);
      showToast(t("channelLoadError"));
    }
  }

  // ==========================================
  // RENDER VIDEO CARDS
  // ==========================================
  function renderCards(videos) {
    if (!cardsGrid) return;
    cardsGrid.innerHTML = "";
    videos.forEach((video) => {
      const isBm = isChannelBookmarked(video.channel);
      const card = document.createElement("div");
      card.className = "video-card";

      const thumbUrl = video.thumbnail || `https://i.ytimg.com/vi/${video.id}/hqdefault.jpg`;

      card.innerHTML = `
        <div class="thumb-wrapper">
          <img class="thumb-img" src="${thumbUrl}" alt="${escapeHtml(video.title)}" loading="lazy" onerror="this.src='https://i.ytimg.com/vi/${video.id}/hqdefault.jpg'">
          <span class="duration-tag">${video.duration || "--:--"}</span>
        </div>
        <div class="card-details">
          <h4 class="video-title" title="${escapeHtml(video.title)}">${escapeHtml(video.title)}</h4>
          <div class="card-channel-row">
            <span class="channel-tag" title="${t("viewChannel")} ${escapeHtml(video.channel)}">${escapeHtml(video.channel)}</span>
            <div class="card-actions">
               <button class="card-dl-btn" title="${t("download")}"><svg class="ui-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L12 15.75m0 0l3-3m-3 3V3m-6.75 9.75v4.5A2.25 2.25 0 007.5 19.5h9a2.25 2.25 0 002.25-2.25v-4.5"/></svg></button>
               <button class="card-bm-btn ${isBm ? "active" : ""}" title="${isBm ? t("removeBookmark") : t("saveChannel")}"><svg class="ui-icon" viewBox="0 0 24 24" fill="${isBm ? "currentColor" : "none"}" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442a.563.563 0 01.321.99l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.386a.563.563 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0l-4.725 2.885a.563.563 0 01-.84-.61l1.285-5.386a.563.563 0 00-.182-.557L3.04 10.387a.563.563 0 01.321-.99l5.518-.442a.563.563 0 00.475-.345l2.125-5.111z"/></svg></button>
            </div>
          </div>
        </div>
      `;

      // Click card to play
      card.addEventListener("click", (e) => {
        if (e.target.closest(".card-dl-btn")) {
          e.stopPropagation();
          openDownloadModal(video);
          return;
        }
        if (e.target.closest(".card-bm-btn")) {
          e.stopPropagation();
          toggleBookmark(video.channel, video.channel_url);
          return;
        }
        if (e.target.closest(".channel-tag")) {
          e.stopPropagation();
          loadChannelFeed(video.channel, video.channel_url);
          return;
        }
        openPlayer(video);
      });

      cardsGrid.appendChild(card);
    });
  }

  // ==========================================
  // DOWNLOAD MODAL & ACTIONS
  // ==========================================
  function openDownloadModal(video) {
    pendingDownloadVideo = video;
    if (dlModalThumb) dlModalThumb.src = video.thumbnail || `https://i.ytimg.com/vi/${video.id}/hqdefault.jpg`;
    if (dlModalTitle) dlModalTitle.textContent = video.title || "Video YouTube";
    if (dlModalChannel) dlModalChannel.textContent = video.channel || "YouTube";

    // Reset to MP4 720p default
    if (dlFormatVideo) dlFormatVideo.checked = true;
    if (dlOptionVideoLabel) dlOptionVideoLabel.classList.add("active");
    if (dlOptionAudioLabel) dlOptionAudioLabel.classList.remove("active");
    if (dlResolutionRow) dlResolutionRow.style.display = "block";
    if (dlResolutionSelect) dlResolutionSelect.value = "720";

    if (downloadModal) downloadModal.style.display = "flex";
  }

  function closeDownloadModal() {
    if (downloadModal) downloadModal.style.display = "none";
    pendingDownloadVideo = null;
  }

  function handleConfirmDownload() {
    if (!pendingDownloadVideo) return;
    const formatType = (dlFormatAudio && dlFormatAudio.checked) ? "mp3" : "mp4";
    const resolution = dlResolutionSelect ? dlResolutionSelect.value : "720";
    const video = pendingDownloadVideo;
    closeDownloadModal();

    startDownload(video, formatType, resolution);
  }

  function startDownload(video, formatType = "mp4", resolution = "720") {
    const url = video.url || `https://www.youtube.com/watch?v=${video.id}`;
    const title = video.title || "Video YouTube";
    const thumbnail = video.thumbnail || "";
    fetch("/api/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: url,
        title: title,
        thumbnail: thumbnail,
        format_type: formatType,
        resolution: resolution,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          const typeLabel = formatType === "mp3" ? "MP3 Audio" : `MP4 ${resolution}p`;
          showToast(`Mengunduh [${typeLabel}]: ${title.slice(0, 26)}...`);
          loadDownloads();
        } else {
          showToast(data.error || t("downloadError"));
        }
      })
      .catch(() => {
        showToast(t("downloadError"));
      });
  }

  function downloadVideo(video) {
    openDownloadModal(video);
  }

  // ==========================================
  // DOWNLOAD MANAGER
  // ==========================================
  async function loadDownloads() {
    try {
      const res = await fetch("/api/downloads");
      const tasks = await res.json();
      allDownloads = tasks;
      renderDownloads();
      updateDownloadsBadge();

      const hasActive = tasks.some((t) => t.status === "downloading" || t.status === "queued");
      const isDlViewOpen = downloadsSection && downloadsSection.style.display !== "none";

      if (hasActive || isDlViewOpen) {
        if (!downloadsPollingTimer) {
          downloadsPollingTimer = setInterval(loadDownloads, 1000);
        }
      } else {
        if (downloadsPollingTimer) {
          clearInterval(downloadsPollingTimer);
          downloadsPollingTimer = null;
        }
      }
    } catch (err) {
      console.error("Gagal memuat unduhan:", err);
    }
  }

  function updateDownloadsBadge() {
    const activeCount = allDownloads.filter((t) => t.status === "downloading" || t.status === "queued").length;
    if (sideDownloadsBadge) {
      sideDownloadsBadge.textContent = activeCount;
      sideDownloadsBadge.style.display = activeCount > 0 ? "inline-block" : "none";
    }
    if (navDownloadsBadge) {
      navDownloadsBadge.textContent = activeCount;
      navDownloadsBadge.style.display = activeCount > 0 ? "inline-block" : "none";
    }

    const completedCount = allDownloads.filter((t) => t.status === "completed").length;
    if (countAll) countAll.textContent = allDownloads.length;
    if (countActive) countActive.textContent = activeCount;
    if (countCompleted) countCompleted.textContent = completedCount;

    if (dlSummaryText) {
      dlSummaryText.textContent = `${activeCount} unduhan aktif • ${completedCount} selesai • Berkas tersimpan di folder Downloads`;
    }
  }

  function renderDownloads() {
    if (!downloadsList) return;

    let filtered = allDownloads;
    if (currentDlFilter === "active") {
      filtered = allDownloads.filter((t) => t.status === "downloading" || t.status === "queued" || t.status === "paused");
    } else if (currentDlFilter === "completed") {
      filtered = allDownloads.filter((t) => t.status === "completed");
    }

    if (filtered.length === 0) {
      downloadsList.innerHTML = "";
      if (emptyDownloadsState) emptyDownloadsState.style.display = "block";
      return;
    }

    if (emptyDownloadsState) emptyDownloadsState.style.display = "none";

    downloadsList.innerHTML = "";
    filtered.forEach((task) => {
      const card = document.createElement("div");
      card.className = "dl-card";
      card.dataset.id = task.id;

      let badgeClass = "badge-downloading";
      let badgeText = "Mengunduh";
      let fillClass = "";

      if (task.status === "downloading") {
        badgeClass = "badge-downloading";
        badgeText = "Mengunduh";
      } else if (task.status === "queued") {
        badgeClass = "badge-downloading";
        badgeText = "Antrean";
      } else if (task.status === "paused") {
        badgeClass = "badge-paused";
        badgeText = "Dijeda";
        fillClass = "fill-paused";
      } else if (task.status === "completed") {
        badgeClass = "badge-completed";
        badgeText = "Selesai";
        fillClass = "fill-completed";
      } else if (task.status === "cancelled") {
        badgeClass = "badge-cancelled";
        badgeText = "Dibatalkan";
      } else if (task.status === "error") {
        badgeClass = "badge-error";
        badgeText = "Gagal";
      }

      const progressVal = task.status === "completed" ? 100 : (task.progress || 0);

      let actionButtons = "";
      if (task.status === "downloading" || task.status === "queued") {
        actionButtons = `
          <button class="dl-btn-ctrl dl-btn-pause" data-action="pause" data-id="${task.id}" title="Jeda unduhan">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 5.25v13.5m-7.5-13.5v13.5"/></svg>
            <span>Jeda</span>
          </button>
          <button class="dl-btn-ctrl dl-btn-cancel" data-action="cancel" data-id="${task.id}" title="Batalkan unduhan">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
            <span>Batal</span>
          </button>
        `;
      } else if (task.status === "paused") {
        actionButtons = `
          <button class="dl-btn-ctrl dl-btn-resume" data-action="resume" data-id="${task.id}" title="Lanjutkan unduhan">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-1.079 1.16-1.756 2.097-1.227l11.249 6.347c.96.542.96 1.912 0 2.454L7.347 19.574c-.937.529-2.097-.148-2.097-1.227V5.653Z"/></svg>
            <span>Lanjutkan</span>
          </button>
          <button class="dl-btn-ctrl dl-btn-cancel" data-action="cancel" data-id="${task.id}" title="Batalkan unduhan">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
            <span>Batal</span>
          </button>
        `;
      } else if (task.status === "completed") {
        actionButtons = `
          <button class="dl-btn-ctrl dl-btn-play" data-action="open-file" data-id="${task.id}" title="Buka dan putar video">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-1.079 1.16-1.756 2.097-1.227l11.249 6.347c.96.542.96 1.912 0 2.454L7.347 19.574c-.937.529-2.097-.148-2.097-1.227V5.653Z"/></svg>
            <span>Putar</span>
          </button>
          <button class="dl-btn-ctrl" data-action="open-folder" title="Buka folder berkas di Windows Explorer">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z"/></svg>
            <span>Folder</span>
          </button>
        `;
      } else if (task.status === "cancelled" || task.status === "error") {
        actionButtons = `
          <button class="dl-btn-ctrl dl-btn-resume" data-action="resume" data-id="${task.id}" title="Coba unduh ulang">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"/></svg>
            <span>Ulangi</span>
          </button>
        `;
      }

      const thumbHtml = task.thumbnail
        ? `<img src="${escapeHtml(task.thumbnail)}" class="dl-thumb-img" alt="Thumbnail" loading="lazy">`
        : `<div class="dl-thumb-fallback"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-1.079 1.16-1.756 2.097-1.227l11.249 6.347c.96.542.96 1.912 0 2.454L7.347 19.574c-.937.529-2.097-.148-2.097-1.227V5.653Z"/></svg></div>`;

      const fmtType = (task.format_type || "mp4").toLowerCase();
      let formatTagHtml = "";
      if (fmtType === "mp3") {
        formatTagHtml = `<span class="dl-format-tag format-mp3">MP3 Audio</span>`;
      } else {
        const resLabel = task.resolution ? `${task.resolution}p` : "720p";
        formatTagHtml = `<span class="dl-format-tag format-mp4">MP4 ${resLabel}</span>`;
      }

      card.innerHTML = `
        <div class="dl-thumb-wrap">
          ${thumbHtml}
        </div>
        <div class="dl-info">
          <div class="dl-title-row">
            <span class="dl-title-text" title="${escapeHtml(task.title)}">${escapeHtml(task.title)}</span>
            <div style="display:flex;align-items:center;gap:6px;flex-shrink:0;">
              ${formatTagHtml}
              <span class="dl-badge ${badgeClass}">
                <span class="badge-dot"></span>
                ${badgeText}
              </span>
            </div>
          </div>

          <div class="dl-progress-row">
            <div class="dl-progress-track">
              <div class="dl-progress-fill ${fillClass}" style="width: ${progressVal}%;"></div>
            </div>
            <span class="dl-progress-num">${progressVal.toFixed(1)}%</span>
          </div>

          <div class="dl-meta-row">
            <span class="dl-meta-item" title="Kecepatan download">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z"/></svg>
              ${task.speed || "--"}
            </span>
            <span class="dl-meta-item" title="Ukuran terunduh / total ukuran">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 5.625c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125"/></svg>
              ${task.downloaded || "0 B"} / ${task.total || "--"}
            </span>
            <span class="dl-meta-item" title="Perkiraan waktu tersisa">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              ETA: ${task.eta || "--:--"}
            </span>
          </div>
        </div>

        <div class="dl-actions">
          ${actionButtons}
        </div>
      `;

      downloadsList.appendChild(card);
    });
  }

  // ==========================================
  // PLAYER VIEW
  // ==========================================
  function openPlayer(video) {
    currentVideo = video;
    saveToHistory(video);
    // Send to native embedded MPV player
    fetch("/api/play", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(video),
    }).catch((err) => {
      showToast(t("playError") + err.message);
    });
  }

  // ==========================================
  // BOOKMARKS MANAGEMENT
  // ==========================================
  async function loadBookmarks() {
    try {
      const res = await fetch("/api/bookmarks");
      bookmarkedChannels = await res.json();
      renderBookmarksList();
    } catch {
      bookmarkedChannels = [];
    }
  }

  function isChannelBookmarked(channelName) {
    return bookmarkedChannels.some((b) => b.name.toLowerCase() === (channelName || "").toLowerCase());
  }

  function renderBookmarksList() {
    if (!channelList) return;
    channelList.innerHTML = "";
    if (!bookmarkedChannels.length) {
      channelList.innerHTML = `<div class="channel-empty">${t("noChannels")}</div>`;
      return;
    }

    bookmarkedChannels.forEach((bm) => {
      const item = document.createElement("div");
      item.className = "channel-item";
      const initial = (bm.name || "C").charAt(0).toUpperCase();

      item.innerHTML = `
        <div class="channel-left">
          <div class="channel-badge">${initial}</div>
          <span class="channel-name" title="${escapeHtml(bm.name)}">${escapeHtml(bm.name)}</span>
        </div>
        <button class="del-ch-btn" title="${t("removeBookmark")}"><svg class="ui-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg></button>
      `;

      item.addEventListener("click", (e) => {
        if (e.target.closest(".del-ch-btn")) {
          e.stopPropagation();
          deleteBookmark(bm.name);
          return;
        }
        loadChannelFeed(bm.name, bm.url);
      });

      channelList.appendChild(item);
    });
  }

  async function toggleBookmark(channelName, channelUrl) {
    if (!channelName || channelName === "YouTube") return;

    if (isChannelBookmarked(channelName)) {
      await deleteBookmark(channelName);
    } else {
      await addBookmark(channelName, channelUrl);
    }
  }

  async function addBookmark(channelName, channelUrl) {
    try {
      const url = channelUrl || `https://www.youtube.com/@${channelName.replace(/\s+/g, "")}`;
      await fetch("/api/bookmarks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: channelName, url: url }),
      });
      await loadBookmarks();
      renderCards(currentFeed);
      showToast(t("bookmarkSaved", channelName));
    } catch {
      showToast(t("bookmarkSaveError"));
    }
  }

  async function deleteBookmark(channelName) {
    try {
      await fetch(`/api/bookmarks?name=${encodeURIComponent(channelName)}`, {
        method: "DELETE",
      });
      await loadBookmarks();
      renderCards(currentFeed);
      showToast(t("bookmarkRemoved", channelName));
    } catch {
      showToast(t("bookmarkRemoveError"));
    }
  }

  async function handleSaveChannelModal() {
    if (!channelHandleInput) return;
    const val = channelHandleInput.value.trim();
    if (!val) return;

    let name = val;
    let url = val;
    if (name.startsWith("@")) {
      name = name.substring(1);
      url = `https://www.youtube.com/@${name}`;
    } else if (!url.startsWith("http")) {
      url = `https://www.youtube.com/@${name}`;
    }

    if (channelModal) channelModal.style.display = "none";
    await addBookmark(name, url);
  }

  // ==========================================
  // HISTORY MANAGEMENT
  // ==========================================
  async function saveToHistory(video) {
    try {
      await fetch("/api/history", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(video),
      });
    } catch {}
  }

  async function loadHistory() {
    showFeedView();
    isCurrentFeedHistory = true;
    if (feedTitle) feedTitle.textContent = t("historyTitle");
    if (feedCount) feedCount.textContent = "";

    if (cardsGrid) cardsGrid.innerHTML = "";
    if (loadingSkeleton) loadingSkeleton.style.display = "grid";

    try {
      const res = await fetch("/api/history");
      const data = await res.json();
      if (loadingSkeleton) loadingSkeleton.style.display = "none";

      if (!data || !data.length) {
        showEmptyState(EMPTY_STATE_HISTORY_TITLE, EMPTY_STATE_HISTORY_DESC);
        return;
      }

      currentFeed = data;
      if (feedCount) feedCount.textContent = t("historyVideoCount", data.length);
      renderCards(data);
    } catch {
      if (loadingSkeleton) loadingSkeleton.style.display = "none";
      showEmptyState(EMPTY_STATE_HISTORY_TITLE, EMPTY_STATE_HISTORY_DESC);
    }
  }

  // ==========================================
  // FULLSCREEN HELPER
  // ==========================================
  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      }
    }
  }

  // ==========================================
  // UTILITIES
  // ==========================================
  function showToast(msg) {
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => {
      toast.classList.remove("show");
    }, 2800);
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Run
  window.addEventListener("DOMContentLoaded", init);
})();
